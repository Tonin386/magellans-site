import { defineComponent } from "./define";

/** Anime un nombre de 0 à sa valeur quand il apparaît à l'écran. */
export const countUp = (target = 0) =>
  defineComponent({
    // La vraie valeur est affichée d'emblée : l'animation n'est qu'un bonus.
    value: target,
    done: false,
    start() {
      if (this.done) return;
      this.done = true;
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches || target <= 0) return;
      const duration = 1400;
      const startTime = performance.now();
      const tick = (now: number) => {
        const progress = Math.min(1, (now - startTime) / duration);
        const eased = 1 - Math.pow(1 - progress, 4);
        this.value = Math.round(target * eased);
        if (progress < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    },
  });
