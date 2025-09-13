// TypeScript interfaces for chess.js
interface ChessMove {
  color: string;
  from: string;
  to: string;
  flags: string;
  piece: string;
  san: string;
  captured?: string;
  promotion?: string;
}

// Import Chess.js properly
import { Chess } from "chess.js";

const isDevelopment = import.meta.env.MODE === "development";

const BASE_URL = isDevelopment ? "http://localhost:5000" : "https://chessserver.vercel.app";

const API_URL = `${BASE_URL}/api/stockfish`;

interface StockfishResponse {
  status?: string;
  move?: string;
  error?: string;
}

// Local fallback function to provide moves when the server is unavailable
const getLocalFallbackMove = (fen: string): string => {
  try {
    // Use the properly imported Chess class
    const chess = new Chess(fen);
    const moves = chess.moves({ verbose: true }) as ChessMove[];

    if (moves.length === 0) {
      return ""; // No moves available
    }

    // Use a basic strategy - prioritize captures and checks
    const captures = moves.filter((move: ChessMove) => move.flags.includes("c"));
    const checks = moves.filter((move: ChessMove) => move.san.includes("+"));

    let selectedMove: ChessMove;
    if (captures.length > 0) {
      // Prioritize capturing high-value pieces
      captures.sort((a: ChessMove, b: ChessMove) => {
        const pieceValues: { [key: string]: number } = { p: 1, n: 3, b: 3, r: 5, q: 9, k: 0 };
        // Safe property access with type assertion and fallback to 0
        const valueA = a.captured ? pieceValues[a.captured as string] || 0 : 0;
        const valueB = b.captured ? pieceValues[b.captured as string] || 0 : 0;
        return valueB - valueA;
      });
      selectedMove = captures[0];
    } else if (checks.length > 0) {
      // Choose a random check
      selectedMove = checks[Math.floor(Math.random() * checks.length)];
    } else {
      // Choose a random move
      selectedMove = moves[Math.floor(Math.random() * moves.length)];
    }

    // Ensure we're returning a valid move
    if (selectedMove && selectedMove.from && selectedMove.to) {
      console.log("Generated valid fallback move:", selectedMove.from + selectedMove.to);
      return selectedMove.from + selectedMove.to;
    } else {
      // Fallback to the first move
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

    // Default emergency move for white
    return "e2e4";
  }
};

export const checkStockfishHealth = async (): Promise<boolean> => {
  try {
    console.log("Checking Stockfish health...");
    const url = `${API_URL}/health`;
    console.log("API URL:", url);

    const response = await fetch(url, {
      method: "GET",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      mode: "cors", // Explicitly set CORS mode
      credentials: "omit", // Don't send credentials to work with CORS *
    });

    if (!response.ok) {
      console.error("Response status:", response.status);
      console.error("Response headers:", [...response.headers.entries()]);
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log("Health check response:", data);
    return data.status === "ok";
  } catch (error) {
    console.error("Health check failed:", error);

    // Return true for CORS or network errors to use local fallback
    if (error instanceof TypeError || String(error).includes("CORS") || String(error).includes("network")) {
      console.warn("Health check failed with possible CORS or network issue. Using local fallback.");
      return true;
    }

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

    try {
      // Attempt to get move from server
      const response = await fetch(`${API_URL}/move`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        mode: "cors",
        credentials: "omit", // Don't send credentials to work with CORS *
        body: JSON.stringify({ fen, skillLevel }),
      });

      if (!response.ok) {
        // If server request fails, use local fallback
        console.warn(`Server returned ${response.status} - using local fallback`);
        const fallbackMove = getLocalFallbackMove(fen);
        console.log("Using local fallback move:", fallbackMove);
        return fallbackMove;
      }

      const data = await response.json();
      console.log("Server response:", data);

      if (!data.move) {
        throw new Error("No move returned from server");
      }

      return data.move;
    } catch (error) {
      console.error("Error communicating with server:", error);

      // Use local fallback for any network errors
      const fallbackMove = getLocalFallbackMove(fen);
      console.log("Using local fallback move due to error:", fallbackMove);
      return fallbackMove;
    }
  } catch (error) {
    console.error("Error getting Stockfish move:", error);
    // Final fallback - this ensures the game continues even with errors
    try {
      return getLocalFallbackMove(fen);
    } catch (e) {
      console.error("Even fallback generation failed:", e);
      throw error; // Only throw if absolutely everything fails
    }
  }
};
