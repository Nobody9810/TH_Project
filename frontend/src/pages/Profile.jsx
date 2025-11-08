import React, { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import axiosClient from "../api/axiosClient";
import AvatarDisplay from '../components/AvatarDisplay';
import Header from '../components/Header'; // 导入统一的Header
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

// 头像上传组件
const AvatarUpload = ({ user, onAvatarUpdate, onError, size = 120 }) => {
  const fileInputRef = useRef(null);
  const [uploading, setUploading] = useState(false);

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // 验证文件类型
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
    if (!allowedTypes.includes(file.type)) {
      onError?.({ type: "error", text: '只支持 JPEG、PNG 和 GIF 格式的图片' });
      return;
    }

    // 验证文件大小 (2MB)
    if (file.size > 2 * 1024 * 1024) {
      onError?.({ type: "error", text: '头像文件不能超过 2MB' });
      return;
    }

    setUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('avatars', file);
      
      const uploadClient = axios.create({
        baseURL: 'https://api.trippalholiday.my/api',
      });

      // 添加 token 拦截器
      uploadClient.interceptors.request.use((config) => {
        const token = localStorage.getItem('access');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      });

      const response = await uploadClient.patch('me/avatar/', formData);

      console.log('上传成功:', response.data);
      onAvatarUpdate?.(response.data);
      onError?.({ type: "success", text: "头像上传成功！" });
    } finally {
      setUploading(false);
      // 清空文件输入
      event.target.value = '';
    }
  };

  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="text-center">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        accept="image/jpeg,image/png,image/gif"
        className="hidden"
      />
      
      <div className="relative inline-block">
        {/* 使用 AvatarDisplay 组件显示头像 */}
        <div onClick={handleAvatarClick} className="cursor-pointer">
          <AvatarDisplay user={user} size={size} />
        </div>
        
        {/* 上传覆盖层 */}
        <div 
          className="absolute inset-0 bg-black bg-opacity-40 rounded-2xl flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity cursor-pointer"
          onClick={handleAvatarClick}
        >
          {uploading ? (
            <div className="text-white">
              <LoadingSpinner size="small" />
              <p className="text-sm mt-2">上传中...</p>
            </div>
          ) : (
            <div className="text-white text-center">
              <svg className="w-8 h-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <p className="text-sm mt-1">更换头像</p>
            </div>
          )}
        </div>
      </div>
      
      <p className="text-sm text-gray-500 mt-2">
        点击头像上传新图片
        <br />
        <span className="text-xs">支持 JPG、PNG、GIF，最大 2MB</span>
      </p>
    </div>
  );
};

// 状态消息组件
const StatusMessage = ({ type, text, onClose }) => {
  const bgColors = {
    success: "bg-gradient-to-r from-green-50 to-emerald-50 border-emerald-200 text-emerald-800",
    error: "bg-gradient-to-r from-red-50 to-orange-50 border-red-200 text-red-800",
    info: "bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200 text-blue-800"
  };

  return (
    <div className={`mb-6 p-4 rounded-xl border ${bgColors[type]} flex items-center justify-between`}>
      <div className="flex items-center gap-3">
        {type === 'success' && (
          <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )}
        {type === 'error' && (
          <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )}
        <span className="font-medium">{text}</span>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
};

export default function Profile() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [form, setForm] = useState({
    username: "",
    email: "",
    first_name: "",
    last_name: "",
  });
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    async function fetchProfile() {
      try {
        const res = await axiosClient.get("me/");
        if (!mountedRef.current) return;
        
        console.log('用户数据:', res.data);
        console.log('头像路径:', res.data.profile?.avatar);
        
        setUser(res.data);
        setForm({
          username: res.data.username || "",
          email: res.data.email || "",
          first_name: res.data.first_name || "",
          last_name: res.data.last_name || "",
        });
      } catch (err) {
        console.error("获取用户资料失败:", err);
        if (!mountedRef.current) return;
        const serverMsg =
          err?.response?.data && typeof err.response.data === "object"
            ? Object.values(err.response.data).flat().join(" ")
            : err?.response?.data || err?.message || "无法获取用户资料，请稍后重试。";
        setStatus({ type: "error", text: serverMsg });
      } finally {
        if (!mountedRef.current) return;
        setLoading(false);
      }
    }
    fetchProfile();
    return () => {
      mountedRef.current = false;
    };
  }, []);

  function validateEmail(email) {
    if (!email) return false;
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  }

  async function handleSave(e) {
    e.preventDefault();
    setStatus(null);

    if (!form.username.trim()) {
      setStatus({ type: "error", text: "用户名不能为空。" });
      return;
    }
    if (!validateEmail(form.email)) {
      setStatus({ type: "error", text: "请输入有效的邮箱地址。" });
      return;
    }

    setSaving(true);
    try {
      const payload = {
        username: form.username.trim(),
        email: form.email.trim(),
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
      };

      const res = await axiosClient.patch("me/", payload);

      setUser(res.data);
      setEditing(false);
      setStatus({ type: "success", text: "个人资料已成功更新！" });
    } catch (err) {
      console.error("保存用户资料失败:", err);

      if (err?.response) {
        const statusCode = err.response.status;
        const data = err.response.data;
        if (statusCode === 401) {
          setStatus({ type: "error", text: "未登录或权限已过期，请重新登录。" });
          localStorage.removeItem("access");
          setTimeout(() => navigate("/"), 1200);
        } else {
          const msg =
            typeof data === "string"
              ? data
              : data && typeof data === "object"
              ? Object.values(data).flat().join(" ")
              : err.message;
          setStatus({ type: "error", text: msg || "保存失败，请稍后重试。" });
        }
      } else {
        setStatus({ type: "error", text: err?.message || "保存失败：网络错误。" });
      }
    } finally {
      setSaving(false);
    }
  }

  const handleCancel = () => {
    setForm({
      username: user.username || "",
      email: user.email || "",
      first_name: user.first_name || "",
      last_name: user.last_name || "",
    });
    setEditing(false);
    setStatus(null);
  };

  // 头像更新后的回调函数
  const handleAvatarUpdate = (updatedUser) => {
    console.log('头像更新后的用户数据:', updatedUser);
    setUser(updatedUser);
  };

  // 头像上传错误处理
  const handleAvatarError = (errorStatus) => {
    setStatus(errorStatus);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50/60 to-indigo-100/60 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="large" />
          <p className="mt-4 text-gray-600">加载个人资料...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50/60 to-indigo-100/60">
      {/* 头部导航 */}
      <Header 
        title="个人资料"
        subtitle="管理您的账户信息和偏好设置"
        showNewTicketButton={false}
        user={user}
      />

       <main className="max-w-4xl mx-auto px-6 py-8">
        {status && (
          <StatusMessage 
            type={status.type} 
            text={status.text} 
            onClose={() => setStatus(null)} 
          />
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 左侧：头像和基本信息 */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
              <div className="text-center">
                {/* 使用 AvatarUpload 组件替代原来的头像显示 */}
                <AvatarUpload 
                  user={user} 
                  onAvatarUpdate={handleAvatarUpdate}
                  onError={handleAvatarError}
                  size={120}
                />
                
                <h2 className="text-xl font-bold text-gray-900 mt-4">
                  {`${form.first_name} ${form.last_name}`.trim() || form.username}
                </h2>
                <p className="text-gray-600 mt-1">{form.email}</p>
                
                <div className="mt-4 space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">角色</span>
                    <span className={`font-medium px-2 py-1 rounded-full ${
                      user?.is_staff 
                        ? 'bg-emerald-100 text-emerald-800' 
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {user?.is_staff ? '系统管理员' : '普通用户'}
                    </span>
                  </div>
                  
                  {user?.last_login && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">最后登录</span>
                      <span className="text-gray-900 font-medium">
                        {new Date(user.last_login).toLocaleDateString('zh-CN')}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 操作按钮 */}
            <div className="mt-6 space-y-3">
              {!editing ? (
                <button
                  onClick={() => {
                    setStatus(null);
                    setEditing(true);
                  }}
                  className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl font-semibold hover:shadow-lg transform hover:scale-105 transition-all duration-300 flex items-center justify-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  编辑资料
                </button>
              ) : (
                <button
                  onClick={handleCancel}
                  className="w-full px-6 py-3 bg-white border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors flex items-center justify-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  取消编辑
                </button>
              )}


            </div>
          </div>

          {/* 右侧：表单 */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-white">
                <h2 className="text-lg font-semibold text-gray-900">
                  {editing ? "编辑个人资料" : "个人资料信息"}
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  {editing ? "更新您的个人信息" : "查看您的账户详细信息"}
                </p>
              </div>

              <form onSubmit={handleSave} className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      用户名 <span className="text-red-500">*</span>
                    </label>
                    <input
                      value={form.username}
                      onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
                      disabled={!editing}
                      className={`w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                        editing ? "bg-white" : "bg-gray-50"
                      }`}
                      placeholder="请输入用户名"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      邮箱地址 <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="email"
                      value={form.email}
                      onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                      disabled={!editing}
                      className={`w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                        editing ? "bg-white" : "bg-gray-50"
                      }`}
                      placeholder="请输入邮箱地址"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">名字</label>
                    <input
                      value={form.first_name}
                      onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))}
                      disabled={!editing}
                      className={`w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                        editing ? "bg-white" : "bg-gray-50"
                      }`}
                      placeholder="请输入名字"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">姓氏</label>
                    <input
                      value={form.last_name}
                      onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))}
                      disabled={!editing}
                      className={`w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                        editing ? "bg-white" : "bg-gray-50"
                      }`}
                      placeholder="请输入姓氏"
                    />
                  </div>
                </div>

                {editing && (
                  <div className="mt-8 flex justify-end">
                    <button
                      type="submit"
                      disabled={saving}
                      className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl font-semibold hover:shadow-lg transform hover:scale-105 transition-all duration-300 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {saving ? (
                        <>
                          <LoadingSpinner size="small" />
                          保存中...
                        </>
                      ) : (
                        <>
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          保存更改
                        </>
                      )}
                    </button>
                  </div>
                )}
              </form>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
