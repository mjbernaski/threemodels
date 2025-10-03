#!/usr/bin/env node
import express from 'express';
import { createServer } from 'http';
import { Server } from 'socket.io';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs/promises';
import { validateConfig } from './src/config.js';
import { createModels, callModelsInParallel } from './src/models/index.js';
import { ConversationManager } from './src/conversation.js';
import { generateAndOpenHtml } from './src/htmlGenerator.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const server = createServer(app);
const io = new Server(server);

// Middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.static('public'));

// Store active conversations
const activeConversations = new Map();

// WebSocket connection handling
io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);
  
  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });
});

// Versioning / build metadata
let VERSION = '0.0.0';
let SUBRELEASE = process.env.SUBRELEASE || Date.now().toString();
let STARTED_AT = new Date().toISOString();
try {
  const pkgRaw = await fs.readFile(path.join(__dirname, 'package.json'), 'utf8');
  const pkg = JSON.parse(pkgRaw);
  VERSION = pkg.version || VERSION;
} catch (e) {
  // ignore
}
// Expose build identifier to downstream modules (e.g., html generator)
process.env.BUILD_ID = `${VERSION}+${SUBRELEASE}`;

// API Routes
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/api/version', (req, res) => {
  res.json({
    version: VERSION,
    subrelease: SUBRELEASE,
    build: `${VERSION}+${SUBRELEASE}`,
    startedAt: STARTED_AT
  });
});

app.post('/api/ask', async (req, res) => {
  try {
    const { question, conversationId } = req.body;
    
    if (!question || !question.trim()) {
      return res.status(400).json({ error: 'Question is required' });
    }

    // Get or create conversation
    let conversation;
    if (conversationId && activeConversations.has(conversationId)) {
      conversation = activeConversations.get(conversationId);
    } else {
      const newId = Date.now().toString();
      conversation = new ConversationManager(path.join('data', 'conversations', `conversation_${newId}.json`));
      activeConversations.set(newId, conversation);
    }

    // Get socket for real-time updates
    const socket = req.socket;
    
    // Send initial status
    io.emit('status', { 
      type: 'starting', 
      message: 'Sending question to all models...',
      conversationId: conversationId || Object.keys(activeConversations)[Object.keys(activeConversations).length - 1]
    });

    // Prepare messages
    const messages = conversation.getMessages();
    messages.push({ role: 'user', content: question });

    // Call models with progress updates
    const responses = await callModelsInParallel(models, messages, 3, (modelName, content, duration) => {
      io.emit('modelResponse', {
        model: modelName,
        content: content,
        duration: duration,
        conversationId: conversationId || Object.keys(activeConversations)[Object.keys(activeConversations).length - 1]
      });
    });

    // Add round to conversation
    conversation.addRound(question, responses);
    await conversation.save();

    // Generate HTML comparison
    const htmlFilename = `conversation_${Date.now()}.html`;
    await generateAndOpenHtml(conversation.filename, path.join('public', 'comparisons', htmlFilename));

    // Send completion status
    io.emit('complete', {
      conversationId: conversationId || Object.keys(activeConversations)[Object.keys(activeConversations).length - 1],
      htmlFile: htmlFilename,
      responses: responses
    });

    res.json({
      success: true,
      responses: responses,
      conversationId: conversationId || Object.keys(activeConversations)[Object.keys(activeConversations).length - 1],
      htmlFile: htmlFilename
    });

  } catch (error) {
    console.error('Error processing question:', error);
    io.emit('error', { message: error.message });
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/conversations', async (req, res) => {
  try {
    const files = await fs.readdir(path.join('public', 'comparisons'));
    const conversations = [];
    
    for (const file of files) {
      if (file.endsWith('.html')) {
        const timestamp = file.replace('conversation_', '').replace('.html', '');
        let prompt = 'Conversation';
        
        try {
          // Read the HTML file and extract the first prompt
          const htmlContent = await fs.readFile(path.join('public', 'comparisons', file), 'utf8');
          
          // Look for the user prompt in the HTML
          const promptMatch = htmlContent.match(/<h3>User Prompt:<\/h3>\s*<div><p>(.*?)<\/p><\/div>/s);
          if (promptMatch && promptMatch[1]) {
            // Decode HTML entities and clean up the prompt
            prompt = promptMatch[1]
              .replace(/&quot;/g, '"')
              .replace(/&amp;/g, '&')
              .replace(/&lt;/g, '<')
              .replace(/&gt;/g, '>')
              .replace(/&#39;/g, "'");
            
            // Truncate long prompts for display
            if (prompt.length > 100) {
              prompt = prompt.substring(0, 100) + '...';
            }
          }
        } catch (htmlError) {
          // If HTML file can't be read, use default
          console.log(`Could not read ${file}:`, htmlError.message);
        }
        
        conversations.push({
          filename: file,
          url: `/comparisons/${file}`,
          timestamp: timestamp,
          prompt: prompt
        });
      }
    }
    
    // Sort by timestamp (newest first)
    conversations.sort((a, b) => b.timestamp - a.timestamp);
    
    res.json(conversations);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Initialize models
let models;
try {
  validateConfig();
  models = createModels();
  console.log('✅ Models initialized successfully');
} catch (error) {
  console.error('❌ Configuration error:', error.message);
  process.exit(1);
}

// Create comparisons directory
try {
  await fs.mkdir(path.join('public', 'comparisons'), { recursive: true });
} catch (error) {
  // Directory might already exist
}

const PORT = process.env.PORT || 3000;
const HOST = process.env.HOST || '0.0.0.0';
server.listen(PORT, HOST, () => {
  console.log(`🌐 Web server running at http://${HOST === '0.0.0.0' ? 'localhost' : HOST}:${PORT}`);
  console.log(`🔖 Version: ${VERSION}  Subrelease: ${SUBRELEASE}`);
  console.log('📱 Open your browser and start asking questions!');
});