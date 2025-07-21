export async function callModelsInParallelWithStreaming(models, messages, onChunk) {
  const activeModels = new Set(models.map(m => m.name));
  const results = {};
  
  const promises = models.map(async (model) => {
    try {
      const result = await model.sendMessage(messages, onChunk);
      results[model.name] = result;
    } finally {
      activeModels.delete(model.name);
      if (activeModels.size === 0 && onChunk) {
        onChunk('_complete_', '');
      }
    }
  });
  
  await Promise.all(promises);
  return results;
}