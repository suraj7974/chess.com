import axios from "axios";
import { GameModeType } from "../types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";
const API = axios.create({ baseURL: API_URL });

interface GameResponse {
  gameId: string;
  status: string;
}

interface MoveResponse {
  success: boolean;
  move?: string;
}

export const startGame = (playerType: GameModeType) => API.post<GameResponse>("/start-game", { playerType });

export const getMove = (gameId: string, move: string) => API.post<MoveResponse>("/make-move", { gameId, move });
