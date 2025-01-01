import { useState } from 'react'
import { Container, Flex, Box, Heading } from '@chakra-ui/react'
import ChessBoard from './components/ChessBoard'
import GameControls from './components/GameControls'
import GameInfo from './components/GameInfo'
import './App.css'

function App() {
  const [gameMode, setGameMode] = useState('human')
  const [currentPlayer, setCurrentPlayer] = useState('White')
  const [moveHistory, setMoveHistory] = useState([])

  const handleNewGame = () => {
    setMoveHistory([])
    setCurrentPlayer('White')
  }

  const handlePieceDrop = (sourceSquare, targetSquare) => {
    // Chess logic will be implemented later
    setMoveHistory([...moveHistory, `${sourceSquare} to ${targetSquare}`])
    setCurrentPlayer(currentPlayer === 'White' ? 'Black' : 'White')
    return true
  }

  return (
    <Container maxW="container.xl" py={8}>
      <Heading as="h1" mb={8} textAlign="center">
        Now play chess with llms 
      </Heading>
      <GameControls 
        onModeChange={(e) => setGameMode(e.target.value)}
        onNewGame={handleNewGame}
      />
      <Flex gap={8} direction={{ base: 'column', lg: 'row' }}>
        <Box flex={1}>
          <ChessBoard onPieceDrop={handlePieceDrop} />
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
