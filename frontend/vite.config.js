import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

function bypassHtmlNav(req) {
  // Browser page navigations include 'text/html' in Accept.
  // API fetch() calls use 'application/json'. Only proxy the latter.
  if (req.headers.accept && req.headers.accept.includes('text/html')) {
    return req.url  // return the URL to serve it from Vite instead
  }
}

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api':       { target: 'http://localhost:8000', bypass: bypassHtmlNav },
      '/auth':      { target: 'http://localhost:8000', bypass: bypassHtmlNav },
      '/student':   { target: 'http://localhost:8000', bypass: bypassHtmlNav },
      '/recruiter': { target: 'http://localhost:8000', bypass: bypassHtmlNav },
    }
  }
})
