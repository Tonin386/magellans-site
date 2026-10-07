import { defineComponent } from "./define";

const STORAGE_KEY = "magellans-consent";

type Choice = "granted" | "denied";

function stored(): Choice | null {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY);
    return value === "granted" || value === "denied" ? value : null;
  } catch {
    return null;
  }
}

/** Charge Google Analytics uniquement après accord explicite (exigence CNIL). */
function loadAnalytics(measurementId: string, nonce: string): void {
  if (!/^G-[A-Z0-9]+$/.test(measurementId) || document.getElementById("ga-script")) return;
  const script = document.createElement("script");
  script.id = "ga-script";
  script.async = true;
  script.nonce = nonce;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(measurementId)}`;
  document.head.appendChild(script);
  const w = window as unknown as { dataLayer: unknown[]; gtag: (...args: unknown[]) => void };
  w.dataLayer = w.dataLayer || [];
  w.gtag = function gtag() {
    // eslint-disable-next-line prefer-rest-params
    w.dataLayer.push(arguments);
  };
  w.gtag("js", new Date());
  w.gtag("config", measurementId, { anonymize_ip: true });
}

export const consent = (measurementId = "", nonce = "") =>
  defineComponent({
    visible: false,
    init() {
      if (!measurementId) return;
      const choice = stored();
      if (choice === "granted") loadAnalytics(measurementId, nonce);
      this.visible = choice === null;
      window.addEventListener("open-consent", () => (this.visible = true));
    },
    decide(choice: Choice) {
      try {
        window.localStorage.setItem(STORAGE_KEY, choice);
      } catch {
        /* ignoré */
      }
      this.visible = false;
      if (choice === "granted") loadAnalytics(measurementId, nonce);
    },
    accept() {
      this.decide("granted");
    },
    refuse() {
      this.decide("denied");
    },
  });
