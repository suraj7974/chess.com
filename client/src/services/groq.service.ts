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

// Local fallback function to provide moves when server is unavailable
const getLocalFallbackMove = (fen: string): string => {
  try {
    // Create a chess instance from the current position
    const chess = new Chess(fen);

    // Get all legal moves
    const moves = chess.moves({ verbose: true });

    if (moves.length === 0) {
      return ""; // No moves available (checkmate or stalemate)
    }

    // Use a basic strategy - prioritize captures and checks
    const captures = moves.filter((move) => move.flags.includes("c"));
    const checks = moves.filter((move) => move.san.includes("+"));

    let selectedMove;
    if (captures.length > 0) {
      // Prioritize capturing high-value pieces
      captures.sort((a, b) => {
        const pieceValues = { p: 1, n: 3, b: 3, r: 5, q: 9, k: 0 };
        return (pieceValues[b.captured as keyof typeof pieceValues] || 0) - (pieceValues[a.captured as keyof typeof pieceValues] || 0);
      });
      selectedMove = captures[0];
    } else if (checks.length > 0) {
      // Random check
      selectedMove = checks[Math.floor(Math.random() * checks.length)];
    } else {
      // Random move
      selectedMove = moves[Math.floor(Math.random() * moves.length)];
    }

    // Ensure we're returning a valid move - chess.js verbose moves have from/to properties
    if (selectedMove && selectedMove.from && selectedMove.to) {
      console.log("Generated valid fallback move:", selectedMove.from + selectedMove.to);
      return selectedMove.from + selectedMove.to;
    } else {
      console.error("Failed to generate proper move from:", selectedMove);
      // Last resort - just pick the first move's UCI notation
      const firstMove = moves[0];
      return firstMove.from + firstMove.to;
    }
  } catch (error) {
    console.error("Error generating fallback move:", error);

    // If all else fails, try a simpler approach
    try {
      const chess = new Chess(fen);
      const simpleMoves = chess.moves();
      if (simpleMoves.length > 0) {
        // Get a simple move and convert it
        const move = chess.move(simpleMoves[0]);
        if (move && move.from && move.to) {
          return move.from + move.to;
        }
      }
    } catch (e) {
      console.error("Even simple fallback failed:", e);
    }

    console.warn("Using emergency default move");
    return "e7e6"; // Default emergency fallback that's usually legal for black
  }
};

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
      // Add explicit mode and credentials to help with CORS
      mode: "cors",
      credentials: "omit", // Don't send credentials to work with CORS *
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
    }).finally(() => clearTimeout(timeoutId));

    if (!response.ok) {
      console.error("Health check failed with status:", response.status);
      console.error("Response headers:", [...response.headers.entries()]);

      // If we got a 404, the endpoint might not be deployed yet
      if (response.status === 404) {
        console.warn("Health endpoint not found (404). This may be temporary during deployment.");
        // Return true anyway to allow the game to proceed with fallback modes
        return true;
      }

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

    // Special handling for CORS and network errors
    if (error instanceof TypeError || String(error).includes("CORS") || String(error).includes("network")) {
      console.warn("Health check failed with possible CORS or network issue. Continuing with client-side fallback.");
      // Return true to allow the game to proceed with fallbacks
      return true;
    }

    return false;
  }
};

export const getGroqModels = async (): Promise<{ models: GroqModel[]; default: string }> => {
  try {
    console.log("Fetching Groq models...");
    const url = `${API_URL}/models`;
    console.log("Models URL:", url);

    const response = await fetch(url, {
      // Add explicit mode and credentials to help with CORS
      mode: "cors",
      credentials: "omit", // Don't send credentials to work with CORS *
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
    });

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

    try {
      console.log(`Requesting Groq move using model: ${modelKey || "default"}`);

      const response = await fetch(`${API_URL}/move`, {
        method: "POST",
        mode: "cors",
        credentials: "omit", // Don't send credentials to work with CORS *
        headers: {
          Accept: "application/json",
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
        console.error("Move request failed with status:", response.status);
        console.error("Response headers:", [...response.headers.entries()]);

        // If server request fails, use local fallback
        console.warn(`Server returned ${response.status} - using local fallback`);
        const fallbackMove = getLocalFallbackMove(fen);
        console.log("Using local fallback move:", fallbackMove);
        return fallbackMove;
      }

      // Check content type before parsing JSON
      const contentType = response.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        const textResponse = await response.text();
        console.error("Unexpected non-JSON response:", textResponse);

        // Use local fallback for non-JSON responses
        const fallbackMove = getLocalFallbackMove(fen);
        console.log("Using local fallback move due to non-JSON response:", fallbackMove);
        return fallbackMove;
      }

      const data = await response.json();
      console.log("Groq API response:", data);

      if (!data.move) {
        const fallbackMove = getLocalFallbackMove(fen);
        console.log("No move returned from API, using local fallback:", fallbackMove);
        return fallbackMove;
      }

      return data.move;
    } catch (error) {
      console.error("Error getting Groq move:", error);

      // Use local fallback for any network errors
      const fallbackMove = getLocalFallbackMove(fen);
      console.log("Using local fallback move due to error:", fallbackMove);
      return fallbackMove;
    }
  } catch (error) {
    console.error("Error in Groq move generation:", error);

    // If the error looks like a CORS error, add more diagnostic information
    if (String(error).includes("CORS")) {
      console.error("Possible CORS issue detected. Browser origin:", window.location.origin);
      console.error("API URL being accessed:", `${API_URL}/move`);
    }

    // Final fallback - this ensures the game continues even with errors
    try {
      const fallbackMove = getLocalFallbackMove(fen);
      console.log("Using emergency fallback move:", fallbackMove);
      return fallbackMove;
    } catch (e) {
      console.error("Even local fallback generation failed:", e);
      throw error; // Only throw if absolutely everything fails
    }
  }
};

// Helper function to convert UCI move to source and target squares
export const uciToSquares = (uciMove: string): { from: Square; to: Square } => {
  const from = uciMove.substring(0, 2) as Square;
  const to = uciMove.substring(2, 4) as Square;
  return { from, to };
};
