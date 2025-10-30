from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Destination, Material, MaterialImage, SupportTicket,UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = ['avatar', 'avatar_url', 'phone', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "is_staff", "profile")
        read_only_fields = ("id", "is_staff")

class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ['id', 'name', 'slug']

class MaterialImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialImage
        fields = ['id', 'image']

class MaterialSerializer(serializers.ModelSerializer):
    # 使用嵌套序列化器显示完整的目的地信息和图片列表
    destination = DestinationSerializer(read_only=True)
    images = MaterialImageSerializer(many=True, read_only=True)
    # 返回 material_type 的可读名称，例如 "酒店" 而不是 "hotel"
    material_type_display = serializers.CharField(source='get_material_type_display', read_only=True)
    
    class Meta:
        model = Material
        fields = [
            'id', 'title', 'destination', 'description', 'price',
            'pdf_file', 'header_image', 'images', 'material_type',
            'material_type_display', 'created_at', 'updated_at'
        ]

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
 