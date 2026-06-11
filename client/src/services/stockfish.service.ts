import { Chess } from "chess.js";

// Stockfish 18 (lite, single-threaded WASM) running fully in the browser via a
// Web Worker. The engine files are copied to /engine/ at build time (see
// vite.config.ts), so this works on any static host — no backend needed.

const ENGINE_URL = "/engine/stockfish-18-lite-single.js";
const ENGINE_INIT_TIMEOUT = 15000;
const MOVE_TIMEOUT = 20000;

export interface DifficultyPreset {
  key: string;
  label: string;
  description: string;
  skillLevel: number; // 0-20
  moveTimeMs: number;
}

export const DIFFICULTY_PRESETS: DifficultyPreset[] = [
  { key: "easy", label: "Easy", description: "Casual play, makes mistakes", skillLevel: 2, moveTimeMs: 300 },
  { key: "medium", label: "Medium", description: "Club player strength", skillLevel: 8, moveTimeMs: 600 },
  { key: "hard", label: "Hard", description: "Strong tournament play", skillLevel: 15, moveTimeMs: 1000 },
  { key: "max", label: "Maximum", description: "Full engine strength", skillLevel: 20, moveTimeMs: 1500 },
];

let worker: Worker | null = null;
let initPromise: Promise<Worker> | null = null;
// Serialize requests — the engine handles one search at a time
let queue: Promise<unknown> = Promise.resolve();

const initEngine = (): Promise<Worker> => {
  if (initPromise) return initPromise;

  initPromise = new Promise<Worker>((resolve, reject) => {
    let w: Worker;
    try {
      w = new Worker(ENGINE_URL);
    } catch (error) {
      reject(error);
      return;
    }

    const timeout = setTimeout(() => {
      w.terminate();
      reject(new Error("Stockfish engine failed to initialize in time"));
    }, ENGINE_INIT_TIMEOUT);

    const onMessage = (e: MessageEvent) => {
      const line = typeof e.data === "string" ? e.data : "";
      if (line === "uciok") {
        clearTimeout(timeout);
        w.removeEventListener("message", onMessage);
        worker = w;
        resolve(w);
      }
    };

    w.addEventListener("message", onMessage);
    w.addEventListener("error", (e) => {
      clearTimeout(timeout);
      reject(new Error(`Stockfish worker error: ${e.message}`));
    });

    w.postMessage("uci");
  });

  initPromise.catch(() => {
    initPromise = null;
    worker = null;
  });

  return initPromise;
};

const searchBestMove = (w: Worker, fen: string, skillLevel: number, moveTimeMs: number): Promise<string> =>
  new Promise<string>((resolve, reject) => {
    const timeout = setTimeout(() => {
      w.removeEventListener("message", onMessage);
      reject(new Error("Stockfish search timed out"));
    }, MOVE_TIMEOUT);

    const onMessage = (e: MessageEvent) => {
      const line = typeof e.data === "string" ? e.data : "";
      if (line.startsWith("bestmove")) {
        clearTimeout(timeout);
        w.removeEventListener("message", onMessage);
        const move = line.split(" ")[1];
        if (move && move !== "(none)") {
          resolve(move);
        } else {
          reject(new Error("No move available"));
        }
      }
    };

    w.addEventListener("message", onMessage);
    w.postMessage(`setoption name Skill Level value ${skillLevel}`);
    w.postMessage(`position fen ${fen}`);
    w.postMessage(`go movetime ${moveTimeMs}`);
  });

// Heuristic fallback if the WASM engine can't run (very old browsers)
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

export const checkStockfishHealth = async (): Promise<boolean> => {
  try {
    await initEngine();
    return true;
  } catch (error) {
    console.error("Stockfish WASM unavailable:", error);
    return false;
  }
};

export const getStockfishMove = async (fen: string, skillLevel = 20, moveTimeMs = 1000): Promise<string> => {
  const run = queue.then(async () => {
    try {
      const w = await initEngine();
      return await searchBestMove(w, fen, skillLevel, moveTimeMs);
    } catch (error) {
      console.error("Stockfish WASM failed, using heuristic fallback:", error);
      // Reset so the next call retries a fresh worker
      worker?.terminate();
      worker = null;
      initPromise = null;
      return getLocalFallbackMove(fen);
    }
  });
  queue = run.catch(() => undefined);
  return run;
};
