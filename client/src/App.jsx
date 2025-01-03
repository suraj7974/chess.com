import { useState, useRef } from 'react'
import { Container, Flex, Box, Heading } from '@chakra-ui/react'
import { Chess } from 'chess.js'
import ChessBoard from './components/ChessBoard'
import GameControls from './components/GameControls'
import GameInfo from './components/GameInfo'
import './App.css'

function App() {
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
    // Clear previous highlights if clicking on empty square
    if (!square) {
      setPossibleMoves({})
      return
    }

    const moves = {}
    // Get all possible moves for the clicked piece
    const piece = gameRef.current.get(square)
    
    // Only show moves for current player's pieces
    if (piece && piece.color === gameRef.current.turn()) {
      const legalMoves = gameRef.current.moves({
        square,
        verbose: true
      })

      // Highlight source square
      moves[square] = sourceSquareStyle

      // Highlight possible destination squares
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
        promotion: 'q' // always promote to queen for simplicity
      })

      if (move === null) return false // illegal move

      setPosition(gameRef.current.fen())
      setMoveHistory([...moveHistory, move.san])
      setCurrentPlayer(gameRef.current.turn() === 'w' ? 'White' : 'Black')
      setPossibleMoves({}) // Clear possible moves after a move
      return true
    } catch (error) {
      return false
    }
  }

  return (
    <Container maxW="container.xl" py={8}>
     
      <GameControls 
        onModeChange={(e) => setGameMode(e.target.value)}
        onNewGame={handleNewGame}
      />
      <Flex gap={8} direction={{ base: 'column', lg: 'row' }}>
        <Box flex={1}>
          <ChessBoard 
            position={position} 
            onPieceDrop={handlePieceDrop} 
            onPieceClick={handlePieceClick}
            customSquareStyles={possibleMoves}
          />
        </Box>
        <Box w={{ base: '100%', lg: '300px' }}>
          <GameInfo 
            currentPlayer={currentPlayer}
            moveHistory={moveHistory}
          />
        </Box>
      </Flex>
    </Container>
  )
}

export default App
