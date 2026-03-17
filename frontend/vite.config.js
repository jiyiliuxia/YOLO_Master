import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  // Tauri expects a fixed port in dev mode
  server: {
    port: 5173,
    strictPort: true,
  },
  // Compile for the WebView2 engine (Chromium-based on Windows)
  build: {
    target: ['es2021', 'chrome100', 'safari13'],
    minify: !process.env.TAURI_DEBUG ? 'esbuild' : false,
    sourcemap: !!process.env.TAURI_DEBUG,
  },
  // Enable env var passthrough from Tauri CLI
  envPrefix: ['VITE_', 'TAURI_'],
  clearScreen: false,
})
