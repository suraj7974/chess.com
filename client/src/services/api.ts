import axios from "axios";
import { GameModeType } from "../types";

const API = axios.create({ baseURL: "http://localhost:5000" });

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
