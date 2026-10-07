import { defineComponent } from "./define";

/**
 * Zone de signature manuscrite (contrat de prêt).
 * La bibliothèque signature_pad n'est téléchargée que sur la page du contrat.
 */
export const signatureField = () =>
  defineComponent({
    empty: true,
    pad: null as null | { clear(): void; isEmpty(): boolean; toDataURL(type?: string): string; addEventListener(name: string, cb: () => void): void; off(): void; on(): void },
    async init() {
      const { default: SignaturePad } = await import("signature_pad");
      const canvas = this.$refs.canvas as HTMLCanvasElement;
      const pad = new SignaturePad(canvas, { penColor: "#14100d", minWidth: 0.8, maxWidth: 2.4 });
      this.pad = pad;
      const resize = () => {
        const ratio = Math.max(window.devicePixelRatio || 1, 1);
        const data = pad.isEmpty() ? null : pad.toData();
        canvas.width = canvas.offsetWidth * ratio;
        canvas.height = canvas.offsetHeight * ratio;
        canvas.getContext("2d")?.scale(ratio, ratio);
        pad.clear();
        if (data) pad.fromData(data);
      };
      resize();
      window.addEventListener("resize", resize);
      pad.addEventListener("endStroke", () => this.capture());
    },
    capture() {
      if (!this.pad) return;
      this.empty = this.pad.isEmpty();
      (this.$refs.input as HTMLInputElement).value = this.empty ? "" : this.pad.toDataURL("image/png");
    },
    clear() {
      this.pad?.clear();
      this.capture();
    },
  });
