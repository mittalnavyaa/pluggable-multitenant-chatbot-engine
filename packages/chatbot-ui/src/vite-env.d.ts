// packages/chatbot-ui/src/vite-env.d.ts
/// <reference types="vite/client" />

declare module '*?raw' {
  const content: string;
  export default content;
}
