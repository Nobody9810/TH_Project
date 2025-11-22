import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';

export default function AuthError() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [countdown, setCountdown] = useState(5);

  const error = searchParams.get('error');
  const errorDescription = searchParams.get('error_description');

  // 获取错误信息的友好显示
  const getErrorMessage = (error, description) => {
    const errorMessages = {
      'access_denied': '用户取消授权',
      'invalid_request': '请求参数错误',
      'unauthorized_client': '应用未获得授权',
      'unsupported_response_type': '不支持的响应类型',
      'invalid_scope': '请求的权限范围无效',
      'server_error': '服务器错误',
      'temporarily_unavailable': '服务暂时不可用',
      'missing_params': '缺少必要参数',
      'oauth_error': 'OAuth认证错误',
    };

    return errorMessages[error] || description || '未知错误';
  };

  // 倒计时自动跳转
  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          navigate('/login');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-pink-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
          {/* 错误图标 */}
          <div className="mx-auto w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mb-6">
            <svg className="w-10 h-10 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>

          {/* 标题 */}
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            登录失败
          </h1>

          {/* 错误信息 */}
          <div className="mb-6">
            <p className="text-red-600 font-medium mb-2">
              {getErrorMessage(error, errorDescription)}
            </p>
            
            {/* 详细错误信息（调试用） */}
            {error && (
              <div className="text-xs text-gray-500 bg-gray-50 p-3 rounded-lg">
                <p><strong>错误代码:</strong> {error}</p>
                {errorDescription && (
                  <p><strong>详细信息:</strong> {errorDescription}</p>
                )}
              </div>
            )}
          </div>

          {/* 建议操作 */}
          <div className="mb-6">
            <h3 className="font-medium text-gray-900 mb-3">建议解决方案：</h3>
            <ul className="text-sm text-gray-600 text-left space-y-2">
              <li className="flex items-start gap-2">
                <span className="text-blue-600">•</span>
                检查网络连接是否正常
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600">•</span>
                确认飞书应用权限设置正确
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600">•</span>
                尝试使用传统账号密码登录
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600">•</span>
                联系系统管理员获取帮助
              </li>
            </ul>
          </div>

          {/* 操作按钮 */}
          <div className="space-y-3">
            <button
              onClick={() => navigate('/login')}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-xl transition-colors duration-200"
            >
              返回登录页面
            </button>
            
            <button
              onClick={() => window.location.reload()}
              className="w-full border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium py-3 px-4 rounded-xl transition-colors duration-200"
            >
              重新尝试
            </button>
          </div>

          {/* 自动跳转提示 */}
          <p className="text-xs text-gray-500 mt-6">
            {countdown > 0 ? `${countdown} 秒后自动返回登录页面` : '正在跳转...'}
          </p>
        </div>
      </div>
    </div>
  );
}