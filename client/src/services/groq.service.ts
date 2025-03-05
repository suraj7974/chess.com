import { Chess, Square } from "chess.js";

const isDevelopment = import.meta.env.MODE === "development";
const BASE_URL = isDevelopment ? "http://localhost:5000" : "https://chess-server-mu.vercel.app";

const API_URL = `${BASE_URL}/api/groq`;

interface GroqResponse {
  move?: string;
  error?: string;
}

export const checkGroqHealth = async (): Promise<boolean> => {
  try {
    console.log("Checking Groq API health...");

    // First try the test endpoint
    const testResponse = await fetch(`${API_URL}/test-connection`);
    const testData = await testResponse.json();

    if (testResponse.ok && testData.status === "ok") {
      console.log("Test connection successful:", testData);
      return true;
    }

    // If test fails, try regular health endpoint
    const response = await fetch(`${API_URL}/health`);
    if (!response.ok) {
      console.error("Health check failed with status:", response.status);
      const errorText = await response.text();
      console.error("Error response:", errorText);
      return false;
    }

    const data = await response.json();
    console.log("Health check response:", data);
    return data.status === "ok";
  } catch (error) {
    console.error("Groq API health check failed:", error);
    return false;
  }
};

export const getGroqMove = async (fen: string, previousMoves: string[] = []): Promise<string> => {
  try {
    // First check if engine is healthy
    const isHealthy = await checkGroqHealth();
    if (!isHealthy) {
      throw new Error("Groq API is not available");
    }

    console.log("Requesting Groq move for FEN:", fen);
    console.log("Previous moves:", previousMoves);

    const response = await fetch(`${API_URL}/move`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ fen, previousMoves }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log("Groq API response:", data);

    if (!data.move) {
      throw new Error("No move returned from Groq API");
    }

    return data.move;
  } catch (error) {
    console.error("Error getting Groq move:", error);
    throw error;
  }
};

// Helper function to convert UCI move to source and target squares
export const uciToSquares = (uciMove: string): { from: Square; to: Square } => {
  const from = uciMove.substring(0, 2) as Square;
  const to = uciMove.substring(2, 4) as Square;
  return { from, to };
};
