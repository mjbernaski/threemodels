import { GoogleGenerativeAI } from '@google/generative-ai';
import { BaseModel } from './base.js';
import { config } from '../config.js';

export class GeminiModel extends BaseModel {
  constructor() {
    super('Gemini');
    this.genAI = new GoogleGenerativeAI(config.google.apiKey);
    this.model = this.genAI.getGenerativeModel({ model: 'gemini-2.5-pro' });
  }

  async sendMessage(messages, onChunk) {
    try {
      const startTimeMs = Date.now();
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

      // Safely extract usage metadata
      if (response && response.usageMetadata) {
        try {
          const prompt_tokens = response.usageMetadata.promptTokenCount;
          const completion_tokens = response.usageMetadata.candidatesTokenCount;
          const total_tokens = response.usageMetadata.totalTokenCount;
          usage = {
            prompt_tokens,
            completion_tokens,
            total_tokens,
            // also provide input/output for generic handling
            input_tokens: prompt_tokens,
            output_tokens: completion_tokens
          };
        } catch (metadataError) {
          console.warn('Failed to extract usage metadata:', metadataError);
          usage = null;
        }
      }
      const responseTimeSeconds = (Date.now() - startTimeMs) / 1000;

      return {
        model: this.name,
        content: fullContent,
        usage,
        response_time: responseTimeSeconds
      };
    } catch (error) {
      return {
        model: this.name,
        error: error.message
      };
    }
  }
}