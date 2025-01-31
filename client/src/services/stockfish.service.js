const API_URL = 'http://localhost:5000';

export const checkStockfishHealth = async () => {
  try {
    const response = await fetch(`${API_URL}/health`);
    const data = await response.json();
    return data.status === 'ok';
  } catch (error) {
    console.error('Stockfish health check failed:', error);
    return false;
  }
};

export const getStockfishMove = async (fen, skillLevel = 20) => {
  try {
    // Check health first
    const isHealthy = await checkStockfishHealth();
    if (!isHealthy) {
      throw new Error('Stockfish engine is not available');
    }

    const response = await fetch(`${API_URL}/get-move`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ fen, skillLevel }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to get move');
    }
    
    const data = await response.json();
    return data.move;
  } catch (error) {
    console.error('Error getting Stockfish move:', error);
    throw error;
  }
};
