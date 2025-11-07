import React, { useState } from "react";

const AvatarDisplay = ({ user, size = 40, showName = false, className = "" }) => {
  const [imageError, setImageError] = useState(false);

  const getInitials = (username) => {
    return username ? username.charAt(0).toUpperCase() : "U";
  };

  const getRoleText = (isStaff) => {
    return isStaff ? "系统管理员" : "用户";
  };

  const getAvatarUrl = (avatarPath) => {
    if (!avatarPath) return null;

    if (avatarPath.startsWith("http")) {
      return avatarPath;
    }

    if (avatarPath.startsWith("/")) {
      return `http://127.0.0.1:8000${avatarPath}`;
    }

    return `http://127.0.0.1:8000/media/${avatarPath}`;
  };

  const avatarUrl = user?.profile?.avatar ? getAvatarUrl(user.profile.avatar) : null;

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className="relative">
        {/* 显示图片头像（如果有且未报错） */}
        {avatarUrl && !imageError && (
          <img
            src={avatarUrl}
            alt={user?.username || "用户"}
            className="rounded-full object-cover border-2 border-white shadow"
            style={{ width: size, height: size }}
            onError={() => {
              console.error("头像加载失败:", avatarUrl);
              setImageError(true); // ✅ 使用 React 状态控制
            }}
          />
        )}

        {/* 备用首字母头像 */}
        {(!avatarUrl || imageError) && (
          <div
            className="rounded-full bg-gradient-to-br from-blue-500 to-blue-600 text-white flex items-center justify-center font-semibold border-2 border-white shadow"
            style={{
              width: size,
              height: size,
            }}
          >
            {getInitials(user?.username)}
          </div>
        )}
      </div>

      {showName && (
        <div className="text-left">
          <div className="text-sm font-medium text-gray-900">
            {(`${user?.first_name || ""} ${user?.last_name || ""}`.trim()) ||
              user?.username ||
              "用户"}
          </div>
          <div className="text-xs text-gray-500">{getRoleText(user?.is_staff)}</div>
        </div>
      )}
    </div>
  );
};

export default AvatarDisplay;
