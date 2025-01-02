import { Chessboard } from 'react-chessboard'
import { Box } from '@chakra-ui/react'

function ChessBoard({ onPieceDrop, position }) {
  return (
    <Box width="100%" maxW="600px" mx="auto">
      <Chessboard 
        position={position}
        onPieceDrop={onPieceDrop}
        boardWidth={600}
        animationDuration={200}
      />
    </Box>
  )
}

export default ChessBoard
