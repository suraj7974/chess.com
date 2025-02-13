import axios from "axios";
import { GameModeType } from "../types";

const isDevelopment = import.meta.env.MODE === "development";
const API_URL = isDevelopment ? "http://localhost:5000" : "https://chess-server-kappa.vercel.app"; // Fix: Use actual deployed URL

const API = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

interface GameResponse {
  gameId: string;
  status: string;
}

interface MoveResponse {
  success: boolean;
  move?: string;
}

export const startGame = (playerType: GameModeType) => API.post<GameResponse>("start-game", { playerType });

export const getMove = (gameId: string, move: string) => API.post<MoveResponse>("make-move", { gameId, move });

// Add error interceptor
API.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error);
    return Promise.reject(error);
  }
);
