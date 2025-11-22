"""
Lark (飞书) 登录相关视图 - 简化版
使用统一配置支持企业用户和个人用户登录
"""
import logging
from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from urllib.parse import urlencode

from .client import lark_oauth_client, LarkOAuthError

logger = logging.getLogger(__name__)


class LarkAuthInitiateView(APIView):
    """
    发起Lark登录授权
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        获取Lark授权URL
        """
        try:
            # 检查配置
            if not settings.LARK_APP_ID or not settings.LARK_APP_SECRET:
                return Response(
                    {"error": "Lark应用配置未完成，请联系管理员"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # 生成state参数
            state = lark_oauth_client.generate_state()
            
            # 获取授权URL
            auth_url = lark_oauth_client.get_auth_url(state)
            
            logger.info("发起Lark登录授权")
            return Response({
                "auth_url": auth_url,
                "state": state
            })
            
        except Exception as e:
            logger.error(f"发起Lark授权失败: {str(e)}")
            return Response(
                {"error": f"授权发起失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LarkAuthCallbackView(APIView):
    """
    Lark登录回调处理
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        处理Lark授权回调
        """
        try:
            code = request.GET.get('code')
            state = request.GET.get('state')
            error = request.GET.get('error')
            
            # 检查是否有错误
            if error:
                error_description = request.GET.get('error_description', '未知错误')
                logger.error(f"Lark授权错误: {error} - {error_description}")
                
                # 重定向到前端错误页面
                error_params = urlencode({
                    'error': error,
                    'error_description': error_description
                })
                return HttpResponseRedirect(
                    f"{settings.FRONTEND_URL}/auth/error?{error_params}"
                )
            
            # 检查必要参数
            if not code or not state:
                logger.error("缺少必要的授权参数")
                error_params = urlencode({
                    'error': 'missing_params',
                    'error_description': '缺少授权码或状态参数'
                })
                return HttpResponseRedirect(
                    f"{settings.FRONTEND_URL}/auth/error?{error_params}"
                )
            
            # 完成OAuth流程
            user, user_info = lark_oauth_client.complete_oauth_flow(code, state)
            
            # 生成JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # 重定向到前端，携带tokens
            success_params = urlencode({
                'access': str(access_token),
                'refresh': str(refresh),
                'user_id': user.id,
                'username': user.username,
                'email': user.email or ''
            })
            
            redirect_url = f"{settings.FRONTEND_URL}/auth/success?{success_params}"
            logger.info(f"用户 {user.username} 登录成功，重定向到前端")
            return HttpResponseRedirect(redirect_url)
            
        except LarkOAuthError as e:
            logger.error(f"Lark OAuth错误: {str(e)}")
            error_params = urlencode({
                'error': 'oauth_error',
                'error_description': str(e)
            })
            return HttpResponseRedirect(
                f"{settings.FRONTEND_URL}/auth/error?{error_params}"
            )
        except Exception as e:
            logger.error(f"Lark授权回调处理失败: {str(e)}", exc_info=True)
            error_params = urlencode({
                'error': 'server_error',
                'error_description': '服务器内部错误，请稍后重试'
            })
            return HttpResponseRedirect(
                f"{settings.FRONTEND_URL}/auth/error?{error_params}"
            )


class LarkAuthStatusView(APIView):
    """
    检查Lark登录配置状态
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """获取Lark登录配置状态"""
        lark_enabled = bool(
            settings.LARK_APP_ID and 
            settings.LARK_APP_SECRET
        )
        
        return Response({
            "lark_login_enabled": lark_enabled,
            "app_id": settings.LARK_APP_ID if lark_enabled else None,
            "redirect_uri": settings.LARK_REDIRECT_URI if lark_enabled else None
        })


@method_decorator(csrf_exempt, name='dispatch')
class LarkUserInfoView(APIView):
    """
    获取当前登录用户信息
    """
    def get(self, request):
        """获取用户信息"""
        if not request.user.is_authenticated:
            return Response(
                {"error": "用户未登录"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user = request.user
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_staff": user.is_staff,
            "date_joined": user.date_joined,
            "last_login": user.last_login,
        }
        
        # 如果有profile信息，也包含进来
        if hasattr(user, 'profile'):
            profile = user.profile
            user_data.update({
                "avatar_url": profile.avatar.url if profile.avatar else None,
                "phone": profile.phone,
            })
        
        return Response({"user": user_data})


# 测试视图，用于开发调试
class LarkTestView(APIView):
    """
    Lark登录测试视图（仅在DEBUG模式下可用）
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """返回Lark配置信息（仅调试用）"""
        if not settings.DEBUG:
            return Response(
                {"error": "此接口仅在调试模式下可用"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return Response({
            "lark_config": {
                "app_id": settings.LARK_APP_ID,
                "app_secret": "***" + settings.LARK_APP_SECRET[-4:] if settings.LARK_APP_SECRET else None,
                "redirect_uri": settings.LARK_REDIRECT_URI,
                "frontend_url": settings.FRONTEND_URL,
            },
            "endpoints": {
                "auth_initiate": "/api/auth/lark/",
                "auth_callback": "/api/auth/lark/callback/",
                "status": "/api/auth/lark/status/",
                "user_info": "/api/auth/lark/user/",
            },
            "instructions": {
                "step1": f"访问 /api/auth/lark/ 获取授权URL",
                "step2": "用户在飞书授权页面同意授权",
                "step3": f"飞书重定向到 {settings.LARK_REDIRECT_URI}",
                "step4": "后端处理回调并重定向到前端",
                "step5": "前端保存tokens并跳转到dashboard"
            }
        })