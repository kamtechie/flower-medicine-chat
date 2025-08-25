import path from "path";
import { defineConfig } from "vite";
import preact from "@preact/preset-vite";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [preact(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
      "@/components": path.resolve(__dirname, "src/components"),
      "@/lib": path.resolve(__dirname, "src/lib"),
      react: "preact/compat",
      "react-dom": "preact/compat",
    },
  },
  build: {
    outDir: "../static/preact",
    emptyOutDir: true,
  },
  server: {
    historyApiFallback: true,
    proxy: {
      "/ask": "http://localhost:8000",
      "/ingest": "http://localhost:8000",
      "/stats": "http://localhost:8000",
    },
  },
});
