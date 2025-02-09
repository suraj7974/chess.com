import { Chessboard } from "react-chessboard";
import { Box } from "@chakra-ui/react";
import { CustomSquareStyles } from "../types";
import { Square } from "chess.js";

interface ChessBoardProps {
  onPieceDrop: (source: Square, target: Square) => boolean;
  position: string;
  onPieceClick: (square: Square) => void;
  customSquareStyles: CustomSquareStyles;
}

function ChessBoard({ onPieceDrop, position, onPieceClick, customSquareStyles }: ChessBoardProps) {
  const customBoardStyle = {
    borderRadius: "4px",
    boxShadow: "0 2px 10px rgba(0, 0, 0, 0.5)",
  };

  const customDarkSquareStyle = { backgroundColor: "#5B793D" };
  const customLightSquareStyle = { backgroundColor: "#eeeeee" };

  const handlePieceClick = (piece: any) => {
    if (piece && piece.square) {
      onPieceClick(piece.square as Square);
    }
  };

  return (
    <Box width="100%" maxW="600px" mx="auto">
      <Chessboard
        position={position}
        onPieceDrop={onPieceDrop}
        onSquareClick={onPieceClick}
        onPieceClick={handlePieceClick}
        customSquareStyles={customSquareStyles}
        boardWidth={600}
        animationDuration={200}
        areArrowsAllowed={false}
        showBoardNotation={true}
        customBoardStyle={customBoardStyle}
        customDarkSquareStyle={customDarkSquareStyle}
        customLightSquareStyle={customLightSquareStyle}
      />
    </Box>
  );
}

export default ChessBoard;
