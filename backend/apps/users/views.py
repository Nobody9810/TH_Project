from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, filters, status, generics
from .serializers import UserSerializer




class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class AvatarUploadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        user = request.user
        avatar_file = request.FILES.get('avatars') 
        
        if not avatar_file:
            return Response(
                {"detail": "未提供头像文件"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 验证文件类型
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if avatar_file.content_type not in allowed_types:
            return Response(
                {"detail": "只支持 JPEG、PNG 和 GIF 格式的图片"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 验证文件大小 (最大 2MB)
        if avatar_file.size > 2 * 1024 * 1024:
            return Response(
                {"detail": "头像文件不能超过 2MB"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 保存头像
            user.profile.avatar = avatar_file
            user.profile.save()
            
            # 返回更新后的用户信息
            serializer = UserSerializer(user)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {"detail": f"上传失败: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )