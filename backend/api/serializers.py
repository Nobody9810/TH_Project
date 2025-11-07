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
    """素材图片序列化器"""
    class Meta:
        model = MaterialImage
        fields = ['id', 'image', 'description', 'order']

# class MaterialSerializer(serializers.ModelSerializer):
#     # 使用嵌套序列化器显示完整的目的地信息和图片列表
#     destination = DestinationSerializer(read_only=True)
#     images = MaterialImageSerializer(many=True, read_only=True)
#     # 返回 material_type 的可读名称，例如 "酒店" 而不是 "hotel"
#     material_type_display = serializers.CharField(source='get_material_type_display', read_only=True)
    
#     class Meta:
#         model = Material
#         fields = [
#             'id', 'title', 'destination', 'description', 'price',
#             'pdf_file', 'header_image', 'images', 'material_type',
#             'material_type_display', 'created_at', 'updated_at'
#         ]



class MaterialSerializer(serializers.ModelSerializer):
    """素材序列化器"""
    images = MaterialImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(max_length=100000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )
    destination = DestinationSerializer(read_only=True)
    images = MaterialImageSerializer(many=True, read_only=True)
    # 返回 material_type 的可读名称，例如 "酒店" 而不是 "hotel"
    material_type_display = serializers.CharField(source='get_material_type_display', read_only=True)
    
    class Meta:
        model = Material
        fields = [
            'id', 'material_type', 'title', 'destination', 'description', 
            'price', 'pdf_file', 'header_image', 'video', 'images', 
            'uploaded_images', 'created_at', 'updated_at','material_type_display'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        """验证视频字段只能用于酒店类型"""
        material_type = data.get('material_type', self.instance.material_type if self.instance else None)
        video = data.get('video')
        
        if video and material_type != Material.MaterialType.HOTEL:
            raise serializers.ValidationError({
                'video': '视频只能上传到酒店类型的素材'
            })
        
        return data

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        material = Material.objects.create(**validated_data)
        
        # 创建关联的图片
        for image in uploaded_images:
            MaterialImage.objects.create(material=material, image=image)
        
        return material

    def update(self, instance, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        
        # 更新素材基本信息
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # 添加新图片
        for image in uploaded_images:
            MaterialImage.objects.create(material=instance, image=image)
        
        return instance


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
 