import { fileURLToPath, URL } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, type Plugin } from 'vite'
import { PRODUCT_NAME, PRODUCT_TAGLINE, STORAGE_PREFIX } from './src/config/product.ts'

const API_ORIGIN = 'https://mustaqbal-ai.replit.app'

// Fills %PRODUCT_NAME% etc. (and %BASE_URL%) in index.html from the product constant and config.
function productHtml(): Plugin {
  const values: Record<string, string> = { PRODUCT_NAME, PRODUCT_TAGLINE, STORAGE_PREFIX, BASE_URL: '/' }
  return {
    name: 'product-html',
    configResolved: (config) => {
      values.BASE_URL = config.base
    },
    transformIndexHtml: (html) => html.replace(/%(PRODUCT_NAME|PRODUCT_TAGLINE|STORAGE_PREFIX|BASE_URL)%/g, (_, key: string) => values[key]),
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss(), productHtml()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  // /api goes to the backend in dev and preview, so the browser sees one origin (no CORS)
  // and a build served from the backend's own domain later needs no changes.
  server: { port: 5173, strictPort: true, proxy: { '/api': { target: API_ORIGIN, changeOrigin: true, secure: true } } },
  preview: { proxy: { '/api': { target: API_ORIGIN, changeOrigin: true, secure: true } } },
})
