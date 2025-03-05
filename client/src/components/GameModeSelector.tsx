import { Button, VStack, Heading, Box, useColorModeValue } from "@chakra-ui/react";
import { GameModeType } from "../types";

interface GameModeSelectorProps {
  onSelect: (mode: GameModeType) => void;
}

const GameModeSelector = ({ onSelect }: GameModeSelectorProps) => {
  const bgColor = useColorModeValue("gray.100", "gray.700");

  return (
    <Box p={6} borderRadius="md" bg={bgColor} width="100%" maxW="400px" boxShadow="md">
      <VStack spacing={5}>
        <Heading size="lg">Choose Your Opponent</Heading>

        <Button colorScheme="blue" size="lg" width="full" onClick={() => onSelect("stockfish")}>
          Play against Stockfish
        </Button>

        <Button colorScheme="purple" size="lg" width="full" onClick={() => onSelect("groq")}>
          Play against Mistral (AI)
        </Button>

        <Button colorScheme="green" size="lg" width="full" onClick={() => onSelect("human")}>
          Play against Human
        </Button>
      </VStack>
    </Box>
  );
};

export default GameModeSelector;
