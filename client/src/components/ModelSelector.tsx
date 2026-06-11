import React from "react";
import { Select, Text, VStack } from "@chakra-ui/react";
import { ModelSelectionProps } from "../types";

const ModelSelector: React.FC<ModelSelectionProps> = ({ models, selectedModel, onModelChange }) => {
  if (!models || models.length === 0) return null;

  const current = models.find((m) => m.key === selectedModel);

  return (
    <VStack align="stretch" spacing={2}>
      <Text fontSize="xs" textTransform="uppercase" letterSpacing="wide" color="gray.500">
        Model
      </Text>
      <Select
        value={selectedModel}
        onChange={(e) => onModelChange(e.target.value)}
        bg="surface.700"
        borderColor="surface.600"
        size="md"
        _hover={{ borderColor: "accent.500" }}
      >
        {models.map((model) => (
          <option key={model.key} value={model.key}>
            {model.name}
          </option>
        ))}
      </Select>
      {current && (
        <Text fontSize="xs" color="gray.500" noOfLines={2}>
          {current.description}
        </Text>
      )}
    </VStack>
  );
};

export default ModelSelector;
