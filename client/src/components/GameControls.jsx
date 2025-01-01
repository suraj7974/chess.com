import { Button, HStack, Select } from '@chakra-ui/react'

const GameControls = ({ onModeChange, onNewGame }) => {
  return (
    <HStack spacing={4} my={4}>
      <Select placeholder="Select opponent" onChange={onModeChange}>
        <option value="llm">Play vs LLM</option>
        <option value="stockfish">Play vs Stockfish</option>
        <option value="human">Play vs Human</option>
      </Select>
      <Button colorScheme="blue" onClick={onNewGame}>
        New Game
      </Button>
    </HStack>
  )
}

export default GameControls
