// Single source of truth for the backend URL.
// Set VITE_API_URL in .env / Vercel project settings to point at the deployed
// Flask server. Falls back to localhost during development.
// NOTE: dev default is 5001 — port 5000 is occupied by macOS AirPlay, which
// answers requests and silently breaks the API (run the server with PORT=5001).
const isDevelopment = import.meta.env.MODE === "development";

export const API_BASE_URL: string =
  import.meta.env.VITE_API_URL || (isDevelopment ? "http://localhost:5001" : "https://chessserver.vercel.app");
