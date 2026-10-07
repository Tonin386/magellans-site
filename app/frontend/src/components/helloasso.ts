import { defineComponent } from "./define";

/**
 * Formulaire HelloAsso intégré : l'iframe envoie sa hauteur par postMessage,
 * on l'adapte pour éviter une double barre de défilement.
 */
export const helloassoWidget = () =>
  defineComponent({
    loaded: false,
    init() {
      window.addEventListener("message", (event: MessageEvent) => {
        if (event.origin !== "https://www.helloasso.com") return;
        const height = Number((event.data as { height?: unknown } | null)?.height);
        const frame = this.$refs.frame as HTMLIFrameElement | undefined;
        if (frame && Number.isFinite(height) && height > 200 && height < 20000) {
          frame.style.height = `${Math.ceil(height)}px`;
        }
      });
    },
    onLoad() {
      this.loaded = true;
    },
  });
