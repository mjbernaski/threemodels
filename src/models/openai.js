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
      const startTimeMs = Date.now();
      const stream = await this.client.chat.completions.create({
        model: 'gpt-5',
        messages: messages,
        max_completion_tokens: 4096,
        stream: true,
        stream_options: { include_usage: true }
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
      const responseTimeSeconds = (Date.now() - startTimeMs) / 1000;

      // Normalize usage keys and compute totals if available
      let normalizedUsage = null;
      if (usage) {
        const input = usage.prompt_tokens ?? usage.input_tokens ?? 0;
        const output = usage.completion_tokens ?? usage.output_tokens ?? 0;
        const total = (usage.total_tokens != null) ? usage.total_tokens : (input + output || undefined);
        normalizedUsage = {
          prompt_tokens: usage.prompt_tokens ?? undefined,
          completion_tokens: usage.completion_tokens ?? undefined,
          total_tokens: total,
          // also provide input/output for generic handling
          input_tokens: usage.input_tokens ?? usage.prompt_tokens ?? undefined,
          output_tokens: usage.output_tokens ?? usage.completion_tokens ?? undefined
        };
      }

      return {
        model: this.name,
        content: fullContent,
        usage: normalizedUsage || usage,
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