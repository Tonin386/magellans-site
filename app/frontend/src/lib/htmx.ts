import type htmxType from "htmx.org";

type Htmx = typeof htmxType;

/** Configuration sûre de HTMX : aucune évaluation de code, aucun script injecté. */
export function setupHtmx(htmx: Htmx): void {
  Object.assign(htmx.config, {
    allowEval: false,
    allowScriptTags: false,
    includeIndicatorStyles: false,
    historyCacheSize: 0, // pas de copie des pages (parfois sensibles) dans le stockage local
    selfRequestsOnly: true,
    scrollBehavior: "smooth",
    defaultSwapStyle: "innerHTML",
    responseHandling: [
      { code: "204", swap: false },
      { code: "[23]..", swap: true },
      { code: "422", swap: true }, // erreurs de validation : on affiche le formulaire renvoyé
      { code: "[45]..", swap: false, error: true },
    ],
  });

  // Jeton CSRF ajouté à toutes les requêtes HTMX (cf. <meta name="csrf-token">).
  document.body.addEventListener("htmx:configRequest", (event) => {
    const token = document.querySelector<HTMLMetaElement>('meta[name="csrf-token"]')?.content;
    const detail = (event as CustomEvent).detail as { headers: Record<string, string> };
    if (token) detail.headers["X-CSRFToken"] = token;
  });

  // Erreurs réseau ou serveur : un message clair plutôt qu'un silence.
  document.body.addEventListener("htmx:responseError", (event) => {
    const status = (event as CustomEvent).detail?.xhr?.status as number | undefined;
    const message =
      status === 403
        ? "Action non autorisée."
        : status === 404
          ? "Élément introuvable : il a peut-être été supprimé."
          : "Une erreur est survenue. Réessaie dans un instant.";
    window.dispatchEvent(new CustomEvent("toast", { detail: { value: [{ message, tone: "error" }] } }));
  });
  document.body.addEventListener("htmx:sendError", () => {
    window.dispatchEvent(
      new CustomEvent("toast", {
        detail: { value: [{ message: "Connexion impossible. Vérifie ta connexion internet.", tone: "error" }] },
      }),
    );
  });

  // Confirmation stylée pour les actions sensibles (attribut hx-confirm).
  document.body.addEventListener("htmx:confirm", (event) => {
    const detail = (event as CustomEvent).detail as {
      question: string | null;
      issueRequest: (skip?: boolean) => void;
      elt: Element;
    };
    if (!detail.question) return;
    event.preventDefault();
    window.dispatchEvent(
      new CustomEvent("confirm-dialog", {
        detail: {
          message: detail.question,
          danger: detail.elt.hasAttribute("data-confirm-danger"),
          confirmLabel: detail.elt.getAttribute("data-confirm-label") || "Confirmer",
          onConfirm: () => detail.issueRequest(true),
        },
      }),
    );
  });

  // Fermeture automatique des modales après une action réussie (HX-Trigger: close-modal).
  document.body.addEventListener("close-modal", () => {
    window.dispatchEvent(new CustomEvent("modal-close"));
  });
}
