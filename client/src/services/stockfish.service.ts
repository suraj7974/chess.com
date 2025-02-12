const isDevelopment = import.meta.env.MODE === "development";
const BASE_URL = isDevelopment ? "http://localhost:5000" : "https://vercel.com/suraj-patels-projects-a4792e8b/chess-server";

const API_URL = `${BASE_URL}/api/stockfish`;

interface StockfishResponse {
  status?: string;
  move?: string;
  error?: string;
}

export const checkStockfishHealth = async (): Promise<boolean> => {
  try {
    console.log("Checking Stockfish health...");
    const response = await fetch(`${API_URL}/health`);
    const data = await response.json();
    console.log("Health check response:", data);
    return data.status === "ok";
  } catch (error) {
    console.error("Health check failed:", error);
    return false;
  }
};

export const getStockfishMove = async (fen: string, skillLevel: number = 20): Promise<string> => {
  try {
    // First check if engine is healthy
    const isHealthy = await checkStockfishHealth();
    if (!isHealthy) {
      throw new Error("Stockfish engine is not available");
    }

    console.log("Requesting move for FEN:", fen);
    const response = await fetch(`${API_URL}/move`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ fen, skillLevel }),
    });

    const data = await response.json();
    console.log("Server response:", data);

    if (!response.ok) {
      throw new Error(data.error || "Failed to get move");
    }

    if (!data.move) {
      throw new Error("No move returned from server");
    }

    return data.move;
  } catch (error) {
    console.error("Error getting Stockfish move:", error);
    throw error;
  }
};
