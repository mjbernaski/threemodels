import { validateConfig } from './config.js';
import { createModels, callModelsInParallel } from './models/index.js';
import { ConversationManager } from './conversation.js';

async function main() {
  console.log('Multi-Model AI System - Simple Test');
  console.log('===================================\n');
  
  try {
    validateConfig();
  } catch (error) {
    console.error('Configuration error:', error.message);
    process.exit(1);
  }

  const models = createModels();
  const conversation = new ConversationManager('test-conversation.json');
  
  // Test with a simple prompt
  const prompt = 'Compare the number systems used in ancient Rome and ancient Egypt.';
  console.log(`Prompt: ${prompt}\n`);
  console.log('Sending to all models...\n');
  
  const messages = [{ role: 'user', content: prompt }];
  const responses = await callModelsInParallel(models, messages);
  
  for (const [model, response] of Object.entries(responses)) {
    console.log(`\n=== ${model} Response ===`);
    if (response.error) {
      console.log(`Error: ${response.error}`);
    } else {
      console.log(response.content);
      if (response.usage?.total_tokens) {
        console.log(`\nTokens: ${response.usage.total_tokens}`);
      }
    }
  }
  
  // Save the conversation
  conversation.addRound(prompt, responses);
  await conversation.save();
  console.log('\n\nConversation saved to test-conversation.json');
  
  // Test assessment
  console.log('\n\n--- Running Assessment ---\n');
  
  const assessmentPrompt = conversation.formatAssessmentPrompt(prompt, responses);
  const assessmentMessages = [{ role: 'user', content: assessmentPrompt }];
  
  const assessmentResponses = await callModelsInParallel(models, assessmentMessages);
  
  for (const [model, response] of Object.entries(assessmentResponses)) {
    console.log(`\n=== ${model} Assessment ===`);
    if (response.error) {
      console.log(`Error: ${response.error}`);
    } else {
      console.log(response.content.substring(0, 500) + '...');
    }
  }
  
  conversation.addRound(assessmentPrompt, assessmentResponses, true);
  await conversation.save();
}

main().catch(console.error);