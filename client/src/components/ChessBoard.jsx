import { Chessboard } from 'react-chessboard'
import { Box } from '@chakra-ui/react'

const ChessBoard = ({ position = 'start', onPieceDrop }) => {
  return (
    <Box maxW="600px" w="100%">
      <Chessboard 
        position={position}
        onPieceDrop={onPieceDrop}
        boardWidth={600}
        customBoardStyle={{
          borderRadius: '4px',
          boxShadow: '0 2px 10px rgba(0, 0, 0, 0.5)',
        }}
      />
    </Box>
  )
}

export default ChessBoard
