import { Box, Text, VStack } from "@chakra-ui/react";
import { PlayerColor } from "../types";

interface GameInfoProps {
  currentPlayer: PlayerColor;
  moveHistory: string[];
  isThinking?: boolean;
}

const GameInfo = ({ currentPlayer, moveHistory, isThinking }: GameInfoProps) => {
  return (
    <VStack align="start" spacing={4} p={4} bg="gray.50" borderRadius="md">
      <Text fontSize="lg" fontWeight="bold">
        Current Turn: {currentPlayer}
      </Text>
      <Box>
        <Text fontWeight="bold">Move History:</Text>
        <Box maxH="200px" overflowY="auto">
          {moveHistory.map((move, index) => (
            <Text key={index}>{`${index + 1}. ${move}`}</Text>
          ))}
        </Box>
      </Box>
    </VStack>
  );
};

export default GameInfo;
