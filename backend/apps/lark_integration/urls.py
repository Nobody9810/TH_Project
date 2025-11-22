from django.urls import path
from .views import (
    LarkAuthInitiateView,
    LarkAuthCallbackView,
    LarkAuthStatusView,
    LarkUserInfoView,
    LarkTestView,
)

urlpatterns = [    
    # Lark 登录相关路由（简化版）
    path('lark/', LarkAuthInitiateView.as_view(), name='lark_auth'),
    path('lark/callback/', LarkAuthCallbackView.as_view(), name='lark_callback'),
    path('lark/status/', LarkAuthStatusView.as_view(), name='lark_status'),
    path('lark/user/', LarkUserInfoView.as_view(), name='lark_user_info'),
    
    # 调试接口（仅DEBUG模式）
    path('lark/test/', LarkTestView.as_view(), name='lark_test'),
]
