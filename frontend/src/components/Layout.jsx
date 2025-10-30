import React from "react";
import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Layout() {
  const { user, logout } = useAuth();
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-800 text-white flex flex-col">
        <div className="text-2xl font-bold p-4 border-b border-gray-700">Cherry Go Admin</div>
        <nav className="flex-1 p-4">
          <Link to="/dashboard" className="block py-2 hover:text-blue-300">Dashboard</Link>
          <Link to="/tours" className="block py-2 hover:text-blue-300">Tour Lines</Link>
          <Link to="/questions" className="block py-2 hover:text-blue-300">Questions</Link>
        </nav>
        <div className="p-4 border-t border-gray-700">
          <button onClick={logout} className="w-full bg-red-600 py-1 rounded">Logout</button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col">
        <header className="bg-white shadow p-4 flex justify-between items-center">
          <h1 className="text-xl font-semibold">Welcome, {user?.username || "User"}</h1>
        </header>
        <main className="p-6 flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
