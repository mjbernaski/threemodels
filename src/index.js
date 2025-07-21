import readline from 'readline';
import { validateConfig } from './config.js';
import { createModels, callModelsInParallel } from './models/index.js';
import { ConversationManager } from './conversation.js';

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const question = (prompt) => new Promise(resolve => rl.question(prompt, resolve));

async function main() {
  console.log('Multi-Model AI Conversation System');
  console.log('==================================\n');
  
  try {
    validateConfig();
  } catch (error) {
    console.error('Configuration error:', error.message);
    process.exit(1);
  }

  const models = createModels();
  const conversation = new ConversationManager();
  await conversation.load();

  console.log('Commands:');
  console.log('  - Type your prompt and press Enter to send to all models');
  console.log('  - Type "assess" to have models analyze the previous responses');
  console.log('  - Type "exit" to quit and save the conversation\n');

  while (true) {
    const input = await question('\n> ');
    
    if (input.toLowerCase() === 'exit') {
      await conversation.save();
      console.log('\nConversation saved. Goodbye!');
      break;
    }
    
    if (input.toLowerCase() === 'assess') {
      const lastResponses = conversation.getLastResponses();
      if (!lastResponses) {
        console.log('No previous responses to assess.');
        continue;
      }
      
      const lastRound = conversation.conversation.rounds[conversation.conversation.rounds.length - 1];
      const assessmentPrompt = conversation.formatAssessmentPrompt(
        lastRound.userPrompt,
        lastResponses
      );
      
      console.log('\nSending assessment request to all models...\n');
      
      const assessmentMessages = [{
        role: 'user',
        content: assessmentPrompt
      }];
      
      const responses = await callModelsInParallel(models, assessmentMessages);
      
      for (const [model, response] of Object.entries(responses)) {
        console.log(`\n=== ${model} Assessment ===`);
        if (response.error) {
          console.log(`Error: ${response.error}`);
        } else {
          console.log(response.content);
        }
      }
      
      conversation.addRound(assessmentPrompt, responses, true);
      await conversation.save();
      continue;
    }
    
    console.log('\nSending to all models...\n');
    
    const messages = conversation.getMessages();
    messages.push({ role: 'user', content: input });
    
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
    
    conversation.addRound(input, responses);
    await conversation.save();
  }
  
  rl.close();
}

main().catch(console.error);