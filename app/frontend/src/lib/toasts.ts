import type { AlpineInstance } from "@alpinejs/csp";

export type ToastTone = "success" | "info" | "warning" | "error";
interface Toast {
  id: number;
  message: string;
  tone: ToastTone;
  visible: boolean;
}

let nextId = 1;

/** Notifications éphémères (messages Django, réponses HTMX, erreurs). */
export function setupToasts(Alpine: AlpineInstance): void {
  Alpine.store("toasts", {
    items: [] as Toast[],
    push(message: string, tone: ToastTone = "info") {
      const toast: Toast = { id: nextId++, message, tone, visible: true };
      this.items.push(toast);
      const delay = tone === "error" ? 9000 : 5500;
      window.setTimeout(() => this.dismiss(toast.id), delay);
    },
    dismiss(id: number) {
      const toast = this.items.find((item: Toast) => item.id === id);
      if (toast) toast.visible = false;
      window.setTimeout(() => {
        this.items = this.items.filter((item: Toast) => item.id !== id);
      }, 300);
    },
  });

  const push = (items: unknown) => {
    const list = Array.isArray(items) ? items : [items];
    for (const item of list) {
      if (item && typeof item === "object" && "message" in item) {
        const { message, tone } = item as { message: string; tone?: ToastTone };
        Alpine.store("toasts").push(String(message), tone ?? "info");
      }
    }
  };

  // Événement « toast » : depuis HX-Trigger (detail.value) ou depuis le code (detail.value).
  const onToast = (event: Event) => push((event as CustomEvent).detail?.value);
  window.addEventListener("toast", onToast);
  document.body.addEventListener("toast", (event) => {
    event.stopPropagation();
    onToast(event);
  });

  // Messages présents au chargement de la page (rendus par Django).
  const initial = document.getElementById("initial-toasts");
  if (initial?.textContent) {
    try {
      push(JSON.parse(initial.textContent));
    } catch {
      /* contenu invalide : ignoré */
    }
  }
}
