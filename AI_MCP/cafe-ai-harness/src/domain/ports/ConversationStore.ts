import type { Conversation } from "../entities/Conversation.js";
import type { Message } from "../entities/Message.js";

export interface ConversationStore {
  get(userId: string): Promise<Conversation | null>;
  set(conversation: Conversation): Promise<void>;
  delete(userId: string): Promise<void>;
  getContextWindow(userId: string, modelId?: string): Promise<Message[]>;
}