import fs from 'fs/promises';
import path from 'path';

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function markdownToHtml(text) {
  // Escape HTML entities first
  text = escapeHtml(text);

  // Convert code blocks
  text = text.replace(/```([^\n]*)\n(.*?)```/gs, (match, lang, code) =>
    `<pre><code class="language-${lang}">${code.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'")}</code></pre>`
  );
  text = text.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Convert headers
  text = text.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  text = text.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  text = text.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // Convert bold and italic
  text = text.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');
  text = text.replace(/__(.+?)__/g, '<strong>$1</strong>');
  text = text.replace(/_(.+?)_/g, '<em>$1</em>');

  // Convert lists
  const lines = text.split('\n');
  let inList = false;
  const newLines = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Unordered lists
    if (/^[*+-] /.test(line)) {
      if (!inList) {
        newLines.push('<ul>');
        inList = 'ul';
      }
      newLines.push('<li>' + line.slice(2) + '</li>');
    }
    // Ordered lists
    else if (/^\d+\. /.test(line)) {
      if (inList !== 'ol') {
        if (inList) {
          newLines.push('</' + inList + '>');
        }
        newLines.push('<ol>');
        inList = 'ol';
      }
      newLines.push('<li>' + line.replace(/^\d+\. /, '') + '</li>');
    }
    else {
      if (inList) {
        newLines.push('</' + inList + '>');
        inList = false;
      }
      newLines.push(line);
    }
  }

  if (inList) {
    newLines.push('</' + inList + '>');
  }

  text = newLines.join('\n');

  // Convert line breaks - reduce excessive newlines
  text = text.replace(/\n\n+/g, '</p><p>'); // Multiple newlines become paragraph breaks
  text = text.replace(/\n/g, ' '); // Single newlines become spaces
  text = '<p>' + text + '</p>';
  text = text.replace(/<p><\/p>/g, '');
  text = text.replace(/<p>\s*<\/p>/g, ''); // Remove empty paragraphs with whitespace

  // Clean up code blocks that got wrapped in paragraphs
  text = text.replace(/<p>(<pre>.*?<\/pre>)<\/p>/gs, '$1');
  text = text.replace(/<p>(<h[1-6]>.*?<\/h[1-6]>)<\/p>/gs, '$1');
  text = text.replace(/<p>(<ul>.*?<\/ul>)<\/p>/gs, '$1');
  text = text.replace(/<p>(<ol>.*?<\/ol>)<\/p>/gs, '$1');

  // Remove extra spaces around HTML tags
  text = text.replace(/\s*(<[^>]+>)\s*/g, '$1');
  text = text.replace(/<\/p>\s*<p>/g, '</p><p>');

  return text;
}

async function generatePreviousConversationsList(currentHtmlFile) {
  const comparisonsDir = path.join('public', 'comparisons');

  try {
    const files = await fs.readdir(comparisonsDir);
    const htmlFiles = files.filter(f => f.endsWith('.html') && f !== path.basename(currentHtmlFile));

    if (htmlFiles.length === 0) {
      return '';
    }

    // Sort by modification time, newest first
    const filesWithStats = await Promise.all(
      htmlFiles.map(async (file) => {
        const filePath = path.join(comparisonsDir, file);
        const stats = await fs.stat(filePath);
        return { file, mtime: stats.mtime };
      })
    );

    filesWithStats.sort((a, b) => b.mtime - a.mtime);

    // Take only the 10 most recent
    const recentFiles = filesWithStats.slice(0, 10);

    const itemsHtml = await Promise.all(
      recentFiles.map(async ({ file }) => {
        try {
          const filePath = path.join(comparisonsDir, file);
          const content = await fs.readFile(filePath, 'utf8');

          // Extract first user prompt
          const promptMatch = content.match(/<div class="user-prompt">.*?<div>(.*?)<\/div>/s);
          let promptText = 'No prompt found';

          if (promptMatch && promptMatch[1]) {
            promptText = promptMatch[1]
              .replace(/<[^>]+>/g, '')  // Remove HTML tags
              .replace(/&quot;/g, '"')
              .replace(/&amp;/g, '&')
              .replace(/&lt;/g, '<')
              .replace(/&gt;/g, '>')
              .replace(/&#39;/g, "'")
              .trim();

            if (promptText.length > 150) {
              promptText = promptText.substring(0, 150) + '...';
            }
          }

          // Extract timestamp from filename or use file stats
          const timestamp = file.replace('conversation_', '').replace('.html', '');
          let dateStr;
          try {
            const date = new Date(parseInt(timestamp));
            dateStr = date.toLocaleString('en-US', {
              month: 'long',
              day: 'numeric',
              year: 'numeric',
              hour: 'numeric',
              minute: '2-digit',
              hour12: true
            });
          } catch {
            dateStr = timestamp;
          }

          return `
                <div class="conversation-item">
                    <a href="${file}">
                        <div class="conversation-date">${dateStr}</div>
                        <div class="conversation-snippet">${escapeHtml(promptText)}</div>
                    </a>
                </div>`;
        } catch {
          return '';
        }
      })
    );

    const validItems = itemsHtml.filter(item => item.trim() !== '');

    if (validItems.length === 0) {
      return '';
    }

    return `
        <div class="previous-conversations">
            <h2>📚 Previous Conversations</h2>
            <div class="conversation-list">
                ${validItems.join('')}
            </div>
        </div>`;
  } catch {
    return '';
  }
}

export async function generateAndOpenHtml(jsonFilePath = path.join('data', 'conversations', 'conversation.json'), outputPath = path.join('public', 'comparisons', 'conversation_side_by_side.html')) {
  try {
    // Ensure the output directory exists
    try {
      await fs.mkdir(path.dirname(outputPath), { recursive: true });
    } catch (e) {
      // ignore mkdir errors
    }
    const data = JSON.parse(await fs.readFile(jsonFilePath, 'utf8'));

    const metadata = data.metadata || {};
    const startTime = metadata.startTime || 'N/A';
    const totalRounds = metadata.totalRounds || 0;
    const lastUpdated = metadata.lastUpdated || 'N/A';

    const buildId = process.env.BUILD_ID || '';
    let htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Model Comparison - Side by Side</title>
    <style>
        html, body {
            height: 100%;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: #e0e0e0;
            padding: 20px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
        }

        .container {
            max-width: 1600px;
            margin: 0 auto;
            flex: 1;
            display: flex;
            flex-direction: column;
            min-height: 0;
        }

        h1 {
            text-align: center;
            color: #e0e0e0;
            margin-bottom: 30px;
            flex-shrink: 0;
        }

        .metadata {
            background: rgba(30, 30, 50, 0.95);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #e0e0e0;
            flex-shrink: 0;
        }

        .round {
            margin-bottom: 40px;
            background: rgba(30, 30, 50, 0.95);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            flex: 1;
            display: flex;
            flex-direction: column;
            min-height: 0;
        }

        .round-header {
            border-bottom: 2px solid #444;
            padding-bottom: 15px;
            margin-bottom: 20px;
            flex-shrink: 0;
        }

        .timestamp {
            color: #999;
            font-size: 0.9em;
        }

        .user-prompt {
            background: rgba(102, 126, 234, 0.2);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
            color: #e0e0e0;
            flex-shrink: 0;
        }

        .user-prompt h3 {
            margin-top: 0;
            color: #e0e0e0;
        }

        .responses-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            align-items: stretch;
            flex: 1;
            min-height: 0;
        }

        .model-response {
            background: #2a2a3e;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 15px;
            display: flex;
            flex-direction: column;
            min-height: 0;
            color: #e0e0e0;
        }

        .model-header {
            font-weight: bold;
            font-size: 1.1em;
            padding: 10px;
            margin: -15px -15px 15px -15px;
            border-radius: 7px 7px 0 0;
            text-align: center;
            color: white;
            flex-shrink: 0;
        }

        .anthropic-header {
            background: #7C3AED;
        }

        .openai-header {
            background: #10B981;
        }

        .gemini-header {
            background: #F59E0B;
        }

        .model-content {
            padding-right: 10px;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 0.9em;
            line-height: 1.6;
            flex: 1;
            overflow-y: auto;
            min-height: 0;
        }

        .model-content code {
            background: #444;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9em;
            color: #e0e0e0;
        }

        .model-content pre {
            background: #444;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 10px 0;
            color: #e0e0e0;
        }

        .model-content pre code {
            background: none;
            padding: 0;
        }

        .model-content h1, .model-content h2, .model-content h3 {
            margin-top: 20px;
            margin-bottom: 10px;
        }

        .model-content ul, .model-content ol {
            margin: 10px 0;
            padding-left: 30px;
        }

        .model-content li {
            margin: 5px 0;
        }

        .model-content p {
            margin: 10px 0;
        }

        .model-content::-webkit-scrollbar {
            width: 8px;
        }

        .model-content::-webkit-scrollbar-track {
            background: #444;
            border-radius: 4px;
        }

        .model-content::-webkit-scrollbar-thumb {
            background: #666;
            border-radius: 4px;
        }

        .model-content::-webkit-scrollbar-thumb:hover {
            background: #888;
        }

        .usage-info {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #444;
            font-size: 0.85em;
            color: #999;
            flex-shrink: 0;
        }

        @media (max-width: 1200px) {
            .responses-grid {
                grid-template-columns: 1fr;
            }
        }

        .previous-conversations {
            margin-top: 40px;
            padding-top: 30px;
            border-top: 2px solid #444;
        }

        .previous-conversations h2 {
            text-align: center;
            color: #e0e0e0;
            margin-bottom: 25px;
        }

        .conversation-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }

        .conversation-item {
            background: #2a2a3e;
            border-radius: 8px;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .conversation-item:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.3);
        }

        .conversation-item a {
            display: block;
            padding: 15px;
            text-decoration: none;
            color: #e0e0e0;
        }

        .conversation-date {
            font-size: 0.85em;
            color: #999;
            margin-bottom: 8px;
        }

        .conversation-snippet {
            font-size: 0.95em;
            line-height: 1.4;
            color: #e0e0e0;
            word-wrap: break-word;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Three Models Comparison</h1>

        <div class="metadata">
            <strong>Start Time:</strong> ${startTime}<br>
            <strong>Total Rounds:</strong> ${totalRounds}<br>
            <strong>Last Updated:</strong> ${lastUpdated}<br>
            ${buildId ? `<strong>Build:</strong> ${buildId}` : ''}
        </div>
`;

    for (const roundData of data.rounds) {
      const roundId = roundData.id;
      const timestamp = roundData.timestamp;
      const userPrompt = markdownToHtml(roundData.userPrompt);

      htmlContent += `
        <div class="round">
            <div class="round-header">
                <h2>Round ${roundId}</h2>
                <div class="timestamp">${timestamp}</div>
            </div>

            <div class="user-prompt">
                <h3>User Prompt:</h3>
                <div>${userPrompt}</div>
            </div>

            <div class="responses-grid">
`;

      // Model mapping to show both vendor and specific model names
      const modelNames = {
        'Anthropic': 'Anthropic<br><span style="font-size: 0.8em; opacity: 0.9;">claude-sonnet-4-20250514</span>',
        'OpenAI': 'OpenAI<br><span style="font-size: 0.8em; opacity: 0.9;">gpt-5</span>',
        'Gemini': 'Gemini<br><span style="font-size: 0.8em; opacity: 0.9;">gemini-2.5-pro</span>'
      };

      const models = ['Anthropic', 'OpenAI', 'Gemini'];
      for (const model of models) {
        if (roundData.responses[model]) {
          const response = roundData.responses[model];
          let content;
          if (response.error) {
            content = `<p style="color: #e74c3c;"><strong>Error:</strong> ${escapeHtml(response.error)}</p>`;
          } else {
            content = markdownToHtml(response.content || '');
          }
          const usage = response.usage || {};
          const responseTime = typeof response.response_time === 'number' ? response.response_time : null;

          const headerClass = `${model.toLowerCase()}-header`;
          const displayName = modelNames[model] || model;

          htmlContent += `
                <div class="model-response">
                    <div class="model-header ${headerClass}">${displayName}</div>
                    <div class="model-content">${content}</div>
`;

          // Always render usage/time for consistency across models
          let tokensLine;
          const inputTokens = (usage.input_tokens ?? usage.prompt_tokens);
          const outputTokens = (usage.output_tokens ?? usage.completion_tokens);
          const totalTokens = (usage.total_tokens != null)
            ? usage.total_tokens
            : (inputTokens != null && outputTokens != null)
              ? (inputTokens + outputTokens)
              : undefined;
          const safe = (v) => (v != null ? v : 'N/A');
          tokensLine = `${safe(inputTokens)} in / ${safe(outputTokens)} out / ${safe(totalTokens)} total`;

          const timeLine = (responseTime !== null)
            ? `${responseTime.toFixed(2)}s`
            : 'N/A';

          htmlContent += `
                    <div class="usage-info">
                        <strong>Tokens:</strong> ${tokensLine}<br>
                        <strong>Response time:</strong> ${timeLine}
                    </div>
`;

          htmlContent += `
                </div>
`;
        }
      }

      htmlContent += `
            </div>
        </div>
`;
    }

    htmlContent += `
        ${await generatePreviousConversationsList(outputPath)}
    </div>
</body>
</html>
`;

    await fs.writeFile(outputPath, htmlContent);
    console.log(`\n📄 Side-by-side comparison saved to: ${outputPath}`);

    // Open the HTML file in the default browser
    const { exec } = await import('child_process');
    exec(`open "${outputPath}"`, (error) => {
      if (error) {
        console.log(`⚠️  Could not open browser automatically. Open ${outputPath} manually.`);
      } else {
        console.log('🌐 Opening comparison in browser...');
      }
    });

  } catch (error) {
    console.error('Error generating HTML:', error.message);
  }
}