import fs from 'fs/promises';

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

export async function generateAndOpenHtml(jsonFilePath = 'conversation.json', outputPath = 'conversation_side_by_side.html') {
  try {
    const data = JSON.parse(await fs.readFile(jsonFilePath, 'utf8'));

    const metadata = data.metadata || {};
    const startTime = metadata.startTime || 'N/A';
    const totalRounds = metadata.totalRounds || 0;
    const lastUpdated = metadata.lastUpdated || 'N/A';

    let htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Model Comparison - Side by Side</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }

        .container {
            max-width: 1600px;
            margin: 0 auto;
        }

        h1 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 30px;
        }

        .metadata {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .round {
            margin-bottom: 40px;
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .round-header {
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }

        .timestamp {
            color: #666;
            font-size: 0.9em;
        }

        .user-prompt {
            background: #e8f4f8;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
        }

        .user-prompt h3 {
            margin-top: 0;
            color: #2c3e50;
        }

        .responses-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            align-items: start;
        }

        .model-response {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            height: 100%;
            overflow: hidden;
        }

        .model-header {
            font-weight: bold;
            font-size: 1.1em;
            padding: 10px;
            margin: -15px -15px 15px -15px;
            border-radius: 7px 7px 0 0;
            text-align: center;
            color: white;
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
            max-height: 600px;
            overflow-y: auto;
            padding-right: 10px;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 0.9em;
            line-height: 1.6;
        }

        .model-content code {
            background: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9em;
        }

        .model-content pre {
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 10px 0;
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
            background: #f1f1f1;
            border-radius: 4px;
        }

        .model-content::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 4px;
        }

        .model-content::-webkit-scrollbar-thumb:hover {
            background: #555;
        }

        .usage-info {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e0e0e0;
            font-size: 0.85em;
            color: #666;
        }

        @media (max-width: 1200px) {
            .responses-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Three Models Comparison</h1>

        <div class="metadata">
            <strong>Start Time:</strong> ${startTime}<br>
            <strong>Total Rounds:</strong> ${totalRounds}<br>
            <strong>Last Updated:</strong> ${lastUpdated}
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

          const headerClass = `${model.toLowerCase()}-header`;
          const displayName = modelNames[model] || model;

          htmlContent += `
                <div class="model-response">
                    <div class="model-header ${headerClass}">${displayName}</div>
                    <div class="model-content">${content}</div>
`;

          if (Object.keys(usage).length > 0) {
            if (model === 'Anthropic') {
              htmlContent += `
                    <div class="usage-info">
                        <strong>Tokens:</strong> ${usage.input_tokens || 0} in / ${usage.output_tokens || 0} out / ${usage.total_tokens || 0} total
                    </div>
`;
            } else if (model === 'OpenAI') {
              htmlContent += `
                    <div class="usage-info">
                        <strong>Tokens:</strong> ${usage.prompt_tokens || 0} in / ${usage.completion_tokens || 0} out / ${usage.total_tokens || 0} total
                    </div>
`;
            } else if (model === 'Gemini') {
              htmlContent += `
                    <div class="usage-info">
                        <strong>Tokens:</strong> ${usage.prompt_tokens || 0} in / ${usage.completion_tokens || 0} out / ${usage.total_tokens || 0} total
                    </div>
`;
            }
          }

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