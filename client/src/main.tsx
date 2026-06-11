import { ChakraProvider, ColorModeScript } from "@chakra-ui/react";
import { createRoot } from "react-dom/client";
import theme from "./theme";
import App from "./App";
import "./index.css";

const container = document.getElementById("root") as HTMLElement;
const root = createRoot(container);

root.render(
  <ChakraProvider resetCSS theme={theme}>
    <ColorModeScript initialColorMode="dark" />
    <App />
  </ChakraProvider>
);
