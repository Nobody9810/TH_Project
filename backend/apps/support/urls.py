from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SupportTicketViewSet
router = DefaultRouter()

router.register(r'supportticket', SupportTicketViewSet, basename='supportticket')


urlpatterns = [
    path('auth/', include('apps.users.urls')),  # 包含认证路由
    # path("me/", UserProfileView.as_view(), name="get_me"),
    # path("me/avatar/", AvatarUploadView.as_view(), name="upload_avatar"),
] + router.urls