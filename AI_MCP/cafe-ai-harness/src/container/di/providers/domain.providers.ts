import { container } from "@container/di/Container.js";
import { TOKENS } from "@container/di/tokens.js";
import { PinoLoggerAdapter } from "@infrastructure/adapters/secondary/logging/PinoLoggerAdapter.js";
import { UuidCorrelationProviderAdapter } from "@infrastructure/adapters/secondary/correlation/UuidCorrelationProviderAdapter.js";

export function registerDomainProviders(): void {
  container.registerSingleton(TOKENS.Logger, new PinoLoggerAdapter());
  container.registerSingleton(TOKENS.CorrelationProvider, new UuidCorrelationProviderAdapter());
}