// 文件路径: psychology-app-new/vite.config.js (最终通用版)
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    // 关键配置 1: 监听所有网络接口
    // 这使得局域网内的其他设备（如手机）可以通过你电脑的IP地址访问此开发服务器
    host: '0.0.0.0', 
    
    // 你可以为 App 前端指定一个端口，例如 5173 (Vite 默认)
    port: 5173,

    proxy: {
      // 关键配置 2: API 代理
      // 将所有以 /api 开头的请求都转发到本地运行的 FastAPI 后端
      '/api': {
        // [->] 核心通用化修改：目标始终是 localhost
        // 因为 Vite 开发服务器和 FastAPI 后端都运行在同一台机器上，
        // 使用 localhost 是最稳定、最高效的通信方式，不受你电脑IP地址变化的影响。
        target: 'http://localhost:8000',
        
        changeOrigin: true, // 必须设置为 true，以支持虚拟主机
        
        // 可选: 打印代理请求日志，方便调试
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log(`[Vite Proxy] 正在转发请求: ${req.method} ${req.url} -> ${options.target}${proxyReq.path}`);
          });
          proxy.on('error', (err, req, res) => {
            console.error('[Vite Proxy] 代理时发生错误:', err);
          });
        }
      },
      
      // 关键配置 3: 为 SSE (Server-Sent Events) 添加代理规则
      // 这对于实时报告状态更新至关重要
      '/sse': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: false, // SSE 不是 WebSocket，这里设置为 false
      }
    }
  }
});