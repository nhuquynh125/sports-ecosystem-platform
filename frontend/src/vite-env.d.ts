/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Absolute API base URL; defaults to "/api/v1" (proxied by Vite in development). */
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
