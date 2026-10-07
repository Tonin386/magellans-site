/**
 * Point d'entrée de l'interface magellans.fr.
 *
 * - HTMX : interactions avec le serveur (formulaires, filtres, mises à jour partielles) ;
 * - Alpine.js (build CSP) : petits comportements côté navigateur ;
 * - les modules lourds (sélecteurs avec recherche, signature…) sont chargés à la demande.
 */
import "./styles/main.css";

import collapse from "@alpinejs/collapse";
import Alpine from "@alpinejs/csp";
import focus from "@alpinejs/focus";
import intersect from "@alpinejs/intersect";
import sort from "@alpinejs/sort";
import htmx from "htmx.org";

import { registerComponents } from "./components";
import { enhance } from "./lib/enhance";
import { setupHtmx } from "./lib/htmx";
import { setupRowLinks } from "./lib/row-links";
import { setupToasts } from "./lib/toasts";

declare global {
  interface Window {
    htmx: typeof htmx;
    Alpine: typeof Alpine;
  }
}

window.htmx = htmx;
setupHtmx(htmx);

Alpine.plugin([focus, collapse, intersect, sort]);
registerComponents(Alpine);
setupToasts(Alpine);
window.Alpine = Alpine;
Alpine.start();

enhance(document);
setupRowLinks();
document.body.addEventListener("htmx:afterSettle", (event) => {
  enhance(event.target as Element);
});
