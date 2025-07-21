import Anthropic from '@anthropic-ai/sdk';
import { BaseModel } from './base.js';
import { config } from '../config.js';

export class AnthropicModel extends BaseModel {
  constructor() {
    super('Anthropic');
    this.client = new Anthropic({
      apiKey: config.anthropic.apiKey
    });
  }

  async sendMessage(messages, onChunk) {
    try {
      const stream = await this.client.messages.create({
        model: 'claude-3-5-sonnet-latest',
        max_tokens: 4096,
        messages: this.formatMessages(messages),
        stream: true
      });
      
      let fullContent = '';
      let usage = null;
      
      for await (const chunk of stream) {
        if (chunk.type === 'content_block_delta') {
          fullContent += chunk.delta.text;
          if (onChunk) {
            onChunk(this.name, chunk.delta.text);
          }
        } else if (chunk.type === 'message_delta' && chunk.usage) {
          usage = chunk.usage;
        }
      }
      
      return {
        model: this.name,
        content: fullContent,
        usage
      };
    } catch (error) {
      return {
        model: this.name,
        error: error.message
      };
    }
  }

  formatMessages(messages) {
    return messages.map(msg => ({
      role: msg.role === 'system' ? 'assistant' : msg.role,
      content: msg.content
    }));
  }
}