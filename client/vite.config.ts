import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteStaticCopy } from "vite-plugin-static-copy";
import type { UserConfig } from "vite";

export default defineConfig({
  plugins: [
    react(),
    // Ship the Stockfish WASM engine with the app so it runs fully client-side
    viteStaticCopy({
      targets: [
        {
          src: "node_modules/stockfish/bin/stockfish-18-lite-single.js",
          dest: "engine",
        },
        {
          src: "node_modules/stockfish/bin/stockfish-18-lite-single.wasm",
          dest: "engine",
        },
      ],
    }),
  ],
}) as UserConfig;
