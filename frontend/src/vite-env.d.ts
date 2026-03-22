/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_APP_TITLE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// 扩展 Vue Router Meta
declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    permission?: string
    roles?: string[]
  }
}
