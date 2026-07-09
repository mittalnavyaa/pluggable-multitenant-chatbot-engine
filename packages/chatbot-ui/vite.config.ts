import { defineConfig } from 'vite';
import cssInjectedByJsPlugin from 'vite-plugin-css-injected-by-js';

export default defineConfig({
  plugins: [cssInjectedByJsPlugin()],
  build: {
    lib: {
      entry: 'src/index.ts',
      name: 'EnvoyChatbotWidget',
      fileName: () => 'chatbot-ui.js',
      formats: ['umd']
    },
    rollupOptions: {
      output: {
        extend: true
      }
    }
  }
});
