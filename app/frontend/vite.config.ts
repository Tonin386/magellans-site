import { resolve } from "node:path";

import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

// Les fichiers générés sont servis par Django sous /static/vite/
// (voir STATICFILES_DIRS et DJANGO_VITE dans magellans/settings.py).
export default defineConfig({
  base: "/static/vite/",
  plugins: [tailwindcss()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
    manifest: true,
    target: "es2022",
    sourcemap: false,
    rolldownOptions: {
      input: {
        main: resolve(import.meta.dirname, "src/main.ts"),
      },
    },
  },
  server: {
    host: "localhost",
    port: 5173,
    strictPort: true,
    origin: "http://localhost:5173",
    cors: { origin: ["http://localhost:8000", "http://127.0.0.1:8000"] },
  },
});
