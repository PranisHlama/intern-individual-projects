import type { ServiceMap } from "./tokens.js";

export class Container {
  private readonly singletons = new Map<string, unknown>();
  private readonly factories = new Map<string, () => unknown>();

  registerSingleton<K extends keyof ServiceMap>(token: K, instance: ServiceMap[K]): void {
    this.singletons.set(token, instance);
  }

  registerFactory<K extends keyof ServiceMap>(token: K, factory: () => ServiceMap[K]): void {
    this.factories.set(token, factory);
  }

  resolve<K extends keyof ServiceMap>(token: K): ServiceMap[K] {
    if (this.singletons.has(token)) {
      return this.singletons.get(token) as ServiceMap[K];
    }

    const factory = this.factories.get(token);
    if (!factory) {
      throw new Error(`No registration found for token: ${String(token)}`);
    }

    const instance = factory() as ServiceMap[K];
    this.singletons.set(token, instance);
    return instance;
  }

  has(token: string): boolean {
    return this.singletons.has(token) || this.factories.has(token);
  }
}

export const container = new Container();