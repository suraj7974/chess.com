import { useState, useRef } from 'react'
import { 
  Container, 
  Flex, 
  Box, 
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Button,
  useDisclosure
} from '@chakra-ui/react'
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
  const [gameStatus, setGameStatus] = useState(null)
  const { isOpen, onOpen, onClose } = useDisclosure()
  const gameRef = useRef(new Chess())

  const highlightSquare = {
    background: 'radial-gradient(circle, rgba(0,0,0,.4) 25%, transparent 25%)',
    borderRadius: '50%',
  }

  const sourceSquareStyle = {
    background: 'rgba(255, 165, 0, 0.4)',
  }

  const checkGameStatus = () => {
    if (gameRef.current.isCheckmate()) {
      const winner = gameRef.current.turn() === 'w' ? 'Black' : 'White'
      setGameStatus(`Checkmate! ${winner} wins!`)
      onOpen()
    } else if (gameRef.current.isStalemate()) {
      setGameStatus('Game drawn by stalemate')
      onOpen()
    } else if (gameRef.current.isInsufficientMaterial()) {
      setGameStatus('Game drawn by insufficient material')
      onOpen()
    } else if (gameRef.current.isDraw()) {
      setGameStatus('Game drawn')
      onOpen()
    }
  }

  const handleNewGame = () => {
    gameRef.current = new Chess()
    setMoveHistory([])
    setCurrentPlayer('White')
    setPosition('start')
    setGameStatus(null)
  }

  const handleNewGameAndClose = () => {
    handleNewGame()
    onClose()
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
      checkGameStatus()
      return true
    } catch (error) {
      return false
    }
  }

  return (
    <Container maxW="container.xl" py={8}>
      <Modal isOpen={isOpen} onClose={onClose} isCentered>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Game Over</ModalHeader>
          <ModalBody>
            {gameStatus}
          </ModalBody>
          <ModalFooter>
            <Button colorScheme="blue" mr={3} onClick={handleNewGameAndClose}>
              New Game
            </Button>
            <Button variant="ghost" onClick={onClose}>
              Close
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      <Flex gap={8} direction={{ base: 'column', lg: 'row' }}>
        <Box flex={1}>
          <ChessBoard 
            position={position} 
            onPieceDrop={handlePieceDrop} 
            onPieceClick={handlePieceClick}
            customSquareStyles={possibleMoves}
          />
        </Box>
      </Flex>
    </Container>
  )
}

export default Game
