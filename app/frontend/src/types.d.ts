declare module "@alpinejs/csp" {
  // Typage minimal de la version « CSP » d'Alpine.js.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  type AnyFn = (...args: any[]) => any;
  interface AlpineInstance {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    data(name: string, callback: (...args: any[]) => Record<string, unknown>): void;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    store(name: string, value?: any): any;
    plugin(plugin: AnyFn | AnyFn[]): void;
    start(): void;
    initTree(el: Element): void;
    nextTick(callback?: () => void): Promise<void>;
  }
  const Alpine: AlpineInstance;
  export default Alpine;
  export type { AlpineInstance };
}
declare module "@alpinejs/focus";
declare module "@alpinejs/collapse";
declare module "@alpinejs/intersect";
declare module "@alpinejs/sort";
