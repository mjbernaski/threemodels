import { AnthropicModel } from './anthropic.js';
import { OpenAIModel } from './openai.js';
import { GeminiModel } from './gemini.js';

export function createModels() {
  return [
    new AnthropicModel(),
    new OpenAIModel(),
    new GeminiModel()
  ];
}

export async function callModelsInParallel(models, messages) {
  const promises = models.map(model => model.sendMessage(messages));
  const results = await Promise.all(promises);
  
  return results.reduce((acc, result) => {
    acc[result.model] = result;
    return acc;
  }, {});
}