from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Destination, Material, MaterialImage,MaterialVideo



class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ['id', 'name', 'slug']

class MaterialVideoSerializer(serializers.ModelSerializer):
    """✅ 新增: 素材视频序列化器"""
    class Meta:
        model = MaterialVideo
        fields = ['id', 'video', 'title', 'description', 'thumbnail', 'order', 'duration']

class MaterialImageSerializer(serializers.ModelSerializer):
    """素材图片序列化器"""
    class Meta:
        model = MaterialImage
        fields = ['id', 'image', 'description', 'order']


class MaterialSerializer(serializers.ModelSerializer):
    """✅ 修复: 素材序列化器 (支持多视频)"""
    
    # 嵌套 Serializer
    destination = DestinationSerializer(read_only=True)
    images = MaterialImageSerializer(many=True, read_only=True)
    videos = MaterialVideoSerializer(many=True, read_only=True) # ✅ 新增: 序列化 videos 数组
    
    header_image = serializers.SerializerMethodField()

    uploaded_images = serializers.ListField(
        child=serializers.ImageField(max_length=100000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )
    uploaded_videos = serializers.ListField(
        child=serializers.FileField(max_length=200000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )
    
    # 显示相关(保持不变)
    material_type_display = serializers.CharField(source='get_material_type_display', read_only=True)
    
    class Meta:
        model = Material
        fields = [
            'id', 'material_type', 'title', 'destination', 'description', 
            'price', 'pdf_file', 'header_image', 
            'images', #
            'videos', 
            'uploaded_images',
            'uploaded_videos',
            'created_at', 'updated_at','material_type_display'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_header_image(self, obj):
        """返回第一张图片的 URL"""
        if not obj.pk:
            return None
            
        first_image = obj.images.first()
        if first_image and first_image.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_image.image.url)
            return first_image.image.url
        return None
    def create(self, validated_data):
        # (扩展: 同时处理 uploaded_images 与 uploaded_videos)
        uploaded_images = validated_data.pop('uploaded_images', [])
        uploaded_videos = validated_data.pop('uploaded_videos', [])
        material = Material.objects.create(**validated_data)
        
        # 创建关联的图片
        for image in uploaded_images:
            MaterialImage.objects.create(material=material, image=image)
        # 创建关联的视频
        for video in uploaded_videos:
            MaterialVideo.objects.create(material=material, video=video)
        
        return material

    def update(self, instance, validated_data):
        # (扩展: 同时处理 uploaded_images 与 uploaded_videos)
        uploaded_images = validated_data.pop('uploaded_images', [])
        uploaded_videos = validated_data.pop('uploaded_videos', [])
        
        # 更新素材基本信息
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # 添加新图片
        for image in uploaded_images:
            MaterialImage.objects.create(material=instance, image=image)
        # 添加新视频
        for video in uploaded_videos:
            MaterialVideo.objects.create(material=instance, video=video)
        
        return instance


 