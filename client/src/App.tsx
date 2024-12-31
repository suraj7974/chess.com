import React from "react";

function App() {
  const fetchGameStatus = async () => {
    const response = await fetch("/api/game/status");
    const data = await response.json();
    console.log("Game Status:", data);
  };

  const fetchAIMove = async () => {
    const response = await fetch("/api/ai/move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fen: "startpos" }),
    });
    const data = await response.json();
    console.log("AI Move:", data);
  };

  return (
    <div>
      <h1>Welcome to Chess Platform</h1>
      <button onClick={fetchGameStatus}>Get Game Status</button>
      <button onClick={fetchAIMove}>Get AI Move</button>
    </div>
  );
}

export default App;
