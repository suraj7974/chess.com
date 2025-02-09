import { useState, useRef, useEffect } from "react";
import { Chess, Square } from "chess.js";
import { Container, Flex, Box, Modal, ModalOverlay, ModalContent, ModalHeader, ModalBody, ModalFooter, Button, useDisclosure } from "@chakra-ui/react";
import { GameModeType, PlayerColor, CustomSquareStyles } from "../types";
import ChessBoard from "./ChessBoard";
import GameControls from "./GameControls";
import GameInfo from "./GameInfo";
import { getStockfishMove } from "../services/stockfish.service";
import { Piece } from "react-chessboard/dist/chessboard/types";

function Game() {
  const [gameMode, setGameMode] = useState<GameModeType>("human");
  const [currentPlayer, setCurrentPlayer] = useState<PlayerColor>("White");
  const [moveHistory, setMoveHistory] = useState<string[]>([]);
  const [position, setPosition] = useState("start");
  const [possibleMoves, setPossibleMoves] = useState<CustomSquareStyles>({});
  const [gameStatus, setGameStatus] = useState<string | null>(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const gameRef = useRef<Chess>(new Chess());
  const [isThinking, setIsThinking] = useState(false);
  const [selectedSquare, setSelectedSquare] = useState<Square | null>(null);

  const highlightSquare = {
    background: "radial-gradient(circle, rgba(0,0,0,.4) 25%, transparent 25%)",
    borderRadius: "50%",
  };

  const sourceSquareStyle = {
    background: "rgba(255, 165, 0, 0.4)",
  };

  const checkGameStatus = () => {
    if (gameRef.current.isCheckmate()) {
      const winner = gameRef.current.turn() === "w" ? "Black" : "White";
      setGameStatus(`Checkmate! ${winner} wins!`);
      onOpen();
    } else if (gameRef.current.isStalemate()) {
      setGameStatus("Game drawn by stalemate");
      onOpen();
    } else if (gameRef.current.isInsufficientMaterial()) {
      setGameStatus("Game drawn by insufficient material");
      onOpen();
    } else if (gameRef.current.isDraw()) {
      setGameStatus("Game drawn");
      onOpen();
    }
  };

  const handleNewGame = () => {
    gameRef.current = new Chess();
    setMoveHistory([]);
    setCurrentPlayer("White");
    setPosition("start");
    setGameStatus(null);
  };

  const handleNewGameAndClose = () => {
    handleNewGame();
    onClose();
  };

  const handlePieceClick = (square: Square) => {
    // If clicking the same square that was already selected, clear the selection
    if (selectedSquare === square) {
      setSelectedSquare(null);
      setPossibleMoves({});
      return;
    }

    // If a different square was previously selected, try to make a move
    if (selectedSquare) {
      const moveSuccess = handlePieceDrop(selectedSquare, square);
      setSelectedSquare(null);
      if (moveSuccess) {
        setPossibleMoves({});
        return;
      }
    }

    if (!square) {
      setPossibleMoves({});
      setSelectedSquare(null);
      return;
    }

    const moves: CustomSquareStyles = {};
    const piece = gameRef.current.get(square);

    if (piece && piece.color === gameRef.current.turn()) {
      const legalMoves = gameRef.current.moves({
        square,
        verbose: true,
      });

      moves[square] = sourceSquareStyle;
      legalMoves.forEach((move) => {
        moves[move.to] = highlightSquare;
      });

      setPossibleMoves(moves);
      setSelectedSquare(square);
    } else {
      setPossibleMoves({});
      setSelectedSquare(null);
    }
  };

  // Add effect to handle mode changes
  useEffect(() => {
    console.log("Game mode changed:", gameMode);
    if (gameMode === "stockfish") {
      handleNewGame();
    }
  }, [gameMode]);

  const makeComputerMove = async () => {
    console.log("makeComputerMove called:", {
      gameMode,
      gameStatus,
      isThinking,
      currentPlayer,
      position: gameRef.current.fen(),
    });

    if (gameMode !== "stockfish" || gameStatus || isThinking) {
      console.log("Skipping computer move");
      return;
    }

    try {
      setIsThinking(true);
      const fen = gameRef.current.fen();
      console.log("Requesting move for position:", fen);

      const move = await getStockfishMove(fen);
      console.log("Received move from Stockfish:", move);

      if (move) {
        const result = gameRef.current.move({
          from: move.substring(0, 2),
          to: move.substring(2, 4),
          promotion: move.length === 5 ? move[4] : undefined,
        });

        console.log("Move result:", result);

        if (result) {
          const newPosition = gameRef.current.fen();
          console.log("New position:", newPosition);
          setPosition(newPosition);
          setMoveHistory((prev) => [...prev, result.san]);
          setCurrentPlayer(gameRef.current.turn() === "w" ? "White" : "Black");
          checkGameStatus();
        }
      }
    } catch (error) {
      console.error("Stockfish move error:", error);
    } finally {
      setIsThinking(false);
    }
  };

  const handlePieceDrop = (sourceSquare: Square, targetSquare: Square) => {
    console.log("Piece drop:", {
      sourceSquare,
      targetSquare,
      gameMode,
      isThinking,
      turn: gameRef.current.turn(),
    });

    if (isThinking) return false;

    if (gameMode === "stockfish" && gameRef.current.turn() !== "w") {
      console.log("Not player turn in stockfish mode");
      return false;
    }

    try {
      const move = gameRef.current.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: "q",
      });

      if (move === null) return false;

      console.log("Human move made:", move);
      setPosition(gameRef.current.fen());
      setMoveHistory((prev) => [...prev, move.san]);
      setCurrentPlayer(gameRef.current.turn() === "w" ? "White" : "Black");
      setPossibleMoves({});
      checkGameStatus();

      // Trigger computer move after a short delay
      if (gameMode === "stockfish" && !gameStatus) {
        console.log("Scheduling computer move");
        setTimeout(makeComputerMove, 500);
      }

      return true;
    } catch (error) {
      console.error("Move error:", error);
      return false;
    }
  };

  const showPossibleMoves = (square: Square) => {
    const moves: CustomSquareStyles = {};
    const piece = gameRef.current.get(square);

    if (piece && piece.color === gameRef.current.turn()) {
      const legalMoves = gameRef.current.moves({
        square,
        verbose: true,
      });

      moves[square] = sourceSquareStyle;
      legalMoves.forEach((move) => {
        moves[move.to] = highlightSquare;
      });
    }

    setPossibleMoves(moves);
  };

  const handlePieceDragBegin = (piece: Piece, sourceSquare: Square) => {
    showPossibleMoves(sourceSquare);
  };

  const handlePieceDragEnd = () => {
    setPossibleMoves({});
  };

  return (
    <Container maxW="container.xl" py={8}>
      <Modal isOpen={isOpen} onClose={onClose} isCentered>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Game Over</ModalHeader>
          <ModalBody>{gameStatus}</ModalBody>
          <ModalFooter>
            <Button colorScheme="blue" mr={3} onClick={handleNewGameAndClose}>
              New Game
            </Button>
            <Button variant="ghost" onClick={onClose}>
              Close
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      <Flex gap={8} direction={{ base: "column", lg: "row" }}>
        <Box flex={1}>
          <GameControls gameMode={gameMode} setGameMode={setGameMode} onNewGame={handleNewGame} disabled={isThinking} />
          <ChessBoard
            position={position}
            onPieceDrop={handlePieceDrop}
            onPieceClick={handlePieceClick}
            customSquareStyles={possibleMoves}
            onPieceDragBegin={handlePieceDragBegin}
            onPieceDragEnd={handlePieceDragEnd}
          />
        </Box>
        <Box>
          <GameInfo currentPlayer={currentPlayer} moveHistory={moveHistory} isThinking={isThinking} />
        </Box>
      </Flex>
    </Container>
  );
}

export default Game;
