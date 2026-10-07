import type TomSelectInstance from "tom-select";

/**
 * Améliorations progressives chargées uniquement quand la page en a besoin.
 * Appelé au chargement et après chaque remplacement HTMX.
 */
export function enhance(root: ParentNode): void {
  const selects = root.querySelectorAll<HTMLSelectElement>("select[data-searchable]:not(.tomselected)");
  if (selects.length) {
    void import("tom-select").then(({ default: TomSelect }) => {
      selects.forEach((select) => {
        if (select.tomselect) return;
        const allowCreate = select.hasAttribute("data-create");
        new TomSelect(select, {
          create: allowCreate,
          maxOptions: 500,
          allowEmptyOption: true,
          plugins: select.multiple ? ["remove_button"] : [],
          render: {
            no_results: () => '<div class="no-results">Aucun résultat</div>',
            option_create: (data: { input: string }, escape: (s: string) => string) =>
              `<div class="create">Ajouter « ${escape(data.input)} »</div>`,
          },
        });
      });
    });
  }

  // Formulaires « auto-submit » (filtres) : envoi automatique quand on change une valeur.
  root.querySelectorAll<HTMLFormElement>("form[data-autosubmit]:not([data-enhanced])").forEach((form) => {
    form.dataset.enhanced = "1";
    form.addEventListener("change", () => form.requestSubmit());
  });
}

declare global {
  interface HTMLSelectElement {
    tomselect?: TomSelectInstance;
  }
}
