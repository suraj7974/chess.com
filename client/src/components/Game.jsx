import { useState, useRef } from 'react'
import { Container, Flex, Box } from '@chakra-ui/react'
import { Chess } from 'chess.js'
import ChessBoard from './ChessBoard'
import GameControls from './GameControls'
import GameInfo from './GameInfo'

function Game() {
  const [gameMode, setGameMode] = useState('human')
  const [currentPlayer, setCurrentPlayer] = useState('White')
  const [moveHistory, setMoveHistory] = useState([])
  const [position, setPosition] = useState('start')
  const [possibleMoves, setPossibleMoves] = useState({})
  const gameRef = useRef(new Chess())

  const highlightSquare = {
    background: 'radial-gradient(circle, rgba(0,0,0,.4) 25%, transparent 25%)',
    borderRadius: '50%',
  }

  const sourceSquareStyle = {
    background: 'rgba(255, 165, 0, 0.4)',
  }

  const handleNewGame = () => {
    gameRef.current = new Chess()
    setMoveHistory([])
    setCurrentPlayer('White')
    setPosition('start')
  }

  const handlePieceClick = (square) => {
    if (!square) {
      setPossibleMoves({})
      return
    }

    const moves = {}
    const piece = gameRef.current.get(square)
    
    if (piece && piece.color === gameRef.current.turn()) {
      const legalMoves = gameRef.current.moves({
        square,
        verbose: true
      })

      moves[square] = sourceSquareStyle
      legalMoves.forEach(move => {
        moves[move.to] = highlightSquare
      })

      setPossibleMoves(moves)
    } else {
      setPossibleMoves({})
    }
  }

  const handlePieceDrop = (sourceSquare, targetSquare) => {
    try {
      const move = gameRef.current.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: 'q'
      })

      if (move === null) return false

      setPosition(gameRef.current.fen())
      setMoveHistory([...moveHistory, move.san])
      setCurrentPlayer(gameRef.current.turn() === 'w' ? 'White' : 'Black')
      setPossibleMoves({})
      return true
    } catch (error) {
      return false
    }
  }

  return (
    <Container maxW="container.xl" py={8}>
      {/* <GameControls 
        onModeChange={(e) => setGameMode(e.target.value)}
        onNewGame={handleNewGame}
      /> */}
      <Flex gap={8} direction={{ base: 'column', lg: 'row' }}>
        <Box flex={1}>
          <ChessBoard 
            position={position} 
            onPieceDrop={handlePieceDrop} 
            onPieceClick={handlePieceClick}
            customSquareStyles={possibleMoves}
          />
        </Box>
        {/* <Box w={{ base: '100%', lg: '300px' }}>
          <GameInfo 
            currentPlayer={currentPlayer}
            moveHistory={moveHistory}
          />
        </Box> */}
      </Flex>
    </Container>
  )
}

export default Game
