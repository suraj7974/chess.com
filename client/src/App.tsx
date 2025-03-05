import { useState } from "react";
import { ChakraProvider, Box } from "@chakra-ui/react";
import ChessGame from "./components/ChessGame";
import GameModeSelector from "./components/GameModeSelector";
import { GameModeType } from "./types";
import "./App.css";

function App() {
  const [gameMode, setGameMode] = useState<GameModeType | null>(null);

  const handleSelectMode = (mode: GameModeType) => {
    setGameMode(mode);
  };

  const handleRestartGame = () => {
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
