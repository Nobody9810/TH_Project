from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static 

# ✅ 从 users 应用中导入 JWT View 和 Profile View
from apps.users.views import UserProfileView, AvatarUploadView 
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # 1. 认证接口 (JWT) - 放在 /api/auth/ 下，匹配前端登录成功路径
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 2. 用户资料接口 - 直接放在 /api/ 下，匹配前端 /api/me/ 的请求
    path('api/me/', UserProfileView.as_view(), name='get_me'),
    path('api/me/avatar/', AvatarUploadView.as_view(), name='upload_avatar'),
    
    # 3. 其他应用不变
    path('api/', include('apps.materials.urls')),
    path('api/', include('apps.support.urls')),
    path('api/lark/', include('apps.lark_integration.urls')),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)