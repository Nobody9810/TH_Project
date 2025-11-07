import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Materials from './pages/Materials';
import SupportTicket from './pages/SupportTicket';
import Profile from './pages/Profile';
import PrivateRoute from "./utils/PrivateRoute";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 公开路由 */}
        <Route path="/login" element={<Login />} />
        
        {/* 重定向根路径到登录页 */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        
        {/* 受保护的路由 */}
        <Route
          path="/dashboard"
          element={
            <PrivateRoute>
              <Dashboard />
            </PrivateRoute>
          }
        />
        <Route
          path="/materials"
          element={
            <PrivateRoute>
              <Materials />
            </PrivateRoute>
          }
        />
        <Route
          path="/supportticket"
          element={
            <PrivateRoute>
              <SupportTicket />
            </PrivateRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <PrivateRoute>
              <Profile />
            </PrivateRoute>
          }
        />
        
        {/* 404 页面重定向 */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}