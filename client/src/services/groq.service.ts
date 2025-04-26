import { Chess, Square } from "chess.js";
import { GroqModel } from "../types";

const isDevelopment = import.meta.env.MODE === "development";
const BASE_URL = isDevelopment ? "http://localhost:5000" : "https://chessserver.vercel.app";

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
    const healthUrl = `${API_URL}/health`;
    console.log("Health URL:", healthUrl);

    // Add timeout to prevent long waits
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(healthUrl, {
      signal: controller.signal,
    }).finally(() => clearTimeout(timeoutId));

    if (!response.ok) {
      console.error("Health check failed with status:", response.status);
      return false;
    }

    const data = await response.json();
    console.log("Health check response:", data);

    // Even if we're using mock mode, return true so the game can proceed
    if (data.status === "ok") {
      if (data.mode === "mock") {
        console.warn("Using mock Groq engine - moves won't be from real AI");
      }
      return true;
    }

    return false;
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

    // Return hardcoded fallback data with updated models (removed Qwen)
    return {
      models: [
        {
          key: "deepseek",
          name: "Deepseek R1 (70B)",
          description: "Powerful 70B model with excellent reasoning capabilities",
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

    // Check if response is successful
    if (!response.ok) {
      // Check content type to handle different response formats
      const contentType = response.headers.get("content-type");

      if (contentType && contentType.includes("application/json")) {
        // Handle JSON error response
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      } else {
        // Handle non-JSON error response (like HTML error pages)
        const textError = await response.text();
        console.error("Received non-JSON error response:", textError);
        throw new Error(`Server error (${response.status}): Non-JSON response received`);
      }
    }

    // Check content type before parsing JSON
    const contentType = response.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
      const textResponse = await response.text();
      console.error("Unexpected non-JSON response:", textResponse);
      throw new Error("Server returned non-JSON response");
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
