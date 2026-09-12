// https://nuxt.com/docs/api/configuration/nuxt-config
const apiBaseUrl = process.env.NUXT_API_BASE_URL || 'http://127.0.0.1:8000'

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  // Browser calls same-origin /api/**, Nitro proxies it server-side to the
  // FastAPI backend. Avoids needing CORS config on the backend.
  routeRules: {
    '/api/**': { proxy: `${apiBaseUrl}/api/**` }
  }
})
