import { defineComponent } from "./define";

const HELLOASSO_ORIGIN = "https://www.helloasso.com";

/**
 * Formulaire HelloAsso intégré : masque l'écran de chargement une fois le formulaire
 * affiché et adapte la hauteur de l'iframe (envoyée par postMessage) pour éviter une
 * double barre de défilement.
 *
 * Aucune directive Alpine sur l'iframe elle-même : la version CSP d'Alpine les refuse.
 */
export const helloassoWidget = () =>
  defineComponent({
    loaded: false,
    init() {
      const frame = this.$el.querySelector("iframe");
      const reveal = () => {
        this.loaded = true;
      };
      frame?.addEventListener("load", reveal, { once: true });
      window.setTimeout(reveal, 8000); // filet de sécurité si l'événement a été manqué
      window.addEventListener("message", (event: MessageEvent) => {
        if (event.origin !== HELLOASSO_ORIGIN) return;
        reveal();
        const height = Number((event.data as { height?: unknown } | null)?.height);
        if (frame && Number.isFinite(height) && height > 200 && height < 20000) {
          frame.style.height = `${Math.ceil(height)}px`;
        }
      });
    },
  });
