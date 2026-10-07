/**
 * Composants Alpine.js.
 *
 * Le site utilise la version « CSP » d'Alpine (aucun `eval`) : toute logique non
 * triviale est déclarée ici, et les gabarits ne contiennent que des appels simples
 * (`x-data="dropdown"`, `@click="toggle()"`, `x-show="open"`…).
 */
import type { AlpineInstance } from "@alpinejs/csp";

import { consent } from "./consent";
import { defineComponent } from "./define";
import { countUp } from "./count-up";
import { filterList } from "./filter-list";
import { helloassoWidget } from "./helloasso";
import { signatureField } from "./signature";

type Theme = "light" | "dark" | "system";

function readStorage(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStorage(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    /* stockage indisponible (navigation privée…) */
  }
}

export function applyTheme(theme: Theme): void {
  const dark = theme === "dark" || (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  if (!document.documentElement.hasAttribute("data-force-theme")) {
    document.documentElement.classList.toggle("dark", dark);
  }
}

export function registerComponents(Alpine: AlpineInstance): void {
  // ------------------------------------------------------------- Thème
  Alpine.data("themeSwitcher", () =>
    defineComponent({
    theme: (readStorage("magellans-theme") as Theme) || "system",
    init() {
      window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
        if (this.theme === "system") applyTheme("system");
      });
    },
    set(value: Theme) {
      this.theme = value;
      writeStorage("magellans-theme", value);
      applyTheme(value);
    },
    isActive(value: Theme) {
      return this.theme === value;
    },
  }),
  );

  // -------------------------------------------------- Menus déroulants
  Alpine.data("dropdown", () =>
    defineComponent({
    open: false,
    toggle() {
      this.open = !this.open;
    },
    close() {
      this.open = false;
    },
  }),
  );

  // -------------------------------------------- Navigation mobile / tiroir
  Alpine.data("drawer", () =>
    defineComponent({
    open: false,
    toggle() {
      this.open = !this.open;
      document.documentElement.classList.toggle("overflow-hidden", this.open);
    },
    close() {
      this.open = false;
      document.documentElement.classList.remove("overflow-hidden");
    },
    closeOnLink(event: Event) {
      if ((event.target as Element).closest("a")) this.close();
    },
  }),
  );

  // ------------------------------------------------- En-tête du site public
  Alpine.data("siteHeader", () =>
    defineComponent({
    scrolled: false,
    menuOpen: false,
    init() {
      const update = () => {
        this.scrolled = window.scrollY > 24;
      };
      update();
      window.addEventListener("scroll", update, { passive: true });
    },
    toggleMenu() {
      this.menuOpen = !this.menuOpen;
      document.documentElement.classList.toggle("overflow-hidden", this.menuOpen);
    },
    closeMenu() {
      this.menuOpen = false;
      document.documentElement.classList.remove("overflow-hidden");
    },
  }),
  );

  // ------------------------------------------------------------ Modales
  // <dialog> natif : accessibilité (focus, Échap) gérée par le navigateur.
  Alpine.data("modal", (startOpen = false) =>
    defineComponent({
    init() {
      if (startOpen) this.show();
      window.addEventListener("modal-close", () => this.hide());
    },
    show() {
      const dialog = this.$refs.dialog as HTMLDialogElement | undefined;
      if (dialog && !dialog.open) dialog.showModal();
    },
    hide() {
      const dialog = this.$refs.dialog as HTMLDialogElement | undefined;
      if (dialog?.open) dialog.close();
    },
    backdropClose(event: MouseEvent) {
      if (event.target === this.$refs.dialog) this.hide();
    },
  }),
  );

  // Modale unique chargée par HTMX (#modal-content) : s'ouvre quand du contenu arrive.
  Alpine.data("remoteModal", () =>
    defineComponent({
    title: "",
    init() {
      document.body.addEventListener("htmx:afterSwap", (event) => {
        const target = (event as CustomEvent).detail?.target as Element | undefined;
        if (target?.id === "modal-content") {
          this.title = target.querySelector("[data-modal-title]")?.textContent?.trim() || "";
          const dialog = this.$refs.dialog as HTMLDialogElement;
          if (!dialog.open) dialog.showModal();
        }
      });
      window.addEventListener("modal-close", () => this.hide());
    },
    hide() {
      const dialog = this.$refs.dialog as HTMLDialogElement;
      if (dialog.open) dialog.close();
    },
    backdropClose(event: MouseEvent) {
      if (event.target === this.$refs.dialog) this.hide();
    },
  }),
  );

  // ------------------------------------------- Boîte de confirmation (hx-confirm)
  Alpine.data("confirmDialog", () =>
    defineComponent({
    message: "",
    confirmLabel: "Confirmer",
    danger: false,
    callback: null as null | (() => void),
    init() {
      window.addEventListener("confirm-dialog", (event) => {
        const detail = (event as CustomEvent).detail;
        this.message = detail.message;
        this.confirmLabel = detail.confirmLabel;
        this.danger = detail.danger;
        this.callback = detail.onConfirm;
        (this.$refs.dialog as HTMLDialogElement).showModal();
      });
    },
    accept() {
      (this.$refs.dialog as HTMLDialogElement).close();
      this.callback?.();
      this.callback = null;
    },
    cancel() {
      (this.$refs.dialog as HTMLDialogElement).close();
      this.callback = null;
    },
  }),
  );

  // ------------------------------------------------------- Onglets
  Alpine.data("tabs", (initial = "") =>
    defineComponent({
    active: initial,
    init() {
      const fromHash = window.location.hash.replace("#", "");
      if (fromHash && this.$el.querySelector(`[data-tab="${CSS.escape(fromHash)}"]`)) this.active = fromHash;
    },
    select(name: string) {
      this.active = name;
      history.replaceState(null, "", `#${name}`);
    },
    isActive(name: string) {
      return this.active === name;
    },
  }),
  );

  // ------------------------------------------------ Copier dans le presse-papiers
  Alpine.data("copyable", (text = "") =>
    defineComponent({
    copied: false,
    async copy() {
      try {
        await navigator.clipboard.writeText(text);
        this.copied = true;
        window.setTimeout(() => (this.copied = false), 2000);
      } catch {
        window.dispatchEvent(
          new CustomEvent("toast", { detail: { value: [{ message: "Copie impossible.", tone: "error" }] } }),
        );
      }
    },
  }),
  );

  // ----------------------------------------------- Dépôt de fichiers (glisser-déposer)
  Alpine.data("fileDrop", () =>
    defineComponent({
    dragging: false,
    files: [] as string[],
    update() {
      const input = this.$refs.input as HTMLInputElement;
      this.files = Array.from(input.files ?? []).map((file) => `${file.name} (${Math.ceil(file.size / 1024)} Ko)`);
    },
    drop(event: DragEvent) {
      this.dragging = false;
      const input = this.$refs.input as HTMLInputElement;
      if (event.dataTransfer?.files?.length) {
        input.files = event.dataTransfer.files;
        input.dispatchEvent(new Event("change", { bubbles: true }));
      }
    },
    hasFiles() {
      return this.files.length > 0;
    },
  }),
  );

  // ------------------------------------------------- Vidéo YouTube à la demande
  // L'iframe (et donc les cookies YouTube) n'est chargée qu'au clic.
  Alpine.data("videoFacade", (embedUrl = "") =>
    defineComponent({
    playing: false,
    play() {
      if (!embedUrl.startsWith("https://")) return;
      this.playing = true;
      this.$nextTick(() => {
        const frame = this.$refs.frame as HTMLIFrameElement | undefined;
        if (frame) frame.src = embedUrl;
      });
    },
  }),
  );

  // ------------------------------------------------- Vidéo d'arrière-plan (accueil)
  // Chargée seulement si la connexion le permet (mode économie de données, réseau lent
  // et « réduire les animations » sont respectés) : sinon l'affiche suffit.
  Alpine.data("heroVideo", () =>
    defineComponent({
      paused: true,
      enabled: false,
      init() {
        const video = this.$refs.video as HTMLVideoElement | undefined;
        if (!video) return;
        const connection = (navigator as Navigator & { connection?: { saveData?: boolean; effectiveType?: string } })
          .connection;
        const slow = connection?.saveData || ["slow-2g", "2g", "3g"].includes(connection?.effectiveType ?? "");
        const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        if (slow || reduced) return;
        const source = video.dataset.src;
        if (!source) return;
        video.src = source;
        this.enabled = true;
        video.play().then(
          () => (this.paused = false),
          () => (this.paused = true),
        );
      },
      toggle() {
        const video = this.$refs.video as HTMLVideoElement;
        if (!this.enabled) {
          this.enabled = true;
          video.src = video.dataset.src ?? "";
        }
        if (video.paused) {
          void video.play();
          this.paused = false;
        } else {
          video.pause();
          this.paused = true;
        }
      },
    }),
  );

  // ------------------------------------------- Vidéo intégrée (« Dans les coulisses »)
  // Lecture automatique, sans son, uniquement quand la vidéo est visible à l'écran.
  Alpine.data("inlineVideo", () =>
    defineComponent({
      playing: false,
      allowed: true,
      init() {
        const connection = (navigator as Navigator & { connection?: { saveData?: boolean; effectiveType?: string } })
          .connection;
        const slow = connection?.saveData || ["slow-2g", "2g", "3g"].includes(connection?.effectiveType ?? "");
        this.allowed = !slow && !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      },
      load() {
        const video = this.$refs.video as HTMLVideoElement;
        if (!video.src && video.dataset.src) video.src = video.dataset.src;
        return video;
      },
      enter() {
        if (!this.allowed) return;
        this.load()
          .play()
          .then(() => (this.playing = true))
          .catch(() => (this.playing = false));
      },
      leave() {
        const video = this.$refs.video as HTMLVideoElement;
        if (!video.paused) video.pause();
        this.playing = false;
      },
      toggle() {
        const video = this.load();
        if (video.paused) {
          void video.play();
          this.playing = true;
        } else {
          video.pause();
          this.playing = false;
        }
      },
      fullscreen() {
        const video = this.load();
        void video.play();
        this.playing = true;
        if (video.requestFullscreen) void video.requestFullscreen();
      },
    }),
  );

  // ----------------------------------------------------- Thème « hiver »
  Alpine.data("snowfall", () =>
    defineComponent({
    init() {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      for (let i = 0; i < 28; i += 1) {
        const flake = document.createElement("span");
        flake.className = "snowflake";
        flake.textContent = "❄";
        flake.setAttribute("aria-hidden", "true");
        flake.style.left = `${Math.random() * 100}vw`;
        flake.style.fontSize = `${8 + Math.random() * 14}px`;
        flake.style.animationDuration = `${8 + Math.random() * 12}s`;
        flake.style.animationDelay = `${-Math.random() * 20}s`;
        flake.style.setProperty("--drift", `${-40 + Math.random() * 80}px`);
        this.$el.appendChild(flake);
      }
    },
  }),
  );

  // ------------------------------------------------- Dates d'une réservation
  Alpine.data("dateRange", (minStart = "") =>
    defineComponent({
    start: "",
    end: "",
    init() {
      const startInput = this.$refs.start as HTMLInputElement | undefined;
      const endInput = this.$refs.end as HTMLInputElement | undefined;
      this.start = startInput?.value ?? "";
      this.end = endInput?.value ?? "";
      if (startInput && minStart) startInput.min = minStart;
    },
    sync() {
      const endInput = this.$refs.end as HTMLInputElement | undefined;
      if (endInput && this.start) {
        endInput.min = this.start;
        if (this.end && this.end < this.start) this.end = this.start;
      }
    },
    isValid() {
      return Boolean(this.start && this.end && this.end > this.start);
    },
  }),
  );

  // ----------------------------------------------- Formulaires multiples (formsets Django)
  // Ajoute une ligne à partir d'un <template> contenant le formulaire vide (__prefix__).
  Alpine.data("formset", (prefix = "form") =>
    defineComponent({
      total: 0,
      init() {
        const input = this.$el.querySelector<HTMLInputElement>(`input[name="${prefix}-TOTAL_FORMS"]`);
        this.total = Number(input?.value ?? 0);
      },
      add() {
        const template = this.$refs.template as HTMLTemplateElement;
        const container = this.$refs.rows as HTMLElement;
        const html = template.innerHTML.replace(/__prefix__/g, String(this.total));
        container.insertAdjacentHTML("beforeend", html);
        this.total += 1;
        const input = this.$el.querySelector<HTMLInputElement>(`input[name="${prefix}-TOTAL_FORMS"]`);
        if (input) input.value = String(this.total);
        this.$nextTick(() => {
          const rows = container.querySelectorAll<HTMLElement>("[data-formset-row]");
          rows[rows.length - 1]?.querySelector<HTMLInputElement>("input:not([type=hidden])")?.focus();
        });
      },
      remove(event: Event) {
        const row = (event.target as Element).closest<HTMLElement>("[data-formset-row]");
        if (!row) return;
        const del = row.querySelector<HTMLInputElement>('input[type="checkbox"][name$="-DELETE"]');
        if (del) {
          del.checked = true;
          row.hidden = true;
        } else {
          row.remove();
        }
      },
    }),
  );

  // --------------------------------------------- Listes réordonnables (glisser-déposer)
  Alpine.data("sortableList", () =>
    defineComponent({
      sorted() {
        this.$el.dispatchEvent(new CustomEvent("reordered", { bubbles: true }));
      },
    }),
  );

  Alpine.data("consent", consent);
  Alpine.data("countUp", countUp);
  Alpine.data("filterList", filterList);
  Alpine.data("helloassoWidget", helloassoWidget);
  Alpine.data("signatureField", signatureField);
}
