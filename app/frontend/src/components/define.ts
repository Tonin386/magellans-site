/** Propriétés « magiques » fournies par Alpine.js aux composants. */
export interface AlpineMagics {
  $el: HTMLElement;
  $refs: Record<string, HTMLElement>;
  $root: HTMLElement;
  $nextTick(callback?: () => void): Promise<void>;
  $dispatch(event: string, detail?: unknown): void;
  $watch(property: string, callback: (value: unknown) => void): void;
}

/** Déclare un composant Alpine en conservant le typage de `this`. */
export function defineComponent<T extends object>(definition: T & ThisType<T & AlpineMagics>): T {
  return definition;
}
