import { useState, useCallback, useEffect } from "react";
import { Chess, Square } from "chess.js";
import { Button, VStack, Text, useToast } from "@chakra-ui/react";
import ChessBoard from "./ChessBoard";
import { getStockfishMove } from "../services/stockfish.service";
import { getGroqMove, getGroqModels, uciToSquares } from "../services/groq.service";
import { GameModeType, CustomSquareStyles, GroqModel } from "../types";
import ModelSelector from "./ModelSelector";

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
  const [groqModels, setGroqModels] = useState<GroqModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("llama3");
  const toast = useToast();

  // Update the chessboard position when the game changes
  useEffect(() => {
    setPosition(game.fen());
  }, [game]);

  // Fetch available Groq models on component mount
  useEffect(() => {
    if (gameMode === "groq") {
      const fetchModels = async () => {
        try {
          console.log("Requesting Groq models...");
          const result = await getGroqModels();
          console.log("Received models:", result);

          if (result.models && result.models.length > 0) {
            console.log("Setting models:", result.models.map((m) => m.name).join(", "));
            setGroqModels(result.models);
            setSelectedModel(result.default);
          } else {
            console.warn("No models returned");
          }
        } catch (error) {
          console.error("Failed to fetch models:", error);
          toast({
            title: "Error",
            description: "Failed to load AI models",
            status: "error",
            duration: 3000,
            isClosable: true,
          });
        }
      };

      fetchModels();
    }
  }, [gameMode, toast]);

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
        // Pass the move history and selected model for context
        move = await getGroqMove(game.fen(), moveHistory, selectedModel);
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
  }, [game, gameMode, makeMove, moveHistory, selectedModel, toast]);

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

  // Handle model change
  const handleModelChange = (modelKey: string) => {
    console.log(`Changing model to: ${modelKey}`);
    setSelectedModel(modelKey);

    // Find the selected model details
    const selectedModelData = groqModels.find((m) => m.key === modelKey);
    console.log("Selected model details:", selectedModelData);

    toast({
      title: "Model Changed",
      description: `Now playing against ${selectedModelData?.name || modelKey}`,
      status: "info",
      duration: 2000,
      isClosable: true,
    });
  };

  return (
    <div className="chess-container">
      <Text fontSize="2xl" mb={2}>
        Chess Game vs {getOpponentName()}
      </Text>

      {gameMode === "groq" && groqModels.length > 0 && <ModelSelector models={groqModels} selectedModel={selectedModel} onModelChange={handleModelChange} />}

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
