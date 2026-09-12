// https://nuxt.com/docs/api/configuration/nuxt-config
import tailwindcss from "@tailwindcss/vite";

const apiBaseUrl = process.env.NUXT_API_BASE_URL || "http://127.0.0.1:8000";

export default defineNuxtConfig({
  compatibilityDate: "2025-07-15",
  devtools: { enabled: false },
  devServer: { port: 5000 },

  // Browser calls same-origin /api/**, Nitro proxies it server-side to the
  // FastAPI backend. Avoids needing CORS config on the backend.
  routeRules: {
    "/api/**": { proxy: `${apiBaseUrl}/api/**` },
  },

  css: ["~/assets/css/tailwind.css"],
  vite: {
    plugins: [tailwindcss()],
  },

  components: [
    // shadcn-vue components: register unprefixed (<Button>, <Card>, ...).
    // pattern: "**/*.vue" skips the index.ts barrel (Nuxt would otherwise
    // also register that under the same component name).
    {
      path: "~/components/ui",
      pathPrefix: false,
      pattern: "**/*.vue",
    },
    // everything else (e.g. PhoneNumberForm.vue) keeps default behavior.
    {
      path: "~/components",
      pattern: "**/*.vue",
      ignore: ["ui/**"],
    },
  ],
});
