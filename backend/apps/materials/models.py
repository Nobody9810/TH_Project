# api/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.conf import settings
import os
from django.dispatch import receiver
from django.db.models.signals import post_save
from pdf2image import convert_from_path
from django_ckeditor_5.fields import CKEditor5Field
from io import BytesIO  # ✅ <-- 添加这一行

class Destination(models.Model):
    """目的地/分类，例如:吉隆坡、仙本那"""
    name = models.CharField(max_length=100, unique=True, verbose_name="目的地名称")
    slug = models.SlugField(max_length=100, unique=True, help_text="用于URL的唯一标识,例如 'kuala-lumpur'")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "目的地"
        verbose_name_plural = "目的地"
        app_label = 'materials'
        ordering = ['name']

    def __str__(self):
        return self.name


class Material(models.Model):
    """
    统一的素材库模型,包含酒店、景点门票、路线规划、交通工具
    所有类型都支持多图片和多视频
    """
    class MaterialType(models.TextChoices):
        HOTEL = 'hotel', '酒店'
        TICKET = 'ticket', '景点门票'
        ROUTE = 'route', '路线规划'
        TRANSPORT = 'transport', '交通工具'
        RESTAURANT = 'restaurant', '餐厅' 

    material_type = models.CharField(
        max_length=10,
        choices=MaterialType.choices,
        default=MaterialType.HOTEL,
        verbose_name="素材类型"
    )
    title = models.CharField(max_length=200, verbose_name="标题/名称")
    destination = models.ForeignKey(
        Destination,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="materials",
        verbose_name="所属目的地"
    )
    description = CKEditor5Field('描述/行程', config_name='extends', blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="价格"
    )

    # PDF文件(仅路线规划使用)
    pdf_file = models.FileField(
        upload_to='route_pdfs/',
        null=True,
        blank=True,
        verbose_name="PDF文件 (仅路线规划)"
    )
    
    # 压缩相关信息
    compression_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name="压缩信息"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def header_image(self):
        """
        返回第一张图片作为头图
        如果没有图片或对象未保存,返回 None
        """
        # ✅ 添加主键检查
        if not self.pk:  # 如果对象还没有保存到数据库
            return None
        
        first_image = self.images.first()
        return first_image.image if first_image else None
    
    class Meta:
        verbose_name = "素材"
        verbose_name_plural = "素材库"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_material_type_display()}] {self.title}"

    def save(self, *args, **kwargs):
        # 保存压缩数据
        if hasattr(self, '_compression_data'):
            if self.compression_data is None:
                self.compression_data = {}
            self.compression_data.update(self._compression_data)
            delattr(self, '_compression_data')

        # 先执行父类的 save()，确保 self.id 和 self.pdf_file.path 已被保存
        super().save(*args, **kwargs)
        
        # 路线规划的PDF预览图生成
        if self.material_type == self.MaterialType.ROUTE and self.pdf_file and not self.header_image:
            try:
                # 1. 使用 pdf2image 从 PDF 路径转换第一页
                images = convert_from_path(self.pdf_file.path, first_page=1, last_page=1, fmt='jpeg')
                
                if images:
                    first_page_image = images[0]
                    
                    # 2. 准备文件名和内存中的文件
                    temp_thumb_name = f"{os.path.basename(self.pdf_file.name)}.jpg"
                    
                    # ✅【修复】使用 BytesIO 作为内存缓冲区
                    temp_buffer = BytesIO()
                    first_page_image.save(temp_buffer, 'JPEG')

                    # 3. ✅【核心修复】
                    # 现在 temp_buffer.getvalue() 可以正常工作
                    self.images.create(
                        image=ContentFile(temp_buffer.getvalue(), name=temp_thumb_name),
                        description="PDF 封面页",
                        order=0 # 设为 0，确保它是第一张图片
                    )
            except Exception as e:
                # 确保服务器在 PDF 处理失败时不会崩溃
                print(f"❌ 无法从PDF {self.pdf_file.name} 生成预览图: {e}")


class MaterialImage(models.Model):
    """
    ✅ 更新:用于存储素材的图片库,所有素材类型通用
    """
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="所属素材"
    )
    
    image = models.ImageField(
        upload_to='material_gallery/', 
        verbose_name="图片"
    )
    
    description = models.CharField(
        max_length=200, 
        blank=True, 
        verbose_name="图片描述"
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="排序"
    )

    class Meta:
        verbose_name = "素材图片"
        verbose_name_plural = "素材图片库"
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.material.title} 的图片"


class MaterialVideo(models.Model):
    """
    ✅ 新增:用于存储素材的视频库,所有素材类型通用
    """
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name='videos',
        verbose_name="所属素材"
    )
    
    video = models.FileField(
        upload_to='material_videos/',
        verbose_name="视频文件"
    )
    
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="视频标题"
    )
    
    description = models.CharField(
        max_length=200, 
        blank=True, 
        verbose_name="视频描述"
    )
    
    thumbnail = models.ImageField(
        upload_to='material_video_thumbnails/',
        blank=True,
        null=True,
        verbose_name="视频缩略图"
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="排序"
    )
    
    duration = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="时长(秒)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "素材视频"
        verbose_name_plural = "素材视频库"
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.material.title} 的视频"