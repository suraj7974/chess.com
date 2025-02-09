import { Chessboard } from "react-chessboard";
import { Box } from "@chakra-ui/react";
import { CustomSquareStyles } from "../types";
import { Square } from "chess.js";
import { Piece } from "react-chessboard/dist/chessboard/types";

interface ChessBoardProps {
  onPieceDrop: (source: Square, target: Square) => boolean;
  position: string;
  onPieceClick: (square: Square) => void;
  customSquareStyles: CustomSquareStyles;
  onPieceDragBegin: (piece: Piece, sourceSquare: Square) => void;
  onPieceDragEnd: () => void;
}

function ChessBoard({ onPieceDrop, position, onPieceClick, customSquareStyles, onPieceDragBegin, onPieceDragEnd }: ChessBoardProps) {
  const customBoardStyle = {
    borderRadius: "4px",
    boxShadow: "0 2px 10px rgba(0, 0, 0, 0.5)",
  };

  const customDarkSquareStyle = { backgroundColor: "#5B793D" };
  const customLightSquareStyle = { backgroundColor: "#eeeeee" };

  const handleSquareClick = (square: Square) => {
    onPieceClick(square);
  };

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
        onSquareClick={handleSquareClick}
        onPieceClick={handlePieceClick}
        customSquareStyles={customSquareStyles}
        boardWidth={600}
        animationDuration={200}
        areArrowsAllowed={false}
        showBoardNotation={true}
        customBoardStyle={customBoardStyle}
        customDarkSquareStyle={customDarkSquareStyle}
        customLightSquareStyle={customLightSquareStyle}
        onPieceDragBegin={onPieceDragBegin}
        onPieceDragEnd={onPieceDragEnd}
      />
    </Box>
  );
}

export default ChessBoard;
