/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_AGENT_BACKEND?: string;
}

declare global {
  interface ImportMeta {
    readonly env: ImportMetaEnv;
  }
}
