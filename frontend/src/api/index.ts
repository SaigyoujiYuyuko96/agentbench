import axios from "axios";

// 默认走相对路径，由 Vite dev server 的 proxy（见 vite.config.ts）转发到后端。
// 部署到别处时用 VITE_API_BASE_URL 覆盖，例如 https://api.example.com
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "",
});

export default api;
