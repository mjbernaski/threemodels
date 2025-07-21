import { validateConfig } from './src/config.js';
import { createModels, callModelsInParallel } from './src/models/index.js';

async function test() {
  console.log('Testing the multi-model system...\n');
  
  try {
    validateConfig();
    console.log('✓ Configuration validated');
  } catch (error) {
    console.error('Configuration error:', error.message);
    process.exit(1);
  }

  const models = createModels();
  console.log('✓ Models created\n');

  const testPrompt = 'What is 2+2?';
  console.log(`Sending test prompt: "${testPrompt}"\n`);

  const messages = [{ role: 'user', content: testPrompt }];
  
  const responses = await callModelsInParallel(models, messages);
  
  for (const [model, response] of Object.entries(responses)) {
    console.log(`\n=== ${model} Response ===`);
    if (response.error) {
      console.log(`Error: ${response.error}`);
    } else {
      console.log(response.content);
      if (response.usage) {
        console.log(`\nTokens: ${response.usage.total_tokens || 'N/A'}`);
      }
    }
  }
}

test().catch(console.error);