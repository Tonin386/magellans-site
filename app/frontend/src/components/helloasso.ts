import { defineComponent } from "./define";

const HELLOASSO_ORIGIN = "https://www.helloasso.com";

/** Hauteur annoncée par HelloAsso ({ height } ou sa version texte JSON), sinon NaN. */
const announcedHeight = (data: unknown): number => {
  if (typeof data === "string") {
    try {
      data = JSON.parse(data);
    } catch {
      return Number.NaN;
    }
  }
  return Number((data as { height?: unknown } | null)?.height);
};

/**
 * Formulaire HelloAsso intégré : masque l'écran de chargement une fois le formulaire
 * affiché et adapte la hauteur de l'iframe si HelloAsso l'annonce par postMessage.
 * Le widget actuel ne l'annonce pas : l'iframe garde alors sa hauteur par défaut
 * (750 px, la valeur conseillée par HelloAsso, ajustée au premier écran du formulaire)
 * et les étapes plus longues défilent à l'intérieur.
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
        const height = announcedHeight(event.data);
        if (frame && Number.isFinite(height) && height > 200 && height < 20000) {
          frame.style.height = `${Math.ceil(height)}px`;
        }
      });
    },
  });
