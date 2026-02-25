import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [tailwindcss(), react()],
  server: {
    port: 5174,
    // strictPort: true, ----> This would cause Vite to exit if the port is already in use, which can be inconvenient during development. By default, Vite will try the next available port if 5174 is taken.
  },
});
