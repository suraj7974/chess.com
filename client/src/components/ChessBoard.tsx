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
  return (
    <Box
      w={{ base: "min(92vw, 600px)", xl: "min(700px, calc(100vh - 250px), calc(100vw - 620px))" }}
      mx="auto"
      borderRadius="xl"
      overflow="hidden"
      boxShadow="0 10px 40px -10px rgba(0, 0, 0, 0.7)"
    >
      <Chessboard
        position={position}
        onPieceDrop={onPieceDrop}
        onSquareClick={onPieceClick}
        customSquareStyles={customSquareStyles}
        animationDuration={200}
        areArrowsAllowed={false}
        showBoardNotation={true}
        customBoardStyle={{ width: "100%" }}
        customDarkSquareStyle={{ backgroundColor: "#769656" }}
        customLightSquareStyle={{ backgroundColor: "#eeeed2" }}
        onPieceDragBegin={onPieceDragBegin}
        onPieceDragEnd={onPieceDragEnd}
      />
    </Box>
  );
}

export default ChessBoard;
