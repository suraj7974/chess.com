import { useState } from "react";
import { ChakraProvider, Box } from "@chakra-ui/react";
import ChessGame from "./components/ChessGame";
import GameModeSelector from "./components/GameModeSelector";
import { GameModeType } from "./types";
import "./App.css";

function App() {
  const [gameMode, setGameMode] = useState<GameModeType | null>(null);

  console.log("Current game mode:", gameMode); // Add debug logging

  const handleSelectMode = (mode: GameModeType) => {
    console.log(`Selecting game mode: ${mode}`);
    setGameMode(mode);
  };

  const handleRestartGame = () => {
    console.log("Restarting game / changing opponent");
    setGameMode(null);
  };

  return (
    <ChakraProvider>
      <Box className="app-container">
        {gameMode ? <ChessGame gameMode={gameMode} onRestartGame={handleRestartGame} /> : <GameModeSelector onSelect={handleSelectMode} />}
      </Box>
    </ChakraProvider>
  );
}

export default App;
