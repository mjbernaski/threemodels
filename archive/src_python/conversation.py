import json
import asyncio
import os
import html
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class ConversationManager:
    def __init__(self, filename: str = 'data/conversations/conversation.json'):
        self.filename = filename
        self.conversation = {
            'rounds': [],
            'metadata': {
                'start_time': datetime.now().isoformat(),
                'total_rounds': 0
            }
        }
    
    async def load(self):
        """Load conversation from file"""
        try:
            with open(self.filename, 'r') as f:
                self.conversation = json.load(f)
        except FileNotFoundError:
            print('Starting new conversation')
    
    async def save(self):
        """Save conversation to file and generate HTML comparison"""
        # Ensure output directory exists
        Path(self.filename).parent.mkdir(parents=True, exist_ok=True)
        with open(self.filename, 'w') as f:
            json.dump(self.conversation, f, indent=2)

        # Generate HTML comparison file
        self.generate_html_comparison()
    
    def add_round(self, user_prompt: str, model_responses: Dict[str, Any], is_assessment: bool = False):
        """Add a conversation round"""
        round_data = {
            'id': len(self.conversation['rounds']) + 1,
            'timestamp': datetime.now().isoformat(),
            'userPrompt': user_prompt,
            'responses': model_responses,
            'isAssessment': is_assessment
        }
        
        self.conversation['rounds'].append(round_data)
        self.conversation['metadata']['total_rounds'] += 1
        self.conversation['metadata']['last_updated'] = datetime.now().isoformat()
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Get messages for model context"""
        messages = []
        
        for round_data in self.conversation['rounds']:
            messages.append({
                'role': 'user',
                'content': round_data['userPrompt']
            })
            
            if (not round_data['isAssessment'] and 
                'Anthropic' in round_data['responses'] and 
                'error' not in round_data['responses']['Anthropic']):
                messages.append({
                    'role': 'assistant',
                    'content': round_data['responses']['Anthropic']['content']
                })
        
        return messages
    
    def get_last_responses(self) -> Optional[Dict[str, Any]]:
        """Get the last round's responses"""
        if not self.conversation['rounds']:
            return None
        return self.conversation['rounds'][-1]['responses']
    
    def format_assessment_prompt(self, original_prompt: str, responses: Dict[str, Any]) -> str:
        """Format prompt for model assessment"""
        prompt = f'Original prompt: "{original_prompt}"\n\n'
        prompt += 'Here are the responses from three different AI models:\n\n'
        
        for model, response in responses.items():
            prompt += f'{model} Response:\n'
            if 'error' in response:
                prompt += f'[Error: {response["error"]}]\n\n'
            else:
                prompt += f'{response["content"]}\n\n'
        
        prompt += 'Please analyze and compare these responses.'
        return prompt

    def _generate_previous_conversations_list(self):
        """Generate HTML for list of previous conversations"""
        comparisons_dir = Path(__file__).parent.parent / 'conversation_comparisons'

        if not comparisons_dir.exists():
            return ''

        html_files = sorted(
            [f for f in comparisons_dir.glob('conversation_*.html')],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        if not html_files:
            return ''

        items_html = []
        for html_file in html_files[:10]:
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                prompt_match = re.search(r'<div class="user-prompt">.*?<div>.*?</div>.*?<div>(.*?)</div>', content, re.DOTALL)
                if prompt_match:
                    prompt_text = prompt_match.group(1).strip()
                    prompt_text = re.sub(r'<[^>]+>', '', prompt_text)
                    prompt_text = html.unescape(prompt_text)
                    if len(prompt_text) > 150:
                        prompt_text = prompt_text[:150] + '...'
                else:
                    prompt_text = 'No prompt found'

                timestamp_str = html_file.stem.replace('conversation_', '')
                try:
                    dt = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                    date_str = dt.strftime('%B %d, %Y at %I:%M %p')
                except:
                    date_str = timestamp_str

                items_html.append(f'''
                <div class="conversation-item">
                    <a href="{html_file.name}">
                        <div class="conversation-date">{date_str}</div>
                        <div class="conversation-snippet">{html.escape(prompt_text)}</div>
                    </a>
                </div>''')
            except Exception:
                continue

        if not items_html:
            return ''

        return f'''
        <div class="previous-conversations">
            <h2>📚 Previous Conversations</h2>
            <div class="conversation-list">
                {''.join(items_html)}
            </div>
        </div>'''

    def markdown_to_html(self, text):
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

        for line in lines:
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

        if in_list:
            new_lines.append('</' + in_list + '>')

        text = '\n'.join(new_lines)

        # Convert line breaks to paragraphs
        paragraphs = text.split('\n\n')
        text = ''.join('<p>' + p + '</p>' if not p.startswith('<') else p for p in paragraphs if p.strip())

        return text

    def generate_html_comparison(self):
        """Generate HTML file with side-by-side comparison of model responses"""
        if not self.conversation['rounds']:
            return

        # Create comparisons directory if it doesn't exist
        comparisons_dir = Path('public') / 'comparisons'
        comparisons_dir.mkdir(exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_filename = comparisons_dir / f'conversation_{timestamp}.html'

        # Generate HTML content
        html_content = self._generate_html_content()

        # Write HTML file
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f'\n📄 HTML comparison saved to: {html_filename}')

        # Also write/update latest.html for easy access
        latest_link = comparisons_dir / 'latest.html'
        try:
            with open(latest_link, 'w', encoding='utf-8') as f:
                f.write(html_content)
        except Exception:
            pass

    def _generate_html_content(self):
        """Generate the HTML content for the comparison"""
        html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Model Comparison - {timestamp}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }}
        h1 {{
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .metadata {{
            color: #666;
            font-size: 0.9em;
        }}
        .round {{
            margin-bottom: 40px;
            border: 1px solid #ddd;
            border-radius: 10px;
            overflow: hidden;
        }}
        .user-prompt {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            font-weight: 500;
        }}
        .assessment-prompt {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        .responses {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1px;
            background: #ddd;
        }}
        .response {{
            background: white;
            padding: 20px;
            position: relative;
        }}
        .model-name {{
            font-weight: bold;
            color: #555;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }}
        .response-content {{
            color: #333;
            line-height: 1.6;
        }}
        .response-content p {{ margin-bottom: 10px; }}
        .response-content ul, .response-content ol {{ margin-left: 20px; margin-bottom: 10px; }}
        .response-content li {{ margin-bottom: 5px; }}
        .response-content pre {{
            background: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 10px 0;
        }}
        .response-content code {{
            background: #f0f0f0;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        .response-content pre code {{
            background: transparent;
            padding: 0;
        }}
        .error {{
            color: #d32f2f;
            font-style: italic;
        }}
        .usage-info {{
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #eee;
            font-size: 0.85em;
            color: #666;
        }}
        .timestamp {{
            font-size: 0.85em;
            color: #999;
            margin-top: 10px;
        }}
        @media (max-width: 1200px) {{
            .responses {{ grid-template-columns: 1fr; }}
        }}
        .previous-conversations {{
            margin-top: 40px;
            padding-top: 30px;
            border-top: 2px solid #eee;
        }}
        .previous-conversations h2 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}
        .conversation-list {{
            display: grid;
            gap: 15px;
        }}
        .conversation-item {{
            background: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            transition: all 0.2s ease;
            cursor: pointer;
        }}
        .conversation-item:hover {{
            background: #e9ecef;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .conversation-item a {{
            text-decoration: none;
            color: inherit;
            display: block;
        }}
        .conversation-date {{
            font-weight: bold;
            color: #667eea;
            font-size: 0.95em;
            margin-bottom: 8px;
        }}
        .conversation-snippet {{
            color: #555;
            font-size: 0.9em;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Model Comparison</h1>
            <div class="metadata">
                <p>Session started: {start_time}</p>
                <p>Total rounds: {total_rounds}</p>
                <p>Generated: {generated_time}</p>
            </div>
        </div>
        {rounds_html}
        {previous_conversations}
    </div>
</body>
</html>'''

        rounds_html = []
        for round_data in self.conversation['rounds']:
            round_class = 'assessment-prompt' if round_data.get('isAssessment') else 'user-prompt'
            round_html = f'''
        <div class="round">
            <div class="{round_class}">
                <div>Round {round_data['id']}</div>
                <div>{html.escape(round_data['userPrompt'])}</div>
                <div class="timestamp">Time: {round_data['timestamp']}</div>
            </div>
            <div class="responses">'''

            for model in ['Anthropic', 'OpenAI', 'Gemini']:
                if model in round_data['responses']:
                    response = round_data['responses'][model]
                    if 'error' in response:
                        content_html = f'<div class="error">Error: {html.escape(response["error"])}</div>'
                        if response.get('response_time') or response.get('attempts'):
                            content_html += '<div class="usage-info">'
                            if response.get('response_time'):
                                content_html += f'⏱️ Failed after: {response["response_time"]:.2f}s<br>'
                            if response.get('attempts'):
                                content_html += f'🔄 Failed after {response["attempts"]} attempts<br>'
                            content_html += '</div>'
                    else:
                        content_html = f'<div class="response-content">{self.markdown_to_html(response["content"])}</div>'
                        if response.get('usage') or response.get('response_time') or response.get('attempts'):
                            content_html += '<div class="usage-info">'

                            if response.get('usage'):
                                usage = response['usage']
                                content_html += f'''Tokens - Input: {usage.get('prompt_tokens', 'N/A')} |
                                    Output: {usage.get('completion_tokens', 'N/A')} |
                                    Total: {usage.get('total_tokens', 'N/A')}<br>'''

                            if response.get('response_time'):
                                content_html += f'⏱️ Response time: {response["response_time"]:.2f}s<br>'

                            if response.get('attempts'):
                                attempts = response['attempts']
                                if attempts > 1:
                                    content_html += f'🔄 Required {attempts} attempts<br>'

                            content_html += '</div>'
                else:
                    content_html = '<div class="error">No response</div>'

                round_html += f'''
                <div class="response">
                    <div class="model-name">{model}</div>
                    {content_html}
                </div>'''

            round_html += '''
            </div>
        </div>'''
            rounds_html.append(round_html)

        previous_conversations_html = self._generate_previous_conversations_list()

        return html_template.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            start_time=self.conversation['metadata'].get('start_time', 'Unknown'),
            total_rounds=self.conversation['metadata'].get('total_rounds', 0),
            generated_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            rounds_html=''.join(rounds_html),
            previous_conversations=previous_conversations_html
        )