import { encoding_for_model, Tiktoken, TiktokenModel } from "tiktoken";

let encoder: Tiktoken | null = null;

function getEncoder(model: string = "gpt-4o"): Tiktoken {
  if (!encoder) {
    try {
      encoder = encoding_for_model(model as TiktokenModel);
    } catch {
      encoder = encoding_for_model("gpt-4o");
    }
  }
  return encoder;
}

export function countTokens(text: string, model?: string): number {
  const enc = getEncoder(model);
  return enc.encode(text).length;
}

export function countMessageTokens(message: { role: string; content: string; toolCalls?: Array<{ function: { name: string; arguments: string } }> }, model?: string): number {
  let tokens = 4;
  tokens += countTokens(message.role, model);
  tokens += countTokens(message.content, model);
  
  if (message.toolCalls) {
    for (const tc of message.toolCalls) {
      tokens += countTokens(tc.function.name, model);
      tokens += countTokens(tc.function.arguments, model);
    }
  }
  
  return tokens;
}

export function countMessagesTokens(messages: Array<{ role: string; content: string; toolCalls?: Array<{ function: { name: string; arguments: string } }> }>, model?: string): number {
  let total = 0;
  for (const msg of messages) {
    total += countMessageTokens(msg, model);
  }
  return total + 2;
}

export function buildTokenWindow<T extends { role: string; content: string; toolCalls?: Array<{ function: { name: string; arguments: string } }> }>(
  messages: readonly T[],
  maxTokens: number,
  model?: string
): T[] {
  const result: T[] = [];
  let totalTokens = 0;
  
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i];
    if (!msg) continue;
    const msgTokens = countMessageTokens(msg, model);
    if (totalTokens + msgTokens > maxTokens && result.length > 0) {
      break;
    }
    result.unshift(msg);
    totalTokens += msgTokens;
  }
  
  return result;
}