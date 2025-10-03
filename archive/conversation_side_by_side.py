#!/usr/bin/env python3

import json
import html
import re
from datetime import datetime

def markdown_to_html(text):
    """Convert markdown to HTML"""
    # Escape HTML entities first
    text = html.escape(text)
    
    # Convert code blocks
    text = re.sub(r'```([^\n]*)\n(.*?)```', lambda m: '<pre><code class="language-' + m.group(1) + '">' + html.unescape(m.group(2)) + '</code></pre>', text, flags=re.DOTALL)
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
    
    # Convert line breaks - reduce excessive newlines
    text = re.sub(r'\n\n+', '</p><p>', text)  # Multiple newlines become paragraph breaks
    text = re.sub(r'\n', ' ', text)  # Single newlines become spaces
    text = '<p>' + text + '</p>'
    text = re.sub(r'<p></p>', '', text)
    text = re.sub(r'<p>\s*</p>', '', text)  # Remove empty paragraphs with whitespace
    
    # Clean up code blocks that got wrapped in paragraphs
    text = re.sub(r'<p>(<pre>.*?</pre>)</p>', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'<p>(<h[1-6]>.*?</h[1-6]>)</p>', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'<p>(<ul>.*?</ul>)</p>', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'<p>(<ol>.*?</ol>)</p>', r'\1', text, flags=re.DOTALL)
    
    # Remove extra spaces around HTML tags
    text = re.sub(r'\s*(<[^>]+>)\s*', r'\1', text)
    text = re.sub(r'</p>\s*<p>', '</p><p>', text)
    
    return text

def create_side_by_side_html(json_file_path, output_file_path):
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    metadata = data.get('metadata', {})
    start_time = metadata.get('start_time', 'N/A')
    total_rounds = metadata.get('total_rounds', 0)
    last_updated = metadata.get('last_updated', 'N/A')
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Model Comparison - Side by Side</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #2c3e50;
            color: #333;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
            width: 100%;
        }}

        h1 {{
            text-align: center;
            color: #2c3e50;
            margin-bottom: 20px;
        }}

        .metadata {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .round {{
            margin-bottom: 20px;
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
        }}

        .round-header {{
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 15px;
            margin-bottom: 15px;
        }}

        .timestamp {{
            color: #666;
            font-size: 0.9em;
        }}

        .user-prompt {{
            background: #e8f4f8;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #3498db;
        }}

        .user-prompt h3 {{
            margin-top: 0;
            color: #2c3e50;
        }}

        .responses-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            align-items: start;
        }}

        .model-response {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            display: flex;
            flex-direction: column;
        }}
        
        .model-header {{
            font-weight: bold;
            font-size: 1.1em;
            padding: 10px;
            margin: -15px -15px 15px -15px;
            border-radius: 7px 7px 0 0;
            text-align: center;
            color: white;
        }}

        .anthropic-header {{
            background: #7C3AED;
        }}

        .openai-header {{
            background: #10B981;
        }}

        .gemini-header {{
            background: #F59E0B;
        }}

        .model-content {{
            padding-right: 10px;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 0.9em;
            line-height: 1.6;
        }}
        
        .model-content code {{
            background: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9em;
        }}
        
        .model-content pre {{
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 10px 0;
        }}
        
        .model-content pre code {{
            background: none;
            padding: 0;
        }}
        
        .model-content h1, .model-content h2, .model-content h3 {{
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        
        .model-content ul, .model-content ol {{
            margin: 10px 0;
            padding-left: 30px;
        }}
        
        .model-content li {{
            margin: 5px 0;
        }}
        
        .model-content p {{
            margin: 10px 0;
        }}

        .usage-info {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e0e0e0;
            font-size: 0.85em;
            color: #666;
        }}
        
        @media (max-width: 1200px) {{
            .responses-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Three Models Comparison</h1>
        
        <div class="metadata">
            <strong>Start Time:</strong> {start_time}<br>
            <strong>Total Rounds:</strong> {total_rounds}<br>
            <strong>Last Updated:</strong> {last_updated}
        </div>
"""
    
    for round_data in data['rounds']:
        round_id = round_data['id']
        timestamp = round_data['timestamp']
        user_prompt = markdown_to_html(round_data['userPrompt'])
        
        html_content += f"""
        <div class="round">
            <div class="round-header">
                <h2>Round {round_id}</h2>
                <div class="timestamp">{timestamp}</div>
            </div>
            
            <div class="user-prompt">
                <h3>User Prompt:</h3>
                <div>{user_prompt}</div>
            </div>
            
            <div class="responses-grid">
"""
        
        # Model mapping to show both vendor and specific model names
        model_names = {
            'Anthropic': 'Anthropic<br><span style="font-size: 0.8em; opacity: 0.9;">claude-sonnet-4-20250514</span>',
            'OpenAI': 'OpenAI<br><span style="font-size: 0.8em; opacity: 0.9;">gpt-5</span>', 
            'Gemini': 'Gemini<br><span style="font-size: 0.8em; opacity: 0.9;">gemini-2.5-pro</span>'
        }
        
        models = ['Anthropic', 'OpenAI', 'Gemini']
        for model in models:
            if model in round_data['responses']:
                response = round_data['responses'][model]
                if 'error' in response:
                    content = f"<p style='color: #e74c3c;'><strong>Error:</strong> {response['error']}</p>"
                else:
                    content = markdown_to_html(response.get('content', ''))
                usage = response.get('usage', {})
                
                header_class = f"{model.lower()}-header"
                display_name = model_names.get(model, model)
                
                html_content += f"""
                <div class="model-response">
                    <div class="model-header {header_class}">{display_name}</div>
                    <div class="model-content">{content}</div>
"""
                
                if usage:
                    if model == 'Anthropic':
                        html_content += f"""
                    <div class="usage-info">
                        <strong>Tokens:</strong> {usage.get('input_tokens', 0)} in / {usage.get('output_tokens', 0)} out / {usage.get('total_tokens', 0)} total
                    </div>
"""
                    elif model == 'OpenAI':
                        html_content += f"""
                    <div class="usage-info">
                        <strong>Tokens:</strong> {usage.get('prompt_tokens', 0)} in / {usage.get('completion_tokens', 0)} out / {usage.get('total_tokens', 0)} total
                    </div>
"""
                    elif model == 'Gemini':
                        html_content += f"""
                    <div class="usage-info">
                        <strong>Tokens:</strong> {usage.get('prompt_tokens', 0)} in / {usage.get('completion_tokens', 0)} out / {usage.get('total_tokens', 0)} total
                    </div>
"""
                
                html_content += """
                </div>
"""
        
        html_content += """
            </div>
        </div>
"""
    
    html_content += """
    </div>
</body>
</html>
"""
    
    with open(output_file_path, 'w') as f:
        f.write(html_content)
    
    print(f"Side-by-side comparison saved to: {output_file_path}")

if __name__ == "__main__":
    import sys, os
    json_file = sys.argv[1] if len(sys.argv) > 1 else 'data/conversations/conversation.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'public/comparisons/conversation_side_by_side.html'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    create_side_by_side_html(json_file, output_file)