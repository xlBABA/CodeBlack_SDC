/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** API base, relative so the same build works behind the backend's domain. Default /api/v1. */
  readonly VITE_API_BASE_URL?: string
  /** "true" serves bundled fixtures instead of calling the API (offline fallback). */
  readonly VITE_USE_MOCKS?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
