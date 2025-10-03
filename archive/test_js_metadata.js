#!/usr/bin/env node

// Quick test to verify JavaScript metadata fix
import { createModels, callModelsInParallel } from './src/models/index.js';
import { ConversationManager } from './src/conversation.js';

async function testJsMetadata() {
    console.log('🔍 Testing JavaScript metadata fix...\n');

    try {
        const models = createModels();
        const conversation = new ConversationManager('test_js_metadata.json');

        const testPrompt = "Say hello briefly";
        const messages = [{ role: 'user', content: testPrompt }];

        console.log(`Testing with: "${testPrompt}"`);

        const responses = await callModelsInParallel(models, messages);

        for (const [modelName, response] of Object.entries(responses)) {
            if (response.error) {
                console.log(`❌ ${modelName}: ${response.error}`);
                if (response.error.toLowerCase().includes('metadata')) {
                    console.log(`🚨 METADATA ERROR FOUND in ${modelName}!`);
                }
            } else {
                console.log(`✅ ${modelName}: Success (${response.content.length} chars)`);
                if (response.usage) {
                    console.log(`   Usage: ${JSON.stringify(response.usage)}`);
                }
            }
        }

        conversation.addRound(testPrompt, responses);
        await conversation.save();

        console.log('\n✅ JavaScript metadata test completed!');

    } catch (error) {
        console.error('🚨 Test failed:', error.message);
        if (error.message.toLowerCase().includes('metadata')) {
            console.log('🚨 METADATA ERROR FOUND in test!');
        }
    }
}

testJsMetadata();