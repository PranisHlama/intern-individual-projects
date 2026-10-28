import type { Message } from "./Message.js";
import { v4 as uuidv4 } from "uuid";

export interface ConversationProps {
  userId: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

export class Conversation {
  private readonly id: string;
  private props: ConversationProps;
  private static readonly MAX_MESSAGES = 100;

  private constructor(props: ConversationProps, id?: string) {
    this.id = id ?? uuidv4();
    this.props = props;
  }

  static create(userId: string): Conversation {
    if (!userId || userId.trim() === "") {
      throw new Error("userId is required and cannot be empty");
    }
    const now = new Date();
    return new Conversation(
      {
        userId: userId.trim(),
        messages: [],
        createdAt: now,
        updatedAt: now,
      },
      uuidv4()
    );
  }

  static reconstitute(props: ConversationProps & { id: string }): Conversation {
    return new Conversation(
      {
        userId: props.userId,
        messages: props.messages,
        createdAt: props.createdAt,
        updatedAt: props.updatedAt,
      },
      props.id
    );
  }

  getId(): string {
    return this.id;
  }

  getUserId(): string {
    return this.props.userId;
  }

  getMessages(): ReadonlyArray<Message> {
    return [...this.props.messages].sort(
      (a, b) => a.getTimestamp().getTime() - b.getTimestamp().getTime()
    );
  }

  getCreatedAt(): Date {
    return this.props.createdAt;
  }

  getUpdatedAt(): Date {
    return this.props.updatedAt;
  }

  addMessage(message: Message): void {
    if (this.props.messages.length >= Conversation.MAX_MESSAGES) {
      this.props.messages.shift();
    }
    this.props.messages.push(message);
    this.props.updatedAt = new Date();
  }

  clear(): void {
    this.props.messages = [];
    this.props.updatedAt = new Date();
  }

  getMessageCount(): number {
    return this.props.messages.length;
  }

  isEmpty(): boolean {
    return this.props.messages.length === 0;
  }

  toSnapshot(): ConversationProps & { id: string } {
    return {
      id: this.id,
      userId: this.props.userId,
      messages: [...this.props.messages],
      createdAt: this.props.createdAt,
      updatedAt: this.props.updatedAt,
    };
  }
}