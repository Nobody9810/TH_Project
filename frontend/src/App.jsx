import { BrowserRouter, Routes, Route,Navigate } from "react-router-dom";
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
         <Route path="/" element={<Login />} />
         <Route path="/" element={<Navigate to="/login" replace />} />
         <Route path="/login" element={<Login />} />
         <Route path="/dashboard" element={<Dashboard />} />
         <Route path="/materials" element={<Materials />} />
         <Route path="/supportticket" element={<SupportTicket />} />
         <Route path="/Profile" element={<Profile/>} />
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
      </Routes>
    </BrowserRouter>
  );
}

