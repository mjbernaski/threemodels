#!/usr/bin/env python3

import json
import webbrowser
import os
import re
from datetime import datetime

def markdown_to_html(text):
    """Convert markdown to HTML"""
    # Escape HTML entities first
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Convert code blocks
    text = re.sub(r'```([^\n]*)\n(.*?)```', lambda m: '<pre><code class="language-' + m.group(1) + '">' + m.group(2).replace('&lt;', '<').replace('&gt;', '>') + '</code></pre>', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    # Convert headers
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # Convert bold and italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    
    # Convert lists
    lines = text.split('\n')
    in_list = False
    new_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Unordered lists
        if re.match(r'^[*+-] ', line):
            if not in_list:
                new_lines.append('<ul>')
                in_list = 'ul'
            new_lines.append('<li>' + line[2:] + '</li>')
        # Ordered lists
        elif re.match(r'^\d+\. ', line):
            if in_list != 'ol':
                if in_list:
                    new_lines.append('</' + in_list + '>')
                new_lines.append('<ol>')
                in_list = 'ol'
            new_lines.append('<li>' + re.sub(r'^\d+\. ', '', line) + '</li>')
        else:
            if in_list:
                new_lines.append('</' + in_list + '>')
                in_list = False
            new_lines.append(line)
        
        i += 1
    
    if in_list:
        new_lines.append('</' + in_list + '>')
    
    text = '\n'.join(new_lines)
    
    # Convert line breaks
    text = re.sub(r'\n\n', '</p><p>', text)
    text = '<p>' + text + '</p>'
    text = re.sub(r'<p></p>', '', text)
    
    # Clean up code blocks that got wrapped in paragraphs
    text = re.sub(r'<p>(<pre>.*?</pre>)</p>', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'<p>(<h[1-6]>.*?</h[1-6]>)</p>', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'<p>(<ul>.*?</ul>)</p>', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'<p>(<ol>.*?</ol>)</p>', r'\1', text, flags=re.DOTALL)
    
    return text

def load_conversation(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_timestamp(timestamp):
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%B %d, %Y at %I:%M %p')
    except:
        return timestamp

def generate_html(conversation_data):
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Conversation History</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
            line-height: 1.6;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding: 20px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .round {
            background: white;
            margin-bottom: 30px;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .round-header {
            background: #e3f2fd;
            padding: 20px;
            border-bottom: 1px solid #ddd;
        }
        .round-number {
            font-weight: bold;
            color: #1976d2;
            font-size: 1.1em;
        }
        .timestamp {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }
        .user-prompt {
            background: #f5f5f5;
            padding: 20px;
            border-left: 4px solid #2196f3;
            margin: 0;
            font-weight: 500;
        }
        .responses {
            padding: 0;
        }
        .response {
            border-bottom: 1px solid #eee;
            padding: 20px;
        }
        .response:last-child {
            border-bottom: none;
        }
        .model-name {
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
            padding: 8px 12px;
            background: #f0f0f0;
            border-radius: 6px;
            display: inline-block;
        }
        .anthropic { background: #e8f5e8; }
        .openai { background: #fff4e6; }
        .gemini { background: #e3f2fd; }
        .content {
            margin: 15px 0;
            color: #333;
        }
        .content code {
            background: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9em;
        }
        .content pre {
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 10px 0;
        }
        .content pre code {
            background: none;
            padding: 0;
        }
        .content h1, .content h2, .content h3 {
            margin-top: 15px;
            margin-bottom: 10px;
            color: #333;
        }
        .content ul, .content ol {
            margin: 10px 0;
            padding-left: 30px;
        }
        .content li {
            margin: 5px 0;
        }
        .content p {
            margin: 10px 0;
        }
        .error {
            color: #d32f2f;
            background: #ffebee;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #d32f2f;
        }
        .usage {
            font-size: 0.85em;
            color: #666;
            margin-top: 10px;
            padding: 8px;
            background: #f9f9f9;
            border-radius: 4px;
        }
        .metadata {
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin-top: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .metadata h3 {
            margin-top: 0;
            color: #1976d2;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>AI Model Conversation History</h1>
        <p>Comparing responses from multiple AI models</p>
    </div>
"""

    for round_data in conversation_data['rounds']:
        html += f"""
    <div class="round">
        <div class="round-header">
            <div class="round-number">Round {round_data['id']}</div>
            <div class="timestamp">{format_timestamp(round_data['timestamp'])}</div>
        </div>
        <div class="user-prompt">
            <strong>Question:</strong> <span>{markdown_to_html(round_data['userPrompt'])}</span>
        </div>
        <div class="responses">
"""

        for model, response_data in round_data['responses'].items():
            model_class = model.lower()
            html += f"""
            <div class="response {model_class}">
                <div class="model-name">{response_data['model']}</div>
"""
            
            if 'error' in response_data:
                html += f'<div class="error"><strong>Error:</strong> {response_data["error"]}</div>'
            else:
                html += f'<div class="content">{markdown_to_html(response_data["content"])}</div>'
            
            if response_data.get('usage'):
                usage = response_data['usage']
                usage_text = []
                if 'input_tokens' in usage:
                    usage_text.append(f"Input: {usage['input_tokens']}")
                if 'output_tokens' in usage:
                    usage_text.append(f"Output: {usage['output_tokens']}")
                if 'total_tokens' in usage:
                    usage_text.append(f"Total: {usage['total_tokens']}")
                if 'prompt_tokens' in usage:
                    usage_text.append(f"Prompt: {usage['prompt_tokens']}")
                if 'completion_tokens' in usage:
                    usage_text.append(f"Completion: {usage['completion_tokens']}")
                
                if usage_text:
                    html += f'<div class="usage">Token usage: {" | ".join(usage_text)}</div>'
            
            html += """
            </div>
"""

        html += """
        </div>
    </div>
"""

    metadata = conversation_data.get('metadata', {})
    html += f"""
    <div class="metadata">
        <h3>Conversation Metadata</h3>
        <p><strong>Start Time:</strong> {format_timestamp(metadata.get('startTime', 'Unknown'))}</p>
        <p><strong>Total Rounds:</strong> {metadata.get('total_rounds', 'Unknown')}</p>
        <p><strong>Last Updated:</strong> {format_timestamp(metadata.get('lastUpdated', metadata.get('last_updated', 'Unknown')))}</p>
    </div>
</body>
</html>
"""
    return html

def main():
    import sys
    conversation_file = sys.argv[1] if len(sys.argv) > 1 else 'conversation.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'conversation.html'
    
    if not os.path.exists(conversation_file):
        print(f"Error: {conversation_file} not found in current directory")
        return
    
    try:
        conversation_data = load_conversation(conversation_file)
        html_content = generate_html(conversation_data)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML file generated: {output_file}")
        
        abs_path = os.path.abspath(output_file)
        webbrowser.open(f'file://{abs_path}')
        print(f"Opening {output_file} in your default browser...")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()