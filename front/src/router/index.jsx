import { lazy } from "react";
import { Navigate } from "react-router-dom";
// 使用 lazy 动态导入组件
const Login = lazy(() => import("../pages/Login/Login"));
const Home = lazy(() => import("../pages/Home/Home"));

// 定义路由数组
const routes = [
  {
    path: "/login",
    element: <Login />, // 确保包含 element
  },
  {
    path: "/home",
    element: <Home />, // 确保包含 element
  },
  {
    path: "/", // 添加根路径路由
    element: <Navigate to="/login" replace />, // 重定向到 /login
  },
];

export default routes;
