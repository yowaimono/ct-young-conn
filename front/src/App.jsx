import React, { Suspense } from 'react';
import { BrowserRouter, useRoutes } from 'react-router-dom';
import routes from '@/router/index';

// 使用 useRoutes 动态生成路由
const AppRoutes = () => {
  const element = useRoutes(routes);
  return element;
};

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div>Loading...</div>}>
        <AppRoutes />
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
