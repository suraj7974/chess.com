import { Box, Button, VStack, Heading } from "@chakra-ui/react";
import { Link } from "react-router-dom";

function Home(): JSX.Element {
  return (
    <Box height="100vh" display="flex" alignItems="center" justifyContent="center">
      <VStack spacing={8}>
        <Heading size="2xl">Chess Game</Heading>
        <Link to="/play">
          <Button colorScheme="blue" size="lg">
            Start Playing
          </Button>
        </Link>
      </VStack>
    </Box>
  );
}

export default Home;
