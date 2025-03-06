import React from "react";
import { Box, FormControl, FormLabel, Select, Tooltip, Text } from "@chakra-ui/react";
import { ModelSelectionProps } from "../types";

const ModelSelector: React.FC<ModelSelectionProps> = ({ models, selectedModel, onModelChange }) => {
  if (!models || models.length === 0) {
    return null;
  }

  return (
    <Box mb={4} width="100%" maxW="400px">
      <FormControl>
        <FormLabel fontWeight="bold">AI Model:</FormLabel>
        <Select value={selectedModel} onChange={(e) => onModelChange(e.target.value)} variant="filled" size="md">
          {models.map((model) => (
            <option key={model.key} value={model.key}>
              {model.name}
            </option>
          ))}
        </Select>
      </FormControl>

      {/* Display the description of the selected model */}
      {models.map(
        (model) =>
          model.key === selectedModel && (
            <Tooltip key={model.key} label={model.description}>
              <Text fontSize="xs" mt={1} color="gray.500" noOfLines={2}>
                {model.description}
              </Text>
            </Tooltip>
          )
      )}
    </Box>
  );
};

export default ModelSelector;
