export type GameModeType = "stockfish" | "groq" | "human";
export type PlayerColor = "White" | "Black";

export interface CustomSquareStyles {
  [square: string]: React.CSSProperties;
}
