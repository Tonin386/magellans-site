/**
 * Lignes de tableau cliquables : `<tr data-href="…">` ouvre la fiche au clic n'importe où
 * sur la ligne. Les liens, boutons et champs de la ligne gardent leur propre action ;
 * Ctrl/⌘-clic, Maj-clic ou clic molette ouvrent dans un nouvel onglet. Un lien de la ligne
 * reste le moyen d'y accéder au clavier.
 */
const INTERACTIVE = "a, button, input, select, textarea, label, summary, [role=button]";

function rowFor(event: MouseEvent): HTMLElement | null {
  const target = event.target as Element | null;
  if (!target || target.closest(INTERACTIVE)) return null;
  if (window.getSelection()?.toString()) return null; // l'utilisateur sélectionne du texte
  return target.closest<HTMLElement>("tr[data-href]");
}

export function setupRowLinks(): void {
  document.addEventListener("click", (event) => {
    const row = rowFor(event);
    if (!row?.dataset.href || event.button !== 0) return;
    if (event.ctrlKey || event.metaKey || event.shiftKey) window.open(row.dataset.href, "_blank", "noopener");
    else window.location.assign(row.dataset.href);
  });
  document.addEventListener("auxclick", (event) => {
    const row = rowFor(event);
    if (row?.dataset.href && event.button === 1) window.open(row.dataset.href, "_blank", "noopener");
  });
}
