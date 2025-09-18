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
        model: 'claude-sonnet-4-20250514',
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
      // Enhanced error handling with more context
      console.error('🚨 ANTHROPIC ERROR DEBUG:', error);

      let detailedError;
      const errorMsg = error.message?.toLowerCase() || '';
      const statusCode = error.status || error.response?.status;
      const errorType = error.error?.type || '';

      if (statusCode === 401) {
        detailedError = `Authentication failed (401): Check API key validity`;
      } else if (statusCode === 429) {
        detailedError = `Rate limited (429): Too many requests, try again later`;
      } else if (statusCode === 500 || statusCode === 502 || statusCode === 503) {
        detailedError = `Anthropic server error (${statusCode}): Service temporarily unavailable`;
      } else if (statusCode === 400) {
        detailedError = `Invalid request (400): ${error.message}`;
      } else if (errorType === 'overloaded_error') {
        detailedError = `Service overloaded: Anthropic servers are experiencing high demand`;
      } else if (errorMsg.includes('connection') || errorMsg.includes('timeout') || errorMsg.includes('network') || errorMsg.includes('enotfound') || errorMsg.includes('econnreset')) {
        detailedError = `Network connection error: Unable to reach Anthropic servers - ${error.message}`;
      } else if (errorMsg.includes('api') && errorMsg.includes('key')) {
        detailedError = `API key error: ${error.message}`;
      } else if (errorMsg.includes('quota') || errorMsg.includes('billing')) {
        detailedError = `Quota/billing issue: ${error.message}`;
      } else {
        detailedError = `Anthropic API error${statusCode ? ` (${statusCode})` : ''}: ${error.message}`;
      }

      return {
        model: this.name,
        error: detailedError
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