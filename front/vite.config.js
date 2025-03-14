import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path"; // 导入 path 模块
// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"), // 配置 @ 别名
    },
  },
});
