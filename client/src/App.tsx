import { useState } from "react";
import { Box, Flex, Heading, Text } from "@chakra-ui/react";
import ChessGame from "./components/ChessGame";
import GameModeSelector from "./components/GameModeSelector";
import { GameModeType } from "./types";
import "./App.css";

function App() {
  const [gameMode, setGameMode] = useState<GameModeType | null>(null);

  return (
    <Flex direction="column" minH="100vh" bg="surface.900">
      <Flex
        as="header"
        align="center"
        px={{ base: 4, md: 8 }}
        py={3}
        borderBottom="1px solid"
        borderColor="surface.700"
        cursor="pointer"
        onClick={() => setGameMode(null)}
      >
        <Heading size="md" letterSpacing="tight" color="gray.50">
          <Text as="span" color="accent.300" mr={2}>
            ♞
          </Text>
          chessss<Text as="span" color="accent.300">.com</Text>
        </Heading>
      </Flex>

      <Box as="main" flex="1" display="flex" alignItems="center" justifyContent="center" px={4} py={{ base: 4, md: 8 }}>
        {gameMode ? (
          <ChessGame gameMode={gameMode} onRestartGame={() => setGameMode(null)} />
        ) : (
          <GameModeSelector onSelect={setGameMode} />
        )}
      </Box>
    </Flex>
  );
}

export default App;
