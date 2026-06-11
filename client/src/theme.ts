import { extendTheme, type ThemeConfig } from "@chakra-ui/react";

const config: ThemeConfig = {
  initialColorMode: "dark",
  useSystemColorMode: false,
};

export default extendTheme({
  config,
  fonts: {
    heading: `'Inter', system-ui, -apple-system, sans-serif`,
    body: `'Inter', system-ui, -apple-system, sans-serif`,
  },
  colors: {
    board: {
      light: "#eeeed2",
      dark: "#769656",
    },
    surface: {
      900: "#161512",
      800: "#1f1e1b",
      700: "#2a2926",
      600: "#3d3b37",
    },
    accent: {
      300: "#a3d160",
      400: "#8bbf3f",
      500: "#769656",
      600: "#5d7a43",
    },
  },
  styles: {
    global: {
      body: {
        bg: "surface.900",
        color: "gray.100",
      },
    },
  },
  components: {
    Button: {
      baseStyle: {
        fontWeight: "600",
        borderRadius: "lg",
      },
    },
  },
});
