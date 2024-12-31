import axios from 'axios';

const API = axios.create({ baseURL: 'http://localhost:5000' });

export const startGame = (playerType) => API.post('/start-game', { playerType });
export const getMove = (gameId, move) => API.post('/make-move', { gameId, move });
