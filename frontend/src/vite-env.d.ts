/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_PARTITION: string
  readonly VITE_SSO_HOST: string
  readonly VITE_AUTH_SERVICE_HOST: string
  readonly VITE_API_URL: string
  readonly VITE_DISABLE_SSO: string
  readonly VITE_API_PROXY_TARGET: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
