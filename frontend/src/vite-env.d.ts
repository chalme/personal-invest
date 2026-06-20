/// <reference types="vite/client" />

declare module '*.css';


declare global {
  interface Window {
    __APP_CONFIG__?: {
      apiBase?: string;
      frontendPublicUrl?: string;
    };
  }
}

export {};
