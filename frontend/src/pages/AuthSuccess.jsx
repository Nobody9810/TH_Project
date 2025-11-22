import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';

export default function AuthSuccess() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [isProcessing, setIsProcessing] = useState(true);

  useEffect(() => {
    const processAuth = async () => {
      try {
        const access = searchParams.get('access');
        const refresh = searchParams.get('refresh');
        const authType = searchParams.get('auth_type');
        const userId = searchParams.get('user_id');
        const username = searchParams.get('username');

        if (access && refresh) {
          // 保存tokens到localStorage
          localStorage.setItem('access', access);
          localStorage.setItem('refresh', refresh);
          
          // 可选：保存用户信息
          localStorage.setItem('user_info', JSON.stringify({
            user_id: userId,
            username: username,
            auth_type: authType,
            login_time: new Date().toISOString()
          }));

          // 短暂延迟后跳转到仪表板
          setTimeout(() => {
            window.location.href = '/dashboard';
          }, 1500);
        } else {
          throw new Error('缺少认证信息');
        }
      } catch (error) {
        console.error('处理认证失败:', error);
        // 跳转到登录页面
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      }
    };

    processAuth();
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
          {/* 成功图标 */}
          <div className="mx-auto w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-6">
            <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>

          {/* 标题 */}
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            登录成功！
          </h1>

          {/* 描述 */}
          <p className="text-gray-600 mb-6">
            正在为您跳转到系统首页...
          </p>

          {/* 加载动画 */}
          <div className="flex justify-center">
            <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          </div>

          {/* 用户信息 */}
          {searchParams.get('username') && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-700">
                欢迎回来，<span className="font-medium">{searchParams.get('username')}</span>
              </p>
              <p className="text-xs text-gray-500 mt-1">
                登录方式: {searchParams.get('auth_type') === 'enterprise' ? '飞书企业账号' : '飞书个人账号'}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}