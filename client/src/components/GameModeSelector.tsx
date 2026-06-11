import { Box, Heading, SimpleGrid, Text, VStack } from "@chakra-ui/react";
import { GameModeType } from "../types";

interface GameModeSelectorProps {
  onSelect: (mode: GameModeType) => void;
}

interface ModeCard {
  mode: GameModeType;
  title: string;
  description: string;
  accent: string;
}

const MODES: ModeCard[] = [
  {
    mode: "stockfish",
    title: "Stockfish",
    description: "The world's strongest chess engine, running right in your browser. Pick a difficulty from casual to brutal.",
    accent: "#769656",
  },
  {
    mode: "groq",
    title: "AI Models",
    description: "Challenge large language models like LLaMA 3.3 and GPT-OSS. Watch how an LLM actually plays chess.",
    accent: "#9f7aea",
  },
  {
    mode: "human",
    title: "Pass & Play",
    description: "Two players, one board. Play a friendly game with someone next to you.",
    accent: "#4299e1",
  },
];

const GameModeSelector = ({ onSelect }: GameModeSelectorProps) => {
  return (
    <VStack spacing={{ base: 8, md: 12 }} maxW="5xl" w="full">
      <VStack spacing={3} textAlign="center">
        <Heading size={{ base: "xl", md: "2xl" }} color="gray.50" letterSpacing="tight">
          Choose your opponent
        </Heading>
        <Text color="gray.400" fontSize={{ base: "md", md: "lg" }} maxW="lg">
          Play against the strongest engine ever built, a large language model, or a friend.
        </Text>
      </VStack>

      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={6} w="full">
        {MODES.map((card) => (
          <Box
            key={card.mode}
            as="button"
            onClick={() => onSelect(card.mode)}
            bg="surface.800"
            border="1px solid"
            borderColor="surface.700"
            borderRadius="2xl"
            p={8}
            textAlign="left"
            display="flex"
            alignItems="flex-start"
            transition="border-color 0.2s ease, box-shadow 0.2s ease"
            _hover={{
              borderColor: card.accent,
              boxShadow: `0 8px 30px -10px ${card.accent}66`,
            }}
          >
            <VStack align="flex-start" spacing={4}>
              <Box w="36px" h="4px" borderRadius="full" bg={card.accent} />
              <Heading size="md" color="gray.50">
                {card.title}
              </Heading>
              <Text color="gray.400" fontSize="sm" lineHeight="1.6">
                {card.description}
              </Text>
              <Text color={card.accent} fontWeight="600" fontSize="sm">
                Play now →
              </Text>
            </VStack>
          </Box>
        ))}
      </SimpleGrid>
    </VStack>
  );
};

export default GameModeSelector;
