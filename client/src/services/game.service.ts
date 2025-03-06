// Check if this file exists and update any URL references
const isDevelopment = import.meta.env.MODE === "development";
const BASE_URL = isDevelopment ? "http://localhost:5000" : "https://chessserver.vercel.app";
