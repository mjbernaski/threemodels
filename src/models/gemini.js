import { GoogleGenerativeAI } from '@google/generative-ai';
import { BaseModel } from './base.js';
import { config } from '../config.js';

export class GeminiModel extends BaseModel {
  constructor() {
    super('Gemini');
    this.genAI = new GoogleGenerativeAI(config.google.apiKey);
    this.model = this.genAI.getGenerativeModel({ model: 'gemini-1.5-pro-latest' });
  }

  async sendMessage(messages, onChunk) {
    try {
      const history = messages.slice(0, -1).map(msg => ({
        role: msg.role === 'assistant' ? 'model' : 'user',
        parts: [{ text: msg.content }]
      }));
      
      const chat = this.model.startChat({ history });
      const result = await chat.sendMessageStream(messages[messages.length - 1].content);
      
      let fullContent = '';
      let usage = null;
      
      for await (const chunk of result.stream) {
        const chunkText = chunk.text();
        if (chunkText) {
          fullContent += chunkText;
          if (onChunk) {
            onChunk(this.name, chunkText);
          }
        }
      }
      
      const response = await result.response;
      usage = {
        prompt_tokens: response.usageMetadata?.promptTokenCount,
        completion_tokens: response.usageMetadata?.candidatesTokenCount,
        total_tokens: response.usageMetadata?.totalTokenCount
      };
      
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