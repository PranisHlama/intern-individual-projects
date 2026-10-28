import type { ModelPreferenceStore } from "@domain/ports/ModelPreferenceStore.js";
import { ModelSelection } from "@domain/entities/ModelSelection.js";
import { getConfig } from "@infrastructure/config/EnvConfig.js";
import { createClient } from "redis";

const PREFIX = "model_preference:";
const TTL_SECONDS = 60 * 60 * 24 * 30;

export class RedisModelPreferenceStore implements ModelPreferenceStore {
  private client: ReturnType<typeof createClient> | null = null;
  private readonly ttlSeconds: number;

  constructor(ttlSeconds = TTL_SECONDS) {
    this.ttlSeconds = ttlSeconds;
  }

  private async ensureConnected(): Promise<ReturnType<typeof createClient>> {
    if (this.client && this.client.isOpen) {
      return this.client;
    }

    const config = getConfig();
    const clientOptions: Record<string, unknown> = {
      socket: {
        host: config.REDIS_HOST,
        port: config.REDIS_PORT,
        connectTimeout: config.REDIS_CONNECTION_TIMEOUT_MS,
      },
      database: config.REDIS_DB,
    };
    if (config.REDIS_USERNAME) clientOptions.username = config.REDIS_USERNAME;
    if (config.REDIS_PASSWORD) clientOptions.password = config.REDIS_PASSWORD;

    this.client = createClient(clientOptions as Parameters<typeof createClient>[0]);

    this.client.on("error", (err: Error) => {
      console.error("Redis ModelPreferenceStore error:", err);
    });

    await this.client.connect();
    return this.client;
  }

  private getKey(userId: string): string {
    return `${PREFIX}${userId}`;
  }

  async get(userId: string): Promise<ModelSelection | null> {
    const client = await this.ensureConnected();
    const data = await client.get(this.getKey(userId));
    if (!data) {
      return null;
    }
    try {
      const parsed = JSON.parse(data) as { userId: string; modelId: string; updatedAt: Date; id: string };
      return ModelSelection.reconstitute(parsed);
    } catch {
      return null;
    }
  }

  async set(selection: ModelSelection): Promise<void> {
    const client = await this.ensureConnected();
    const snapshot = selection.toSnapshot();
    await client.set(this.getKey(selection.getUserId()), JSON.stringify(snapshot), {
      EX: this.ttlSeconds,
    });
  }

  async delete(userId: string): Promise<void> {
    const client = await this.ensureConnected();
    await client.del(this.getKey(userId));
  }

  async disconnect(): Promise<void> {
    if (this.client && this.client.isOpen) {
      await this.client.quit();
      this.client = null;
    }
  }
}