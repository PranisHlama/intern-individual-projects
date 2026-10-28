import { ToolCall, type ToolCallProps } from "./ToolCall.js";
import { v4 as uuidv4 } from "uuid";

export type MessageRole = "user" | "assistant";

export interface MessageProps {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  toolCalls: ToolCallProps[];
}

export class Message {
  private readonly props: MessageProps;
  private static readonly MAX_CONTENT_LENGTH = 50000;

  private constructor(props: MessageProps) {
    this.props = {
      ...props,
      toolCalls: props.toolCalls.map((tc) => ToolCall.reconstitute(tc).toSnapshot()),
    };
  }

  static createUserMessage(content: string): Message {
    Message.validateContent(content);
    return new Message({
      id: uuidv4(),
      role: "user",
      content: content.trim(),
      timestamp: new Date(),
      toolCalls: [],
    });
  }

  static createAssistantMessage(content: string, toolCalls: ToolCall[] = []): Message {
    Message.validateContent(content);
    return new Message({
      id: uuidv4(),
      role: "assistant",
      content: content.trim(),
      timestamp: new Date(),
      toolCalls: toolCalls.map((tc) => tc.toSnapshot()),
    });
  }

  static reconstitute(props: MessageProps): Message {
    return new Message({
      ...props,
      timestamp: typeof props.timestamp === "string" ? new Date(props.timestamp) : props.timestamp,
      toolCalls: props.toolCalls,
    });
  }

  private static validateContent(content: string): void {
    if (!content || content.trim() === "") {
      throw new Error("Message content is required and cannot be empty");
    }
    if (content.length > Message.MAX_CONTENT_LENGTH) {
      throw new Error(
        `Message content exceeds maximum length of ${String(Message.MAX_CONTENT_LENGTH)} characters`
      );
    }
  }

  getId(): string {
    return this.props.id;
  }

  getRole(): MessageRole {
    return this.props.role;
  }

  getContent(): string {
    return this.props.content;
  }

  getTimestamp(): Date {
    return this.props.timestamp;
  }

  getToolCalls(): ReadonlyArray<ToolCall> {
    return this.props.toolCalls.map((tc) => ToolCall.reconstitute(tc));
  }

  isUserMessage(): boolean {
    return this.props.role === "user";
  }

  isAssistantMessage(): boolean {
    return this.props.role === "assistant";
  }

  toSnapshot(): MessageProps {
    return { ...this.props };
  }
}