import { Chess, Square } from "chess.js";
import { GroqModel } from "../types";

const isDevelopment = import.meta.env.MODE === "development";
const BASE_URL = isDevelopment ? "http://localhost:5000" : "https://chess-server-mu.vercel.app";

const API_URL = `${BASE_URL}/api/groq`;

interface GroqResponse {
  move?: string;
  error?: string;
  model?: string;
  modelName?: string;
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

export const getGroqModels = async (): Promise<{ models: GroqModel[]; default: string }> => {
  try {
    console.log("Fetching Groq models...");
    const url = `${API_URL}/models`;
    console.log("Models URL:", url);

    const response = await fetch(url);

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Failed to fetch models (${response.status}):`, errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log("Received models data:", data);

    if (!data.models || !Array.isArray(data.models) || data.models.length === 0) {
      console.error("Invalid models data received:", data);
      throw new Error("Invalid models data format");
    }

    return data;
  } catch (error) {
    console.error("Failed to fetch Groq models:", error);

    // Return hardcoded fallback data with all the models
    return {
      models: [
        {
          key: "deepseek",
          name: "Deepseek R1 (70B)",
          description: "Powerful 70B model with excellent reasoning capabilities",
        },
        {
          key: "qwen",
          name: "Qwen QWQ (32B)",
          description: "Good balance of performance and speed",
        },
        {
          key: "mixtral",
          name: "Mixtral 8x7B",
          description: "Strong mixture-of-experts model with long context",
        },
        {
          key: "llama3",
          name: "LLaMa 3.3 (70B)",
          description: "Latest LLaMa model with versatile capabilities",
        },
        {
          key: "gemma2",
          name: "Gemma 2 (9B)",
          description: "Smaller but efficient instruction-tuned model",
        },
      ],
      default: "llama3",
    };
  }
};

export const getGroqMove = async (fen: string, previousMoves: string[] = [], modelKey?: string): Promise<string> => {
  try {
    // First check if engine is healthy
    const isHealthy = await checkGroqHealth();
    if (!isHealthy) {
      throw new Error("Groq API is not available");
    }

    console.log(`Requesting Groq move using model: ${modelKey || "default"}`);

    const response = await fetch(`${API_URL}/move`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        fen,
        previousMoves,
        model: modelKey, // Include the model key in the request
      }),
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
