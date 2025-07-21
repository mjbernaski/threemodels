export class BaseModel {
  constructor(name) {
    this.name = name;
  }

  async sendMessage(messages, onChunk) {
    throw new Error('sendMessage must be implemented by subclass');
  }

  formatMessages(messages) {
    return messages;
  }
}