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
    path('', LarkAuthInitiateView.as_view(), name='lark_auth'),
    path('callback/', LarkAuthCallbackView.as_view(), name='lark_callback'),
    path('status/', LarkAuthStatusView.as_view(), name='lark_status'),
    path('user/', LarkUserInfoView.as_view(), name='lark_user_info'),
    
    # 调试接口（仅DEBUG模式）
    path('test/', LarkTestView.as_view(), name='lark_test'),
]
