import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import axiosClient from "../api/axiosClient";
import AvatarDisplay from './AvatarDisplay';
import logo from "../assets/logo.jpg";
const Header = ({ title, subtitle = true, user: propUser }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(propUser);
  const [isOpen, setIsOpen] = useState(false);
  const [lastSync, setLastSync] = useState(null);

  // 如果没有传递用户信息，则获取用户信息
  useEffect(() => {
    if (!propUser) {
      const fetchUserInfo = async () => {
        try {
          const response = await axiosClient.get("/me/");
          setUser(response.data);
        } catch (err) {
          console.error("获取用户信息失败:", err);
          setUser({
            username: '用户',
            email: 'user@example.com',
            is_staff: false,
            last_login: new Date().toISOString()
          });
        }
      };
      fetchUserInfo();
    }
  }, [propUser]);

  // 更新最后同步时间
  useEffect(() => {
    setLastSync(new Date());
  }, [location]);

  // 处理退出登录
  const handleLogout = () => {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    navigate("/");
  };

  const handleProfile = () => {
    navigate("/profile");
  };

  const getRoleText = (isStaff) => {
    return isStaff ? '系统管理员' : '普通用户';
  };

  const formatDate = (iso) => {
    if (!iso) return "—";
    return new Date(iso).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 导航菜单项
  const navItems = [
    { path: '/dashboard', label: '仪表盘', icon: '📊' },
    { path: '/materials', label: '素材库', icon: '📁' },
    { path: '/supportticket', label: '知识库', icon: '🎫' },
  ];

  const isActivePath = (path) => {
    return location.pathname === path;
  };

  return (
    <header className="bg-white shadow-lg border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* 左侧：Logo和导航 */}
          <div className="flex items-center gap-8">
            {/* Logo */}
            <div
              className="flex items-center gap-3 cursor-pointer"
              onClick={() => navigate('/dashboard')}
            >
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg">
                <img
                  src={logo}
                  alt="Cherry Go Logo"
                  className="h-10 w-10 rounded-md shadow-sm"
                />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Trippal Holiday</h1>
                <p className="text-xs text-gray-600">素材库 & 知识库管理系统</p>
              </div>
            </div>

            {/* 导航菜单 */}
            <nav className="hidden md:flex items-center gap-6">
              {navItems.map((item) => (
                <button
                  key={item.path}
                  onClick={() => navigate(item.path)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-300 ${isActivePath(item.path)
                      ? 'bg-gradient-to-r from-blue-50 to-blue-100 text-blue-700 border border-blue-200'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                >
                  <span className="text-lg">{item.icon}</span>
                  {item.label}
                </button>
              ))}
            </nav>
          </div>

          {/* 右侧：操作按钮和用户信息 */}
          <div className="flex items-center gap-4">
            {/* 最后更新时间 */}
            <div className="text-sm text-gray-500 hidden lg:block">
              最后更新: {lastSync ? formatDate(lastSync) : '—'}
            </div>



            {/* 用户头像和下拉菜单 */}
            <div className="relative">
              <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-100 transition-colors duration-200"
              >
                <AvatarDisplay
                  user={user}
                  size={40}
                  showName={true}
                  className="hidden lg:flex"
                />
                <svg
                  className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* 下拉菜单 */}
              {isOpen && (
                <>
                  {/* 背景遮罩 */}
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setIsOpen(false)}
                  ></div>

                  {/* 菜单内容 */}
                  <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-2xl shadow-2xl border border-gray-200 z-50 overflow-hidden">
                    {/* 用户信息头部 */}
                    <div className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 border-b border-blue-200">
                      <div className="flex items-center gap-4">
                <AvatarDisplay
                  user={user}
                  size={80}
                />

                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900 text-lg">{user?.first_name + user.last_name || user.username}</h3>
                          <p className="text-sm text-gray-600 mt-1">{user?.email || '暂无邮箱'}</p>
                          <div className="flex items-center gap-2 mt-2">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${user?.is_staff
                                ? 'bg-emerald-100 text-emerald-800'
                                : 'bg-blue-100 text-blue-800'
                              }`}>
                              {getRoleText(user?.is_staff)}
                            </span>
                            <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-medium">
                              在线
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* 菜单选项 */}
                    <div className="p-2">
                      {/* 个人资料查看 */}
                      <button
                        onClick={() => {
                          handleProfile();
                          setIsOpen(false);
                        }}
                        className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors text-left"
                      >
                        <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center text-gray-600">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">个人资料</div>
                          <div className="text-sm text-gray-500">查看和编辑账户信息</div>
                        </div>
                      </button>

                      {/* 刷新数据 */}
                      <button
                        onClick={() => {
                          window.location.reload();
                          setIsOpen(false);
                        }}
                        className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors text-left mt-1"
                      >
                        <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center text-green-600">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">刷新数据</div>
                          <div className="text-sm text-gray-500">更新最新信息</div>
                        </div>
                      </button>

                      {/* 退出登录 */}
                      <button
                        onClick={() => {
                          handleLogout();
                          setIsOpen(false);
                        }}
                        className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-red-50 transition-colors text-left mt-1"
                      >
                        <div className="w-10 h-10 bg-red-100 rounded-xl flex items-center justify-center text-red-600">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                          </svg>
                        </div>
                        <div>
                          <div className="font-medium text-gray-500">退出登录</div>
                          <div className="text-sm text-gray-500">安全退出系统</div>
                        </div>
                      </button>
                    </div>

                    {/* 底部信息 */}
                    <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
                      <div className="text-xs text-gray-500">
                        <div>最后登录: {user?.last_login ? formatDate(user.last_login) : '未知'}</div>
                        <div className="mt-1">系统版本: v1.0.0</div>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* 页面标题区域 */}
        {(title || subtitle) && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                {title && <h1 className="text-2xl font-bold text-gray-900">{title}</h1>}
                {subtitle && <p className="text-sm text-gray-600 mt-1">{subtitle}</p>}
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;