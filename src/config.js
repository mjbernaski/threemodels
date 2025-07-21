import dotenv from 'dotenv';
dotenv.config();

export const config = {
  anthropic: {
    apiKey: process.env.ANTHROPIC_API_KEY
  },
  openai: {
    apiKey: process.env.OPENAI_API_KEY
  },
  google: {
    apiKey: process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY
  }
};

export function validateConfig() {
  const missing = [];
  if (!config.anthropic.apiKey) missing.push('ANTHROPIC_API_KEY');
  if (!config.openai.apiKey) missing.push('OPENAI_API_KEY');
  if (!config.google.apiKey) missing.push('GEMINI_API_KEY or GOOGLE_API_KEY');
  
  if (missing.length > 0) {
    throw new Error(`Missing required API keys: ${missing.join(', ')}`);
  }
}