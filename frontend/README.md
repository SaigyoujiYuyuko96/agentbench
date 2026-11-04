# AgentBench 前端

Vue 3 + TypeScript + Vite + Naive UI + Pinia。

```bash
npm ci
npm run dev      # http://localhost:5173，把 /api 代理到 127.0.0.1:8090
npm test         # vitest
npm run build    # vue-tsc 类型检查 + vite build
```

后端需要先起在 `127.0.0.1:8090`，代理配置见 `vite.config.ts`。

页面说明见仓库根目录的 [README](../README.md)。
