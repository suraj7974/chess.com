import { Chessboard } from 'react-chessboard'
import { Box } from '@chakra-ui/react'

function ChessBoard({ onPieceDrop, position, onPieceClick, customSquareStyles }) {
  return (
    <Box width="100%" maxW="600px" mx="auto">
      <Chessboard 
        position={position}
        onPieceDrop={onPieceDrop}
        onSquareClick={onPieceClick}
        onPieceClick={onPieceClick}
        customSquareStyles={customSquareStyles}
        boardWidth={600}
        animationDuration={200}
        areArrowsAllowed={false}
        showBoardNotation={true}
      />
    </Box>
  )
}

export default ChessBoard
