export type GameModeType = "stockfish" | "groq" | "human";
export type PlayerColor = "White" | "Black";

export interface CustomSquareStyles {
  [square: string]: React.CSSProperties;
}

export interface GroqModel {
  key: string;
  name: string;
  description: string;
}

export interface ModelSelectionProps {
  models: GroqModel[];
  selectedModel: string;
  onModelChange: (model: string) => void;
}
