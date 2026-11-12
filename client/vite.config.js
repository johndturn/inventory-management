import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          // <search> is a native HTML landmark element (wraps the filter form),
          // not a Vue component; without this Vue warns it can't resolve it.
          isCustomElement: (tag) => tag === 'search'
        }
      }
    })
  ],
  server: {
    port: 3000
  }
})
