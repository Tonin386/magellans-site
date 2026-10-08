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
        // data-create : saisie libre ; data-create-prefix distingue une nouvelle valeur d'un
        // identifiant existant (ex. « nouveau:Titre » pour un projet à créer).
        const allowCreate = select.hasAttribute("data-create");
        const createPrefix = select.dataset.createPrefix ?? "";
        const createLabel = select.dataset.createLabel ?? "Ajouter";
        const instance = new TomSelect(select, {
          create: allowCreate && createPrefix
            ? (input, done) => {
                done({ value: createPrefix + input.trim(), text: input.trim() });
                return true;
              }
            : allowCreate,
          maxOptions: 500,
          allowEmptyOption: true,
          // Choix unique : la recherche se tape dans la liste déroulante, le champ garde la sélection.
          plugins: select.multiple ? ["remove_button"] : ["dropdown_input"],
          render: {
            // Avec la saisie libre, l'option « Créer… » suffit quand rien ne correspond.
            no_results: () => (allowCreate ? "" : '<div class="no-results">Aucun résultat</div>'),
            option_create: (data: { input: string }, escape: (s: string) => string) =>
              `<div class="create">${escape(createLabel)} « <strong>${escape(data.input)}</strong> »</div>`,
          },
        });
        if (!select.multiple) {
          instance.control_input.placeholder = allowCreate ? "Rechercher ou saisir un nouveau nom…" : "Rechercher…";
        }
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
