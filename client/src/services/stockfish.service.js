const API_URL = 'http://localhost:5000/api/stockfish';

export const checkStockfishHealth = async () => {
  try {
    console.log('Checking Stockfish health...');
    const response = await fetch(`${API_URL}/health`);
    const data = await response.json();
    console.log('Health check response:', data);
    return data.status === 'ok';
  } catch (error) {
    console.error('Health check failed:', error);
    return false;
  }
};

export const getStockfishMove = async (fen, skillLevel = 20) => {
  try {
    // First check if engine is healthy
    const isHealthy = await checkStockfishHealth();
    if (!isHealthy) {
      throw new Error('Stockfish engine is not available');
    }

    console.log('Requesting move for FEN:', fen);
    const response = await fetch(`${API_URL}/move`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ fen, skillLevel }),
    });

    const data = await response.json();
    console.log('Server response:', data);

    if (!response.ok) {
      throw new Error(data.error || 'Failed to get move');
    }
    
    if (!data.move) {
      throw new Error('No move returned from server');
    }

    return data.move;
  } catch (error) {
    console.error('Error getting Stockfish move:', error);
    throw error;
  }
};
