from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import UserProfileView, AvatarUploadView

urlpatterns = [
    # === JWT 认证 (登录 & 刷新) ===
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # === 用户资料 ===

    path('me/', UserProfileView.as_view(), name='get_me'),
    path('me/avatar/', AvatarUploadView.as_view(), name='upload_avatar'),
]

