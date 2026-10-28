import { v4 as uuidv4 } from "uuid";

export interface ToolCallProps {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
  result: unknown;
  error: string | null;
  durationMs: number;
  timestamp: Date;
}

export class ToolCall {
  private readonly props: ToolCallProps;

  private constructor(props: ToolCallProps) {
    this.props = props;
  }

  static create(name: string, args: Record<string, unknown>): ToolCall {
    if (!name || name.trim() === "") {
      throw new Error("Tool name is required");
    }
    return new ToolCall({
      id: uuidv4(),
      name: name.trim(),
      arguments: args,
      result: null,
      error: null,
      durationMs: 0,
      timestamp: new Date(),
    });
  }

  static createCompleted(
    name: string,
    args: Record<string, unknown>,
    result: unknown,
    durationMs: number
  ): ToolCall {
    const toolCall = ToolCall.create(name, args);
    toolCall.props.result = result;
    toolCall.props.durationMs = durationMs;
    return toolCall;
  }

  static createFailed(
    name: string,
    args: Record<string, unknown>,
    error: string,
    durationMs: number
  ): ToolCall {
    const toolCall = ToolCall.create(name, args);
    toolCall.props.error = error;
    toolCall.props.durationMs = durationMs;
    return toolCall;
  }

  static reconstitute(props: ToolCallProps): ToolCall {
    return new ToolCall({
      ...props,
      timestamp: typeof props.timestamp === "string" ? new Date(props.timestamp) : props.timestamp,
    });
  }

  getId(): string {
    return this.props.id;
  }

  getName(): string {
    return this.props.name;
  }

  getArguments(): Record<string, unknown> {
    return { ...this.props.arguments };
  }

  getResult(): unknown {
    return this.props.result;
  }

  getError(): string | null {
    return this.props.error;
  }

  getDurationMs(): number {
    return this.props.durationMs;
  }

  getTimestamp(): Date {
    return this.props.timestamp;
  }

  isSuccess(): boolean {
    return this.props.error === null;
  }

  isFailure(): boolean {
    return this.props.error !== null;
  }

  toSnapshot(): ToolCallProps {
    return { ...this.props };
  }
}