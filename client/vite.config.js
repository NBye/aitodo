import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
    plugins: [vue()],
    server: {
        port: 6200,
        host: '0.0.0.0',
    },
    css: {
        preprocessorOptions: {
            scss: {
                api: 'modern-compiler' // or "modern"
            }
        }
    },
    optimizeDeps: {
        include: ['vue-clipboard3']  // 确保 vue-clipboard3 被 Vite 正确优化
    }
})
