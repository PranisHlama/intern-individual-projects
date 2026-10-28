import type { ConversationStore } from "@domain/ports/ConversationStore.js";

export interface GetConversationInput {
  userId: string;
}

export interface GetConversationOutput {
  messages: Array<{
    role: "user" | "assistant";
    content: string;
    timestamp: string;
    toolCalls?: Array<{
      name: string;
      arguments: Record<string, unknown>;
      result: unknown;
      error: string | undefined;
      durationMs: number;
    }>;
  }>;
}

export class GetConversationUseCase {
  private readonly conversationStore: ConversationStore;

  constructor(deps: { conversationStore: ConversationStore }) {
    this.conversationStore = deps.conversationStore;
  }

  async execute(input: GetConversationInput): Promise<GetConversationOutput> {
    const conversation = await this.conversationStore.get(input.userId);

    if (!conversation) {
      return { messages: [] };
    }

    const messages = conversation.getMessages().map((msg) => ({
      role: msg.getRole() as "user" | "assistant",
      content: msg.getContent(),
      timestamp: msg.getTimestamp().toISOString(),
      toolCalls: msg.getToolCalls().map((tc) => ({
        name: tc.getName(),
        arguments: tc.getArguments(),
        result: tc.getResult(),
        error: tc.getError() ?? undefined,
        durationMs: tc.getDurationMs(),
      })),
    }));

    return { messages };
  }
}