import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axiosClient from "../api/axiosClient";
import Header from '../components/Header'; // 导入统一的Header

const CATEGORY_CHOICES = [
  { value: "faq", label: "常见问题" },
  { value: "ticket", label: "订票问题" },
  { value: "car", label: "汽车问题" },
  { value: "incident", label: "意外情况" },
];

function formatNumber(n) {
  if (n == null) return "0";
  return Number(n).toLocaleString();
}

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// 专业加载指示器
const LoadingSpinner = ({ size = "medium" }) => {
  const sizeClasses = {
    small: "h-4 w-4",
    medium: "h-6 w-6",
    large: "h-8 w-8"
  };

  return (
    <div className={`animate-spin rounded-full border-2 border-gray-300 border-t-blue-600 ${sizeClasses[size]}`}></div>
  );
};

// 专业统计卡片组件
const StatCard = ({ title, value, description, icon, color = "blue", onClick, loading = false }) => {
  const colorClasses = {
    blue: "from-blue-500 to-blue-600",
    purple: "from-purple-500 to-purple-600",
    orange: "from-orange-500 to-orange-600",
    green: "from-green-500 to-green-600"
  };

  return (
    <div 
      onClick={onClick}
      className={`bg-gradient-to-br ${colorClasses[color]} rounded-2xl p-6 text-white cursor-pointer transform transition-all duration-300 hover:scale-105 hover:shadow-2xl`}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-blue-100 text-sm font-medium mb-1">{title}</p>
          <div className="text-3xl font-bold mb-2">
            {loading ? <LoadingSpinner size="medium" /> : value}
          </div>
          <p className="text-blue-100 text-xs opacity-90">{description}</p>
        </div>
        <div className="text-3xl opacity-90">
          {icon}
        </div>
      </div>
    </div>
  );
};

// 专业列表项组件
const ListItem = ({ title, subtitle, meta, status, onClick, type = "default" }) => {
  const statusColors = {
    answered: "bg-gradient-to-r from-green-100 to-green-200 text-green-800",
    unanswered: "bg-gradient-to-r from-orange-100 to-orange-200 text-orange-800",
    default: "bg-gray-100 text-gray-800"
  };

  return (
    <div 
      onClick={onClick}
      className="group p-4 rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-lg transition-all duration-300 cursor-pointer bg-white transform hover:-translate-y-1"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-gray-900 truncate group-hover:text-blue-600 transition-colors">
            {title}
          </h3>
          <p className="text-xs text-gray-600 mt-1 line-clamp-2">{subtitle}</p>
          <div className="flex items-center gap-3 mt-2">
            {status && (
              <span className={`text-xs font-medium px-2 py-1 rounded-full ${statusColors[status]}`}>
                {status === 'answered' ? '✅ 已处理' : '⏳ 待处理'}
              </span>
            )}
            <span className="text-xs text-gray-500">{meta}</span>
          </div>
        </div>
        <div className="ml-4 flex-shrink-0">
          <svg className="w-5 h-5 text-gray-400 group-hover:text-blue-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>
    </div>
  );
};

// 专业分区组件
const Section = ({ title, action, children, className = "" }) => (
  <div className={`bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden ${className}`}>
    <div className="px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-white flex items-center justify-between">
      <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
      {action && (
        <button 
          onClick={action.onClick}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1 transition-colors"
        >
          {action.label}
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      )}
    </div>
    <div className="p-6">
      {children}
    </div>
  </div>
);

const UserProfile = ({ user, onLogout, onProfile }) => {
  const [isOpen, setIsOpen] = useState(false);

  const getRoleText = (isStaff) => {
    return isStaff ? '系统管理员' : '普通用户';
  };

  return (
    <div className="relative">
      {/* 用户头像按钮 */}
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
                <AvatarDisplay user={user} size={64} />
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 text-lg">{user?.username || '用户'}</h3>
                  <p className="text-sm text-gray-600 mt-1">{user?.email || '暂无邮箱'}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      user?.is_staff 
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
              {/* 个人资料查看 - 跳转到 /profile */}
              <button
                onClick={() => {
                  onProfile?.();
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

              {/* 添加快捷操作 */}
              <button
                onClick={() => {
                  // 刷新数据功能
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

              <button
                onClick={() => {
                  onLogout?.();
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
  );
};

export default function ProfessionalDashboard() {
  const navigate = useNavigate();
  
  const [overview, setOverview] = useState({
    materialCount: 0,
    totalTicketCount: 0,
    unansweredTicketCount: 0,
  });
  const [recents, setRecents] = useState({
    materials: [],
    supportticket: [],
  });

  const [lastSync, setLastSync] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // 用户信息状态
  const [user, setUser] = useState(null);
  const [userLoading, setUserLoading] = useState(true);

  // 获取用户信息
  const fetchUserInfo = async () => {
    try {
      setUserLoading(true);
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
    } finally {
      setUserLoading(false);
    }
  };

  // 数据获取逻辑
  const fetchOverview = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [allMaterialsRes, allTicketsRes, unansweredTicketsRes, recentTicketsRes, recentMaterialsRes] = await Promise.all([
        axiosClient.get("materials/"),
        axiosClient.get("supportticket/?page_size=1&status=all"),
        axiosClient.get("supportticket/?page_size=1&status=unanswered"),
        axiosClient.get("supportticket/?page_size=5&status=all"),
        axiosClient.get("materials/?page_size=5"),
      ]);

      let materialCount = 0;
      if (allMaterialsRes.data && Array.isArray(allMaterialsRes.data.results)) {
        materialCount = allMaterialsRes.data.count || allMaterialsRes.data.results.length;
      } else if (Array.isArray(allMaterialsRes.data)) {
        materialCount = allMaterialsRes.data.length;
      }

      setOverview({
        materialCount: materialCount,
        totalTicketCount: allTicketsRes.data?.count || 0,
        unansweredTicketCount: unansweredTicketsRes.data?.count || 0,
      });

      setRecents({
        materials: recentMaterialsRes.data?.results || recentMaterialsRes.data || [],
        supportticket: recentTicketsRes.data?.results || [],
      });

      setLastSync(new Date());

    } catch (err) {
      console.error("获取概览数据失败:", err);
      setError("无法加载概览数据，请检查网络或权限。");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
    fetchUserInfo();
    const interval = setInterval(fetchOverview, 5 * 60 * 1000); 
    return () => clearInterval(interval);
  }, []);

  // 处理退出登录
  const handleLogout = () => {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    navigate("/");
  };

  const handleProfile = () => {
    navigate("/profile");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50/60 to-indigo-100/60">
      {/* 头部导航 */}
      <Header 
        user={user}
      />
    
      {/* 主要内容 */}
     <main className="max-w-7xl mx-auto px-6 py-8">
        {/* 统计卡片网格 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatCard
            title="素材库总量"
            value={formatNumber(overview.materialCount)}
            description="管理的全部素材资源"
            icon="📁"
            color="blue"
            loading={isLoading}
            onClick={() => navigate('/materials')}
          />
          <StatCard
            title="全部问题"
            value={formatNumber(overview.totalTicketCount)}
            description="所有用户提交的问题"
            icon="📋"
            color="purple"
            loading={isLoading}
            onClick={() => navigate('/supportticket')}
          />
          <StatCard
            title="待处理问题"
            value={formatNumber(overview.unansweredTicketCount)}
            description="需要立即关注的问题"
            icon="⚠️"
            color="orange"
            loading={isLoading}
            onClick={() => navigate('/supportticket?status=unanswered')}
          />
        </div>

        {/* 内容区域 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 最新素材 */}
          <Section
            title="最新素材"
            action={{
              label: "查看全部",
              onClick: () => navigate('/materials')
            }}
          >
            <div className="space-y-4">
              {recents.materials && recents.materials.length > 0 ? (
                recents.materials.map(material => (
                  <ListItem
                    key={material.id}
                    title={material.title}
                    subtitle={material.description || "暂无描述"}
                    meta={`${formatDate(material.created_at)} • ${material.material_type_display || material.material_type}`}
                    onClick={() => navigate(`/materials/${material.id}`)}
                  />
                ))
              ) : (
                <div className="text-center py-8 text-gray-500">
                  {isLoading ? (
                    <div className="flex items-center justify-center gap-2">
                      <LoadingSpinner size="small" />
                      加载中...
                    </div>
                  ) : (
                    "暂无素材数据"
                  )}
                </div>
              )}
            </div>
          </Section>

          {/* 最新问题 */}
          <Section
            title="最新问题"
            action={{
              label: "查看全部",
              onClick: () => navigate('/supportticket')
            }}
          >
            <div className="space-y-4">
              {recents.supportticket && recents.supportticket.length > 0 ? (
                recents.supportticket.map(ticket => (
                  <ListItem
                    key={ticket.id}
                    title={ticket.question_text}
                    subtitle={ticket.category_display || getCategoryLabel(ticket.category)}
                    meta={formatDate(ticket.created_at)}
                    status={ticket.is_answered ? 'answered' : 'unanswered'}
                    onClick={() => navigate(`/supportticket/${ticket.id}`)}
                  />
                ))
              ) : (
                <div className="text-center py-8 text-gray-500">
                  {isLoading ? (
                    <div className="flex items-center justify-center gap-2">
                      <LoadingSpinner size="small" />
                      加载中...
                    </div>
                  ) : (
                    "暂无问题数据"
                  )}
                </div>
              )}
            </div>
          </Section>
        </div>
      </main>
    </div>
  );
}

// 辅助函数
function getCategoryLabel(value) {
  return CATEGORY_CHOICES.find(c => c.value === value)?.label || '未知';
}