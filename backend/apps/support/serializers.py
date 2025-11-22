from rest_framework import serializers
from django.contrib.auth.models import User
from .models import SupportTicket
from apps.users.serializers import UserSerializer
class SupportTicketSerializer(serializers.ModelSerializer):
    # ✅ 嵌套序列化器：使用 UserSerializer 来返回完整的用户对象
    author = UserSerializer(read_only=True)
    answered_by = UserSerializer(read_only=True)
    
    # 返回分类的可读名称，例如 "常见问题" 而不是 "faq"
    category_display = serializers.CharField(source='get_category_display', read_only=True) 

    class Meta:
        model = SupportTicket
        fields = [
            'id', 'author', 'category', 'category_display', 
            'question_text', 'created_at',
            'is_answered', 'answer_content', 'answered_by', 'answered_at',
            'is_public_faq'
        ]
        # 设置只读字段，这些字段将由后端逻辑在 PATCH/Create 时自动设置
        read_only_fields = ('is_answered', 'answered_by', 'answered_at')
 