import { Chess, Square } from "chess.js";
import { GroqModel } from "../types";
import { API_BASE_URL } from "../config";

const API_URL = `${API_BASE_URL}/api/groq`;

export interface GroqMoveResult {
  move: string;
  modelName?: string;
  // "groq" = real model, "fallback" = server heuristic, "local" = client
  // heuristic because the server was unreachable
  source: "groq" | "fallback" | "mock" | "local";
}

// Matches server/config/models.py — used only if the server can't be reached
const FALLBACK_MODELS: GroqModel[] = [
  { key: "llama70b", name: "LLaMA 3.3 (70B)", description: "Meta's flagship 70B model — strong all-round play" },
  { key: "gpt-oss-20b", name: "GPT-OSS (20B)", description: "OpenAI's open-weight reasoning model — thinks before moving" },
  { key: "qwen3-32b", name: "Qwen 3 (32B)", description: "Alibaba's Qwen3 — fast, direct answers" },
];

// Client-side fallback so the game keeps working if the server is down
const getLocalFallbackMove = (fen: string): string => {
  const chess = new Chess(fen);
  const moves = chess.moves({ verbose: true });
  if (moves.length === 0) return "";

  const captures = moves.filter((m) => m.flags.includes("c"));
  const checks = moves.filter((m) => m.san.includes("+"));
  const pool = captures.length > 0 ? captures : checks.length > 0 ? checks : moves;
  const move = pool[Math.floor(Math.random() * pool.length)];
  return move.from + move.to + (move.promotion ?? "");
};

export const getGroqModels = async (): Promise<{ models: GroqModel[]; default: string }> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    const response = await fetch(`${API_URL}/models`, {
      mode: "cors",
      credentials: "omit",
      signal: controller.signal,
      headers: { Accept: "application/json" },
    }).finally(() => clearTimeout(timeoutId));

    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

    const data = await response.json();
    if (!data.models || !Array.isArray(data.models) || data.models.length === 0) {
      throw new Error("Invalid models data format");
    }
    return data;
  } catch (error) {
    console.error("Failed to fetch Groq models, using local list:", error);
    return { models: FALLBACK_MODELS, default: "llama70b" };
  }
};

export const getGroqMove = async (fen: string, previousMoves: string[] = [], modelKey?: string): Promise<GroqMoveResult> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 45000);

    const response = await fetch(`${API_URL}/move`, {
      method: "POST",
      mode: "cors",
      credentials: "omit",
      signal: controller.signal,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ fen, previousMoves, model: modelKey }),
    }).finally(() => clearTimeout(timeoutId));

    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`);
    }

    const data = await response.json();
    if (!data.move) {
      throw new Error(data.error || "No move returned from API");
    }

    return {
      move: data.move,
      modelName: data.modelName,
      source: data.source === "groq" ? "groq" : data.source === "mock" ? "mock" : "fallback",
    };
  } catch (error) {
    console.error("Groq move request failed, using local fallback:", error);
    const fallbackMove = getLocalFallbackMove(fen);
    if (!fallbackMove) throw error;
    return { move: fallbackMove, source: "local" };
  }
};

// Helper function to convert UCI move to source and target squares
export const uciToSquares = (uciMove: string): { from: Square; to: Square; promotion?: string } => {
  const from = uciMove.substring(0, 2) as Square;
  const to = uciMove.substring(2, 4) as Square;
  const promotion = uciMove.length === 5 ? uciMove[4] : undefined;
  return { from, to, promotion };
};
