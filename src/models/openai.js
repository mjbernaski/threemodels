import OpenAI from 'openai';
import { BaseModel } from './base.js';
import { config } from '../config.js';

export class OpenAIModel extends BaseModel {
  constructor() {
    super('OpenAI');
    this.client = new OpenAI({
      apiKey: config.openai.apiKey
    });
  }

  async sendMessage(messages, onChunk) {
    try {
      const stream = await this.client.chat.completions.create({
        model: 'gpt-5',
        messages: messages,
        max_completion_tokens: 4096,
        stream: true
      });
      
      let fullContent = '';
      let usage = null;
      
      for await (const chunk of stream) {
        const delta = chunk.choices[0]?.delta?.content || '';
        if (delta) {
          fullContent += delta;
          if (onChunk) {
            onChunk(this.name, delta);
          }
        }
        if (chunk.usage) {
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
}