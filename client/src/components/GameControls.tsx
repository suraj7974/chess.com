import { Button, HStack, Select } from "@chakra-ui/react";
import { GameModeType } from "../types";

interface GameControlsProps {
  gameMode: GameModeType;
  setGameMode: (mode: GameModeType) => void;
  onNewGame: () => void;
  disabled: boolean;
}

const GameControls = ({ gameMode, setGameMode, onNewGame, disabled }: GameControlsProps) => {
  const handleModeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setGameMode(e.target.value as GameModeType);
  };

  return (
    <HStack spacing={4} my={4}>
      <Select value={gameMode} onChange={handleModeChange} isDisabled={disabled}>
        <option value="human">Play vs Human</option>
        <option value="stockfish">Play vs Stockfish</option>
      </Select>
      <Button colorScheme="blue" onClick={onNewGame} isDisabled={disabled}>
        New Game
      </Button>
    </HStack>
  );
};

export default GameControls;
