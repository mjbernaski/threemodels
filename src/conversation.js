import fs from 'fs/promises';
import path from 'path';

export class ConversationManager {
  constructor(filename = path.join('data', 'conversations', 'conversation.json')) {
    this.filename = filename;
    this.conversation = {
      rounds: [],
      metadata: {
        startTime: new Date().toISOString(),
        totalRounds: 0
      }
    };
  }

  async load() {
    try {
      const data = await fs.readFile(this.filename, 'utf8');
      this.conversation = JSON.parse(data);
    } catch (error) {
      console.log('Starting new conversation');
    }
  }

  async save() {
    // Ensure the output directory exists
    try {
      await fs.mkdir(path.dirname(this.filename), { recursive: true });
    } catch (e) {
      // ignore mkdir errors; write will surface issues
    }
    await fs.writeFile(this.filename, JSON.stringify(this.conversation, null, 2));
  }

  addRound(userPrompt, modelResponses, isAssessment = false) {
    const round = {
      id: this.conversation.rounds.length + 1,
      timestamp: new Date().toISOString(),
      userPrompt,
      responses: modelResponses,
      isAssessment
    };
    
    this.conversation.rounds.push(round);
    this.conversation.metadata.totalRounds++;
    this.conversation.metadata.lastUpdated = new Date().toISOString();
  }

  getMessages() {
    const messages = [];
    
    for (const round of this.conversation.rounds) {
      messages.push({
        role: 'user',
        content: round.userPrompt
      });
      
      if (!round.isAssessment && round.responses.Anthropic && !round.responses.Anthropic.error) {
        messages.push({
          role: 'assistant',
          content: round.responses.Anthropic.content
        });
      }
    }
    
    return messages;
  }

  getLastResponses() {
    if (this.conversation.rounds.length === 0) return null;
    return this.conversation.rounds[this.conversation.rounds.length - 1].responses;
  }

  formatAssessmentPrompt(originalPrompt, responses) {
    let prompt = `Original prompt: "${originalPrompt}"\n\n`;
    prompt += 'Here are the responses from three different AI models:\n\n';
    
    for (const [model, response] of Object.entries(responses)) {
      prompt += `${model} Response:\n`;
      if (response.error) {
        prompt += `[Error: ${response.error}]\n\n`;
      } else {
        prompt += `${response.content}\n\n`;
      }
    }
    
    prompt += 'Please analyze and compare these responses.';
    return prompt;
  }
}