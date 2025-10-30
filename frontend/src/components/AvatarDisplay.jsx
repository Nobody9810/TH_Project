import React from "react";


const AvatarDisplay = ({ user, size = 40, showName = false, className = "" }) => {
  const getInitials = (username) => {
    return username ? username.charAt(0).toUpperCase() : 'U';
  };

  const getRoleText = (isStaff) => {
    return isStaff ? '系统管理员' : '普通用户';
  };

  // 获取完整的头像 URL
  const getAvatarUrl = (avatarPath) => {
    if (!avatarPath) return null;
    
    // 如果已经是完整 URL，直接返回
    if (avatarPath.startsWith('http')) {
      return avatarPath;
    }
    
    // 如果是相对路径，构建完整 URL
    if (avatarPath.startsWith('/')) {
      return `http://127.0.0.1:8000${avatarPath}`;
    }
    
    // 其他情况，假设是相对于 media 的路径
    return `http://127.0.0.1:8000/media/${avatarPath}`;
  };

  const avatarUrl = user?.profile?.avatar ? getAvatarUrl(user.profile.avatar) : null;

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className="relative">
        {avatarUrl ? (
          <img
            src={avatarUrl}
            alt={user?.username || '用户'}
            className="rounded-full object-cover border-2 border-white shadow"
            style={{ width: size, height: size }}
            onError={(e) => {
              // 如果图片加载失败，回退到首字母头像
              console.error('头像加载失败:', avatarUrl);
              e.target.style.display = 'none';
              // 显示备用的首字母头像
              const fallback = document.getElementById(`avatar-fallback-${user?.id}`);
              if (fallback) fallback.style.display = 'flex';
            }}
          />
        ) : null}
        
        {/* 首字母头像（备用） */}
        <div
          id={`avatar-fallback-${user?.id}`}
          className="rounded-full bg-gradient-to-br from-blue-500 to-blue-600 text-white flex items-center justify-center font-semibold border-2 border-white shadow"
          style={{ 
            width: size, 
            height: size,
            display: avatarUrl ? 'none' : 'flex'
          }}
        >
          {getInitials(user?.username)}
        </div>
      </div>
      
      {showName && (
        <div className="text-left">
          <div className="text-sm font-medium text-gray-900">{user?.username || '用户'}</div>
          <div className="text-xs text-gray-500">{getRoleText(user?.is_staff)}</div>
        </div>
      )}
    </div>
  );
};

export default AvatarDisplay;