import { container } from "@container/di/Container.js";
import { TOKENS } from "@container/di/tokens.js";
import { SendMessageUseCase } from "@application/use-cases/chat/SendMessageUseCase.js";
import { GetConversationUseCase } from "@application/use-cases/conversation/GetConversationUseCase.js";
import { DeleteConversationUseCase } from "@application/use-cases/conversation/DeleteConversationUseCase.js";
import { ExecuteToolUseCase } from "@application/use-cases/tool/ExecuteToolUseCase.js";
import { GetModelsUseCase } from "@application/use-cases/model/GetModelsUseCase.js";
import { GetModelUseCase } from "@application/use-cases/model/GetModelUseCase.js";
import { SetModelPreferenceUseCase } from "@application/use-cases/model/SetModelPreferenceUseCase.js";
import { GetModelPreferenceUseCase } from "@application/use-cases/model/GetModelPreferenceUseCase.js";

export function registerApplicationProviders(): void {
  container.registerFactory(TOKENS.SendMessageUseCase, () => {
    return new SendMessageUseCase({
      mcpClient: container.resolve(TOKENS.MCPClient),
      llmClient: container.resolve(TOKENS.LLMClient),
      conversationStore: container.resolve(TOKENS.ConversationStore),
      logger: container.resolve(TOKENS.Logger),
    });
  });

  container.registerFactory(TOKENS.GetConversationUseCase, () => {
    return new GetConversationUseCase({
      conversationStore: container.resolve(TOKENS.ConversationStore),
    });
  });

  container.registerFactory(TOKENS.DeleteConversationUseCase, () => {
    return new DeleteConversationUseCase({
      conversationStore: container.resolve(TOKENS.ConversationStore),
    });
  });

  container.registerFactory(TOKENS.ExecuteToolUseCase, () => {
    return new ExecuteToolUseCase({
      mcpClient: container.resolve(TOKENS.MCPClient),
      logger: container.resolve(TOKENS.Logger),
    });
  });

  container.registerFactory(TOKENS.GetModelsUseCase, () => {
    return new GetModelsUseCase({
      modelRegistry: container.resolve(TOKENS.ModelRegistry),
    });
  });

  container.registerFactory(TOKENS.GetModelUseCase, () => {
    return new GetModelUseCase({
      modelRegistry: container.resolve(TOKENS.ModelRegistry),
    });
  });

  container.registerFactory(TOKENS.SetModelPreferenceUseCase, () => {
    return new SetModelPreferenceUseCase({
      modelPreferenceStore: container.resolve(TOKENS.ModelPreferenceStore),
    });
  });

  container.registerFactory(TOKENS.GetModelPreferenceUseCase, () => {
    return new GetModelPreferenceUseCase({
      modelPreferenceStore: container.resolve(TOKENS.ModelPreferenceStore),
    });
  });
}