import { useState, useCallback, useEffect } from "react";
import { Chess, Square } from "chess.js";
import { Button, VStack, Text, useToast } from "@chakra-ui/react";
import ChessBoard from "./ChessBoard";
import { getStockfishMove } from "../services/stockfish.service";
import { getGroqMove, uciToSquares } from "../services/groq.service";
import { GameModeType, CustomSquareStyles } from "../types";

interface ChessGameProps {
  gameMode: GameModeType;
  onRestartGame: () => void;
}

const ChessGame = ({ gameMode, onRestartGame }: ChessGameProps) => {
  const [game, setGame] = useState(new Chess());
  const [position, setPosition] = useState(game.fen());
  const [isPlayerTurn, setIsPlayerTurn] = useState(true);
  const [moveHistory, setMoveHistory] = useState<string[]>([]);
  const [selectedPiece, setSelectedPiece] = useState<Square | null>(null);
  const [customSquareStyles, setCustomSquareStyles] = useState<CustomSquareStyles>({});
  const toast = useToast();

  // Update the chessboard position when the game changes
  useEffect(() => {
    setPosition(game.fen());
  }, [game]);

  // Reset styles when starting a new move
  const resetStyles = () => {
    setCustomSquareStyles({});
    setSelectedPiece(null);
  };

  // Make a move
  const makeMove = useCallback(
    (from: Square, to: Square) => {
      try {
        const gameCopy = new Chess(game.fen());
        const moveResult = gameCopy.move({ from, to, promotion: "q" });

        if (moveResult) {
          // Update game state
          setGame(gameCopy);
          setPosition(gameCopy.fen());
          setIsPlayerTurn(false);

          // Update move history
          const newMove = `${moveResult.san}`;
          setMoveHistory((prev) => [...prev, newMove]);
          resetStyles();
          return true;
        }
        return false;
      } catch (error) {
        console.error("Move error:", error);
        return false;
      }
    },
    [game]
  );

  // Handle computer move based on game mode
  const handleComputerMove = useCallback(async () => {
    try {
      let move: string;

      if (gameMode === "stockfish") {
        move = await getStockfishMove(game.fen());
      } else if (gameMode === "groq") {
        // Pass the move history for context
        move = await getGroqMove(game.fen(), moveHistory);
      } else {
        // This is for human vs human mode
        setIsPlayerTurn(true);
        return;
      }

      const { from, to } = uciToSquares(move);

      // Highlight the computer's move
      setCustomSquareStyles({
        [from]: { backgroundColor: "rgba(255, 255, 0, 0.4)" },
        [to]: { backgroundColor: "rgba(255, 255, 0, 0.4)" },
      });

      // Make the move after a small delay to show the highlights
      setTimeout(() => {
        makeMove(from, to);
        setIsPlayerTurn(true);
        resetStyles();
      }, 500);
    } catch (error) {
      console.error(`${gameMode} move error:`, error);
      toast({
        title: "Error",
        description: `Failed to get ${gameMode} move. Please try again.`,
        status: "error",
        duration: 3000,
        isClosable: true,
      });
      setIsPlayerTurn(true);
    }
  }, [game, gameMode, makeMove, moveHistory, toast]);

  // Get computer move when it's their turn
  useEffect(() => {
    if (!isPlayerTurn && !game.isGameOver()) {
      handleComputerMove();
    }
  }, [isPlayerTurn, game, handleComputerMove]);

  // Handle piece drop (for drag and drop)
  const onPieceDrop = (sourceSquare: Square, targetSquare: Square) => {
    if (!isPlayerTurn || game.isGameOver()) return false;
    return makeMove(sourceSquare, targetSquare);
  };

  // Handle piece click (for click-to-move)
  const onPieceClick = (square: Square) => {
    if (!isPlayerTurn || game.isGameOver()) return;

    // If a piece is already selected
    if (selectedPiece) {
      // If the same square is clicked again, deselect it
      if (selectedPiece === square) {
        setSelectedPiece(null);
        setCustomSquareStyles({});
      } else {
        // Try to make a move
        const moveSuccess = makeMove(selectedPiece, square);

        if (!moveSuccess) {
          // If the move failed, select the new square if it has a piece
          const piece = game.get(square);
          if (piece && piece.color === (game.turn() === "w" ? "w" : "b")) {
            setSelectedPiece(square);

            // Highlight the selected square and valid moves
            const newStyles: CustomSquareStyles = {
              [square]: { backgroundColor: "rgba(255, 0, 0, 0.4)" },
            };

            // Highlight valid move targets
            game.moves({ square, verbose: true }).forEach((move) => {
              newStyles[move.to] = { backgroundColor: "rgba(0, 255, 0, 0.4)" };
            });

            setCustomSquareStyles(newStyles);
          } else {
            resetStyles();
          }
        }
      }
    } else {
      // No piece selected yet
      const piece = game.get(square);

      // Only select piece of current player's color
      if (piece && piece.color === (game.turn() === "w" ? "w" : "b")) {
        setSelectedPiece(square);

        // Highlight the selected square and valid moves
        const newStyles: CustomSquareStyles = {
          [square]: { backgroundColor: "rgba(255, 0, 0, 0.4)" },
        };

        // Highlight valid move targets
        game.moves({ square, verbose: true }).forEach((move) => {
          newStyles[move.to] = { backgroundColor: "rgba(0, 255, 0, 0.4)" };
        });

        setCustomSquareStyles(newStyles);
      }
    }
  };

  // Handle piece drag begin
  const onPieceDragBegin = (piece: any, sourceSquare: Square) => {
    if (!isPlayerTurn || game.isGameOver()) return;

    // Highlight valid move targets
    const newStyles: CustomSquareStyles = {};
    game.moves({ square: sourceSquare, verbose: true }).forEach((move) => {
      newStyles[move.to] = { backgroundColor: "rgba(0, 255, 0, 0.4)" };
    });

    setCustomSquareStyles(newStyles);
  };

  // Handle piece drag end
  const onPieceDragEnd = () => {
    resetStyles();
  };

  // Reset the game
  const resetGame = () => {
    const newGame = new Chess();
    setGame(newGame);
    setPosition(newGame.fen());
    setIsPlayerTurn(true);
    setMoveHistory([]);
    resetStyles();
  };

  // Get game status text
  const getGameStatus = () => {
    if (game.isCheckmate()) return "Checkmate!";
    if (game.isDraw()) return "Draw!";
    if (game.isStalemate()) return "Stalemate!";
    if (game.isCheck()) return "Check!";

    if (isPlayerTurn) {
      return "Your turn";
    } else {
      return gameMode === "stockfish" ? "Stockfish thinking..." : "Mistral AI thinking...";
    }
  };

  // Get opposing player name
  const getOpponentName = () => {
    if (gameMode === "stockfish") return "Stockfish";
    if (gameMode === "groq") return "Mistral AI";
    return "Human";
  };

  return (
    <div className="chess-container">
      <Text fontSize="2xl" mb={2}>
        Chess Game vs {getOpponentName()}
      </Text>

      <div className="chessboard-wrapper">
        <ChessBoard
          position={position}
          onPieceDrop={onPieceDrop}
          onPieceClick={onPieceClick}
          customSquareStyles={customSquareStyles}
          onPieceDragBegin={onPieceDragBegin}
          onPieceDragEnd={onPieceDragEnd}
        />
      </div>

      <VStack spacing={3} className="controls">
        <Text fontSize="xl" fontWeight="bold">
          {getGameStatus()}
        </Text>

        <Button colorScheme="blue" onClick={resetGame} width="full" maxW="200px">
          New Game
        </Button>

        <Button colorScheme="gray" onClick={onRestartGame} width="full" maxW="200px">
          Change Opponent
        </Button>
      </VStack>
    </div>
  );
};

export default ChessGame;
