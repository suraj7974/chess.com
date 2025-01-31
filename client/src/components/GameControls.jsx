import { Button, HStack, Select } from '@chakra-ui/react'

const GameControls = ({ gameMode, setGameMode, onNewGame, disabled }) => {
  const handleModeChange = (e) => {
    console.log('Mode changed to:', e.target.value);
    setGameMode(e.target.value);
  };

  return (
    <HStack spacing={4} my={4}>
      <Select 
        value={gameMode}
        onChange={handleModeChange}
        isDisabled={disabled}
      >
        <option value="human">Play vs Human</option>
        <option value="stockfish">Play vs Stockfish</option>
      </Select>
      <Button 
        colorScheme="blue" 
        onClick={onNewGame}
        isDisabled={disabled}
      >
        New Game
      </Button>
    </HStack>
  )
}

export default GameControls
