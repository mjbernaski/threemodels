#!/usr/bin/env node
import readline from 'readline';
import { validateConfig } from './src/config.js';
import { createModels, callModelsInParallel } from './src/models/index.js';
import { ConversationManager } from './src/conversation.js';
import { generateAndOpenHtml } from './src/htmlGenerator.js';

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: true
});

async function askQuestion(prompt) {
  return new Promise((resolve) => {
    rl.question(prompt, resolve);
  });
}

async function main() {
  console.clear();
  console.log('Multi-Model AI Conversation System');
  console.log('==================================\n');
  
  try {
    validateConfig();
  } catch (error) {
    console.error('Configuration error:', error.message);
    rl.close();
    process.exit(1);
  }

  const models = createModels();
  const conversation = new ConversationManager();
  
  try {
    await conversation.load();
  } catch (error) {
    console.log('Starting new conversation\n');
  }

  console.log('Commands:');
  console.log('  - Type your prompt and press Enter to send to all models');
  console.log('  - Type "assess" to have models analyze the previous responses');
  console.log('  - Type "exit" to quit and save the conversation\n');

  let running = true;
  
  while (running) {
    try {
      const input = await askQuestion('\n> ');
      
      if (!input || input.trim() === '') {
        continue;
      }
      
      if (input.toLowerCase() === 'exit') {
        await conversation.save();
        console.log('\nConversation saved. Generating HTML...');
        await generateAndOpenHtml();
        console.log('Goodbye!');
        running = false;
        break;
      }
      
      if (input.toLowerCase() === 'assess') {
        const lastResponses = conversation.getLastResponses();
        if (!lastResponses) {
          console.log('No previous responses to assess.');
          continue;
        }
        
        const lastRound = conversation.conversation.rounds[conversation.conversation.rounds.length - 1];
        const assessmentPrompt = conversation.formatAssessmentPrompt(
          lastRound.userPrompt,
          lastResponses
        );
        
        console.log('\nSending assessment request to all models...\n');
        
        const assessmentMessages = [{
          role: 'user',
          content: assessmentPrompt
        }];
        
        const responses = await callModelsInParallel(models, assessmentMessages);
        
        for (const [model, response] of Object.entries(responses)) {
          console.log(`\n=== ${model} Assessment ===`);
          if (response.error) {
            console.log(`Error: ${response.error}`);
          } else {
            console.log(response.content);
          }
        }
        
        conversation.addRound(assessmentPrompt, responses, true);
        await conversation.save();
        await generateAndOpenHtml();
        continue;
      }
      
      console.log('\nSending to all models...\n');
      
      const messages = conversation.getMessages();
      messages.push({ role: 'user', content: input });
      
      const responses = await callModelsInParallel(models, messages);
      
      for (const [model, response] of Object.entries(responses)) {
        console.log(`\n=== ${model} Response ===`);
        if (response.error) {
          console.log(`Error: ${response.error}`);
        } else {
          console.log(response.content);
          if (response.usage?.total_tokens) {
            console.log(`\nTokens: ${response.usage.total_tokens}`);
          }
        }
      }
      
      conversation.addRound(input, responses);
      await conversation.save();
      await generateAndOpenHtml();
      
    } catch (error) {
      console.error('\nError:', error.message);
    }
  }
  
  rl.close();
}

// Handle graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n\nReceived interrupt signal. Saving conversation...');
  try {
    const conversation = new ConversationManager();
    await conversation.save();
  } catch (error) {
    // Ignore save errors on interrupt
  }
  process.exit(0);
});

main().catch((error) => {
  console.error('Fatal error:', error);
  rl.close();
  process.exit(1);
});