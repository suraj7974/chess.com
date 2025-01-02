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
  const gameRef = useRef(new Chess())

  const handleNewGame = () => {
    gameRef.current = new Chess()
    setMoveHistory([])
    setCurrentPlayer('White')
    setPosition('start')
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
