import { type Challenge, solve } from "../lib/proof-of-work";
import ProofOfWorkWorker from "../lib/proof-of-work.worker?worker&inline";
import { defineComponent } from "./define";

/** Résout le défi dans un worker (CSP : worker-src blob:), à défaut sur le fil principal. */
function solveInBackground(challenge: Challenge): Promise<number | null> {
  return new Promise((resolve) => {
    let worker: Worker;
    try {
      worker = new ProofOfWorkWorker();
    } catch {
      solve(challenge).then(resolve, () => resolve(null));
      return;
    }
    worker.onmessage = (event: MessageEvent<number | null>) => {
      worker.terminate();
      resolve(event.data);
    };
    worker.onerror = () => {
      worker.terminate();
      solve(challenge).then(resolve, () => resolve(null));
    };
    worker.postMessage(challenge);
  });
}

/**
 * Protection anti-robots d'un formulaire public (gabarit cotton/antispam.html).
 * Le calcul démarre dès qu'on touche au formulaire ; si l'on envoie avant la fin,
 * l'envoi (HTMX ou classique) est retenu puis relancé une fois la preuve trouvée.
 */
export const antispam = () => {
  // Hors de l'état réactif d'Alpine : objets natifs et écouteurs à retirer.
  let task: Promise<void> | null = null;
  let cleanup = () => {};

  return defineComponent({
    waiting: false,
    settled: false,
    init() {
      const form = this.$el.closest("form");
      if (!form) return;
      const start = () => void this.start();
      const onSubmit = (event: SubmitEvent) => {
        if (event.target !== form || this.settled) return;
        // Retenu avant HTMX (phase de capture sur le document), puis relancé.
        event.preventDefault();
        event.stopImmediatePropagation();
        this.waiting = true;
        const submitter = event.submitter;
        void this.start().then(() => {
          this.waiting = false;
          if (typeof form.requestSubmit === "function") form.requestSubmit(submitter ?? undefined);
          else form.submit();
        });
      };
      form.addEventListener("focusin", start, { once: true });
      form.addEventListener("pointerdown", start, { once: true });
      document.addEventListener("submit", onSubmit, true);
      cleanup = () => {
        form.removeEventListener("focusin", start);
        form.removeEventListener("pointerdown", start);
        document.removeEventListener("submit", onSubmit, true);
      };
    },
    destroy() {
      cleanup();
    },
    start(): Promise<void> {
      if (!task) {
        const { salt = "", hash = "", max = "0" } = this.$el.dataset;
        task = solveInBackground({ salt, hash, max: Number(max) }).then((proof) => {
          // Sans preuve, le formulaire part quand même : le serveur explique le refus.
          if (proof !== null) (this.$refs.proof as HTMLInputElement).value = String(proof);
          this.settled = true;
        });
      }
      return task;
    },
  });
};
