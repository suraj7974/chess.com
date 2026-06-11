import { useState, useCallback, useEffect, useMemo, useRef } from "react";
import { Chess, Square } from "chess.js";
import {
  Badge,
  Box,
  Button,
  Flex,
  Grid,
  HStack,
  Heading,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Spinner,
  Text,
  VStack,
  useDisclosure,
  useToast,
} from "@chakra-ui/react";
import ChessBoard from "./ChessBoard";
import { getStockfishMove, DIFFICULTY_PRESETS, DifficultyPreset } from "../services/stockfish.service";
import { getGroqMove, getGroqModels, uciToSquares, GroqMoveResult } from "../services/groq.service";
import { GameModeType, CustomSquareStyles, GroqModel } from "../types";
import ModelSelector from "./ModelSelector";

interface ChessGameProps {
  gameMode: GameModeType;
  onRestartGame: () => void;
}

const SELECTED_STYLE = { backgroundColor: "rgba(255, 213, 79, 0.55)" };
const TARGET_STYLE = {
  background: "radial-gradient(circle, rgba(0,0,0,0.25) 22%, transparent 24%)",
};
const CAPTURE_TARGET_STYLE = {
  background: "radial-gradient(circle, transparent 56%, rgba(0,0,0,0.25) 58%)",
};
const LAST_MOVE_STYLE = { backgroundColor: "rgba(155, 199, 0, 0.45)" };

const ChessGame = ({ gameMode, onRestartGame }: ChessGameProps) => {
  const [game, setGame] = useState(() => new Chess());
  const [isPlayerTurn, setIsPlayerTurn] = useState(true);
  const [moveHistory, setMoveHistory] = useState<string[]>([]);
  const [selectedPiece, setSelectedPiece] = useState<Square | null>(null);
  const [moveStyles, setMoveStyles] = useState<CustomSquareStyles>({});
  const [lastMove, setLastMove] = useState<{ from: Square; to: Square } | null>(null);
  const [groqModels, setGroqModels] = useState<GroqModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("llama70b");
  const [difficulty, setDifficulty] = useState<DifficultyPreset>(DIFFICULTY_PRESETS[2]);
  const [lastAiInfo, setLastAiInfo] = useState<GroqMoveResult | null>(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();

  const position = game.fen();
  const isThinking = !isPlayerTurn && gameMode !== "human" && !game.isGameOver();

  // Fetch available Groq models when playing against an LLM
  useEffect(() => {
    if (gameMode !== "groq") return;
    getGroqModels()
      .then((result) => {
        setGroqModels(result.models);
        setSelectedModel(result.default);
      })
      .catch(() => {
        toast({
          title: "Failed to load AI models",
          status: "error",
          duration: 3000,
          isClosable: true,
        });
      });
  }, [gameMode, toast]);

  const customSquareStyles = useMemo<CustomSquareStyles>(() => {
    const styles: CustomSquareStyles = {};
    if (lastMove) {
      styles[lastMove.from] = LAST_MOVE_STYLE;
      styles[lastMove.to] = LAST_MOVE_STYLE;
    }
    return { ...styles, ...moveStyles };
  }, [lastMove, moveStyles]);

  const resetSelection = () => {
    setMoveStyles({});
    setSelectedPiece(null);
  };

  const makeMove = useCallback(
    (from: Square, to: Square, promotion = "q") => {
      try {
        const gameCopy = new Chess(game.fen());
        const moveResult = gameCopy.move({ from, to, promotion });
        if (!moveResult) return false;

        setGame(gameCopy);
        setLastMove({ from, to });
        setMoveHistory((prev) => [...prev, moveResult.san]);
        resetSelection();

        if (gameCopy.isGameOver()) {
          setIsPlayerTurn(true);
          onOpen();
        } else {
          setIsPlayerTurn(gameMode === "human" ? true : gameCopy.turn() === "w");
        }
        return true;
      } catch {
        return false;
      }
    },
    [game, gameMode, onOpen],
  );

  // Ask the engine / model for a move when it's the computer's turn
  useEffect(() => {
    if (isPlayerTurn || gameMode === "human" || game.isGameOver()) return;

    let cancelled = false;
    const fen = game.fen();

    const fetchMove = async () => {
      try {
        let uci: string;
        if (gameMode === "stockfish") {
          uci = await getStockfishMove(fen, difficulty.skillLevel, difficulty.moveTimeMs);
        } else {
          const result = await getGroqMove(fen, moveHistory, selectedModel);
          if (cancelled) return;
          setLastAiInfo(result);
          uci = result.move;
        }
        if (cancelled || !uci) return;

        const { from, to, promotion } = uciToSquares(uci);
        // Short pause so the reply doesn't feel instant
        setTimeout(() => {
          if (!cancelled) makeMove(from, to, promotion ?? "q");
        }, 250);
      } catch (error) {
        console.error(`${gameMode} move error:`, error);
        if (!cancelled) {
          toast({
            title: `Failed to get ${gameMode === "stockfish" ? "Stockfish" : "AI"} move`,
            status: "error",
            duration: 3000,
            isClosable: true,
          });
          setIsPlayerTurn(true);
        }
      }
    };

    fetchMove();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isPlayerTurn, game]);

  const showMovesFor = (square: Square) => {
    const piece = game.get(square);
    if (!piece || piece.color !== game.turn()) return false;

    const styles: CustomSquareStyles = { [square]: SELECTED_STYLE };
    game.moves({ square, verbose: true }).forEach((move) => {
      styles[move.to] = game.get(move.to as Square) ? CAPTURE_TARGET_STYLE : TARGET_STYLE;
    });
    setMoveStyles(styles);
    setSelectedPiece(square);
    return true;
  };

  const onPieceDrop = (sourceSquare: Square, targetSquare: Square) => {
    if (!isPlayerTurn || game.isGameOver()) return false;
    return makeMove(sourceSquare, targetSquare);
  };

  const onPieceClick = (square: Square) => {
    if (!isPlayerTurn || game.isGameOver()) return;

    if (selectedPiece) {
      if (selectedPiece === square) {
        resetSelection();
        return;
      }
      if (makeMove(selectedPiece, square)) return;
    }
    if (!showMovesFor(square)) resetSelection();
  };

  const onPieceDragBegin = (_piece: unknown, sourceSquare: Square) => {
    if (!isPlayerTurn || game.isGameOver()) return;
    showMovesFor(sourceSquare);
  };

  const resetGame = () => {
    setGame(new Chess());
    setIsPlayerTurn(true);
    setMoveHistory([]);
    setLastMove(null);
    setLastAiInfo(null);
    resetSelection();
    onClose();
  };

  const opponentName =
    gameMode === "stockfish"
      ? `Stockfish · ${difficulty.label}`
      : gameMode === "groq"
        ? groqModels.find((m) => m.key === selectedModel)?.name ?? "AI Model"
        : "Pass & Play";

  const statusText = () => {
    if (game.isCheckmate()) return `Checkmate — ${game.turn() === "w" ? "Black" : "White"} wins`;
    if (game.isStalemate()) return "Draw by stalemate";
    if (game.isDraw()) return "Draw";
    if (isThinking) return gameMode === "stockfish" ? "Stockfish is thinking…" : "Model is thinking…";
    const turn = game.turn() === "w" ? "White" : "Black";
    return `${game.isCheck() ? "Check — " : ""}${gameMode === "human" ? `${turn} to move` : "Your turn"}`;
  };

  const movePairs = useMemo(() => {
    const pairs: { n: number; white: string; black?: string }[] = [];
    for (let i = 0; i < moveHistory.length; i += 2) {
      pairs.push({ n: i / 2 + 1, white: moveHistory[i], black: moveHistory[i + 1] });
    }
    return pairs;
  }, [moveHistory]);

  // Keep the latest move visible in the bottom strip without moving the page
  const movesRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    movesRef.current?.scrollTo({ left: movesRef.current.scrollWidth, behavior: "smooth" });
  }, [moveHistory]);

  const aiSourceBadge = () => {
    if (gameMode !== "groq" || !lastAiInfo) return null;
    if (lastAiInfo.source === "groq") {
      return <Badge colorScheme="purple">{lastAiInfo.modelName ?? "LLM"}</Badge>;
    }
    return (
      <Badge colorScheme="orange" title="The model/server was unavailable, a basic heuristic move was played">
        fallback move
      </Badge>
    );
  };

  const panelProps = {
    bg: "surface.800",
    border: "1px solid",
    borderColor: "surface.700",
    borderRadius: "xl",
    p: 4,
  } as const;

  return (
    <Flex direction="column" w="full" h={{ xl: "calc(100vh - 130px)" }} gap={4}>
      <Modal isOpen={isOpen} onClose={onClose} isCentered>
        <ModalOverlay backdropFilter="blur(4px)" />
        <ModalContent bg="surface.800" color="gray.100">
          <ModalHeader>Game over</ModalHeader>
          <ModalBody fontSize="lg">{statusText()}</ModalBody>
          <ModalFooter gap={3}>
            <Button colorScheme="green" onClick={resetGame}>
              Play again
            </Button>
            <Button variant="ghost" onClick={onClose}>
              Review board
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Board stays centered; panels live in the corners on large screens so
          nothing around the board ever changes its position */}
      <Flex flex="1" position="relative" direction="column" align="center" justify="center" gap={4}>
        <Box {...panelProps} position={{ base: "static", xl: "absolute" }} top={0} left={0} w={{ base: "min(92vw, 600px)", xl: "270px" }}>
          <Text fontSize="xs" textTransform="uppercase" letterSpacing="wide" color="gray.500">
            Playing against
          </Text>
          <Heading size="sm" color="gray.50" mt={1} mb={3}>
            {opponentName}
          </Heading>
          <HStack spacing={3} bg="surface.700" borderRadius="lg" px={3} py={2}>
            {isThinking && <Spinner size="sm" color="accent.300" />}
            <Text fontWeight="600" fontSize="sm">
              {statusText()}
            </Text>
            {aiSourceBadge()}
          </HStack>
        </Box>

        <ChessBoard
          position={position}
          onPieceDrop={onPieceDrop}
          onPieceClick={onPieceClick}
          customSquareStyles={customSquareStyles}
          onPieceDragBegin={onPieceDragBegin}
          onPieceDragEnd={resetSelection}
        />

        {(gameMode === "groq" || gameMode === "stockfish") && (
          <Box {...panelProps} position={{ base: "static", xl: "absolute" }} top={0} right={0} w={{ base: "min(92vw, 600px)", xl: "270px" }}>
            {gameMode === "groq" && groqModels.length > 0 && (
              <ModelSelector models={groqModels} selectedModel={selectedModel} onModelChange={setSelectedModel} />
            )}
            {gameMode === "stockfish" && (
              <VStack align="stretch" spacing={2}>
                <Text fontSize="xs" textTransform="uppercase" letterSpacing="wide" color="gray.500">
                  Difficulty
                </Text>
                <Grid templateColumns="repeat(2, 1fr)" gap={2}>
                  {DIFFICULTY_PRESETS.map((preset) => (
                    <Button
                      key={preset.key}
                      size="sm"
                      variant={difficulty.key === preset.key ? "solid" : "outline"}
                      colorScheme={difficulty.key === preset.key ? "green" : "gray"}
                      onClick={() => setDifficulty(preset)}
                      title={preset.description}
                    >
                      {preset.label}
                    </Button>
                  ))}
                </Grid>
              </VStack>
            )}
          </Box>
        )}

        <VStack
          {...panelProps}
          position={{ base: "static", xl: "absolute" }}
          bottom={0}
          right={0}
          w={{ base: "min(92vw, 600px)", xl: "270px" }}
          align="stretch"
          spacing={2}
        >
          <Button colorScheme="green" size="sm" onClick={resetGame}>
            New game
          </Button>
          <Button variant="outline" colorScheme="gray" size="sm" onClick={onRestartGame}>
            Change opponent
          </Button>
        </VStack>
      </Flex>

      {/* Fixed-height move strip — the page never grows or scrolls as moves
          are added; the strip scrolls horizontally instead */}
      <Flex h="56px" flexShrink={0} align="center" gap={4} px={4} w={{ base: "min(92vw, 600px)", xl: "full" }} mx="auto" {...panelProps} py={0}>
        <Text fontSize="xs" textTransform="uppercase" letterSpacing="wide" color="gray.500" flexShrink={0}>
          Moves
        </Text>
        <Box ref={movesRef} flex="1" overflowX="auto" whiteSpace="nowrap" fontFamily="mono" fontSize="sm" py={2}>
          {movePairs.length === 0 ? (
            <Text as="span" color="gray.600">
              No moves yet
            </Text>
          ) : (
            movePairs.map((pair) => (
              <Text as="span" key={pair.n} mr={4}>
                <Text as="span" color="gray.600">
                  {pair.n}.
                </Text>{" "}
                <Text as="span" color="gray.200">
                  {pair.white}
                </Text>{" "}
                <Text as="span" color="gray.400">
                  {pair.black ?? ""}
                </Text>
              </Text>
            ))
          )}
        </Box>
      </Flex>
    </Flex>
  );
};

export default ChessGame;
