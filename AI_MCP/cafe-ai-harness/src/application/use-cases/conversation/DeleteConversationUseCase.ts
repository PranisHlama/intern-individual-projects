import type { ConversationStore } from "@domain/ports/ConversationStore.js";

export interface DeleteConversationInput {
  userId: string;
}

export interface DeleteConversationOutput {
  success: boolean;
}

export class DeleteConversationUseCase {
  private readonly conversationStore: ConversationStore;

  constructor(deps: { conversationStore: ConversationStore }) {
    this.conversationStore = deps.conversationStore;
  }

  async execute(input: DeleteConversationInput): Promise<DeleteConversationOutput> {
    await this.conversationStore.delete(input.userId);
    return { success: true };
  }
}