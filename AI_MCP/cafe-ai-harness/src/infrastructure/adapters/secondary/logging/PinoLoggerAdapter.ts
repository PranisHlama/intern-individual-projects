import pino from "pino";
import { getConfig } from "@infrastructure/config/EnvConfig.js";
import type { Logger } from "@domain/ports/Logger.js";

export class PinoLoggerAdapter implements Logger {
  private readonly logger: pino.Logger;

  constructor() {
    const config = getConfig();
    const options: pino.LoggerOptions = {
      level: config.LOG_LEVEL,
    };

    if (config.LOG_PRETTY) {
      options.transport = {
        target: "pino-pretty",
        options: { colorize: true, translateTime: "HH:MM:ss Z" },
      };
    }

    this.logger = pino(options);
  }

  info(message: string, context?: Record<string, unknown>): void {
    this.logger.info(context, message);
  }

  warn(message: string, context?: Record<string, unknown>): void {
    this.logger.warn(context, message);
  }

  error(message: string, context?: Record<string, unknown>): void {
    this.logger.error(context, message);
  }

  debug(message: string, context?: Record<string, unknown>): void {
    this.logger.debug(context, message);
  }
}