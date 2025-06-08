// 文件路径: psychology-admin-frontend/vite.config.js (最终修复版)
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

export default defineConfig({
  // [+] 新增: base 配置项
  // 这个选项告诉 Vite，应用最终会被部署在服务器的 /admin/ 子目录下。
  // 所有静态资源的引用路径都会自动加上这个前缀。
  base: '/admin/', 

  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    host: '0.0.0.0', // 允许局域网访问
    port: 8081, // 后台前端的开发端口
    proxy: {
      // 将前端所有以 /api 开头的请求，代理到后端服务器
      // 例如，前端请求 /api/v1/users/me -> 后端 http://localhost:8000/api/v1/users/me
      '/api': {
        target: 'http://localhost:8000', // 您的 FastAPI 后端地址
        changeOrigin: true, // 必须设置为 true，用于支持虚拟主机
        // 不需要 rewrite，因为前端请求的路径和后端 API 路径的前半部分是匹配的
      },
      // [+] 为 SSE 添加代理规则
      '/sse': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: false, // SSE 不是 WebSocket
      }
    }
  },
  // [+] 新增: build 配置项
  // 指定构建输出目录为 'dist-admin'，以示区分
  build: {
    outDir: 'dist-admin',
  }
});