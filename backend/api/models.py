from django.db import models
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.conf import settings
import os
from django.dispatch import receiver
from django.db.models.signals import post_save
from pdf2image import convert_from_path


class Destination(models.Model):
    """目的地/分类，例如：吉隆坡、仙本那"""
    name = models.CharField(max_length=100, unique=True, verbose_name="目的地名称")
    slug = models.SlugField(max_length=100, unique=True, help_text="用于URL的唯一标识，例如 'kuala-lumpur'")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "目的地"
        verbose_name_plural = "目的地"
        ordering = ['name']

    def __str__(self):
        return self.name

class Material(models.Model):
    """
    统一的素材库模型，包含酒店、门票、路线规划
    """
    class MaterialType(models.TextChoices):
        HOTEL = 'hotel', '酒店'
        TICKET = 'ticket', '门票'
        ROUTE = 'route', '路线规划'

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
    description = models.TextField(blank=True, verbose_name="描述/行程")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="价格"
    )

    # 仅用于路线规划
    pdf_file = models.FileField(
        upload_to='route_pdfs/',
        null=True,
        blank=True,
        verbose_name="PDF文件 (仅路线规划)"
    )
    # 用于酒店/门票的主图，或从PDF生成的第一页预览图
    header_image = models.ImageField(
        upload_to='material_headers/',
        blank=True,
        verbose_name="头图/主图"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "素材"
        verbose_name_plural = "素材库"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_material_type_display()}] {self.title}"

    def save(self, *args, **kwargs):
        # 记录是否是新创建的对象
        is_new = self._state.adding
        # 先保存一次，确保 pdf_file 已经存储到文件系统
        super().save(*args, **kwargs)

        # 如果是路线规划类型，并且上传了PDF，并且没有头图，则自动生成
        if self.material_type == self.MaterialType.ROUTE and self.pdf_file and not self.header_image:
            try:
                # self.pdf_file.path 指向文件在服务器上的绝对路径
                images = convert_from_path(self.pdf_file.path, first_page=1, last_page=1, fmt='jpeg')
                if images:
                    first_page_image = images[0]
                    # 将图片保存到内存中
                    temp_thumb = ContentFile(b'', name=f"{os.path.basename(self.pdf_file.name)}.jpg")
                    first_page_image.save(temp_thumb, 'JPEG')
                    
                    # 将内存中的图片赋值给 header_image 字段
                    self.header_image.save(temp_thumb.name, temp_thumb, save=False)
                    # 再次保存，只更新 header_image 字段以避免递归调用
                    super().save(update_fields=['header_image'])
            except Exception as e:
                # 处理生成失败的情况，例如打印日志
                print(f"无法从PDF {self.pdf_file.name} 生成预览图: {e}")

class MaterialImage(models.Model):
    """用于存储素材的图片库，主要用于酒店"""
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="所属素材"
    )
    image = models.ImageField(upload_to='material_gallery/', verbose_name="图片")

    class Meta:
        verbose_name = "素材图片"
        verbose_name_plural = "素材图片库"

    def __str__(self):
        return f"{self.material.title} 的图片"






class SupportTicket(models.Model):
    CATEGORY_CHOICES = [
        ('faq', '常见问题'),
        ('ticket', '订票问题'),
        ('car', '汽车问题'),
        ('incident', '意外情况'),
    ]
    
    # 提问方/创建者
    author = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='submitted_tickets',
        verbose_name="提问/创建者"
    )
    
    # 问题信息
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="问题分类")
    question_text = models.TextField(verbose_name="问题详细描述/标题") 
    created_at = models.DateTimeField(auto_now_add=True)

    # 管理员回答信息 
    is_answered = models.BooleanField(default=False, verbose_name="是否已回答")
    answer_content = models.TextField(blank=True, null=True, verbose_name="管理员回答内容")
    answered_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='answered_tickets',
        verbose_name="回答者"
    )
    answered_at = models.DateTimeField(blank=True, null=True, verbose_name="回答时间")
    
    # 可选：是否作为最佳/公开知识库
    is_public_faq = models.BooleanField(default=False, verbose_name="公开到知识库")
    
    class Meta:
        verbose_name = "支持工单/问答"
        verbose_name_plural = "支持工单/问答库"
        ordering = ['-created_at']

    def __str__(self):
        # ⚠️ __str__ 使用 question_text 的前 50 个字符作为显示标题
        return self.question_text[:50] + ('...' if len(self.question_text) > 50 else '')



# models.py - 在 SupportTicket 模型后添加
class UserProfile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='profile'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name="头像"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="手机号"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "用户资料"
        verbose_name_plural = "用户资料"

    def __str__(self):
        return f"{self.user.username} 的资料"

# 创建用户资料信号
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()