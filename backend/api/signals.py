# api/signals.py
import os
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.files.base import ContentFile
from .models import Material, MaterialImage
from utils.compression_handler import FileCompressionManager
import logging
from django.utils import timezone

from django.conf import settings
from .models import SupportTicket
from api.lark_notification import lark_notifier

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=Material)
@receiver(pre_save, sender=MaterialImage)
def compress_files_before_save(sender, instance, **kwargs):
    """
    在保存模型之前压缩文件
    """
    # 检查是否是新建对象
    if instance.pk is None:
        # 新建对象，处理文件压缩
        
        # 处理 Material 的头图
        if hasattr(instance, 'header_image') and instance.header_image:
            try:
                print(f"🔍 开始压缩 Material 头图: {instance.header_image.name}")
                
                # 读取文件内容
                instance.header_image.open('rb')
                original_content = instance.header_image.read()
                instance.header_image.close()
                
                print(f"🔍 读取头图内容: {len(original_content)} bytes")
                
                # 处理压缩
                compressed_file, compression_info = FileCompressionManager.process_uploaded_file(
                    original_content, 
                    instance.header_image.name,
                    'image'
                )
                
                if compressed_file and compression_info:
                    print(f"✅ Material 头图压缩成功: {compression_info['compression_ratio']:.1f}%")
                    
                    # 保存压缩信息
                    if not hasattr(instance, '_compression_data'):
                        instance._compression_data = {}
                    instance._compression_data['header_image'] = compression_info
                    
                    # 替换文件
                    instance.header_image.save(
                        compressed_file.name,
                        compressed_file,
                        save=False  # 不立即保存，等待主保存
                    )
                    
            except Exception as e:
                print(f"❌ Material 头图压缩失败: {str(e)}")
        
        # 处理 Material 的视频
        if hasattr(instance, 'video') and instance.video:
            try:
                print(f"🔍 开始压缩 Material 视频: {instance.video.name}")
                
                # 读取文件内容
                instance.video.open('rb')
                original_content = instance.video.read()
                instance.video.close()
                
                print(f"🔍 读取视频内容: {len(original_content)} bytes")
                
                # 处理压缩
                compressed_file, compression_info = FileCompressionManager.process_uploaded_file(
                    original_content, 
                    instance.video.name,
                    'video'
                )
                
                if compressed_file and compression_info:
                    print(f"✅ Material 视频压缩成功: {compression_info['compression_ratio']:.1f}%")
                    
                    # 保存压缩信息
                    if not hasattr(instance, '_compression_data'):
                        instance._compression_data = {}
                    instance._compression_data['video'] = compression_info
                    
                    # 替换文件
                    instance.video.save(
                        compressed_file.name,
                        compressed_file,
                        save=False  # 不立即保存，等待主保存
                    )
                    
            except Exception as e:
                print(f"❌ Material 视频压缩失败: {str(e)}")
        
        # 处理 MaterialImage 的图片
        if hasattr(instance, 'image') and instance.image:
            try:
                print(f"🔍 开始压缩 MaterialImage 图片: {instance.image.name}")
                
                # 读取文件内容
                instance.image.open('rb')
                original_content = instance.image.read()
                instance.image.close()
                
                print(f"🔍 读取图片内容: {len(original_content)} bytes")
                
                # 处理压缩
                compressed_file, compression_info = FileCompressionManager.process_uploaded_file(
                    original_content, 
                    instance.image.name,
                    'image'
                )
                
                if compressed_file and compression_info:
                    print(f"✅ MaterialImage 图片压缩成功: {compression_info['compression_ratio']:.1f}%")
                    
                    # 保存压缩信息到关联的 Material
                    if hasattr(instance, 'material') and instance.material:
                        if not hasattr(instance.material, '_compression_data'):
                            instance.material._compression_data = {}
                        instance.material._compression_data[f'image_{instance.id}'] = compression_info
                    
                    # 替换文件
                    instance.image.save(
                        compressed_file.name,
                        compressed_file,
                        save=False  # 不立即保存，等待主保存
                    )
                    
            except Exception as e:
                print(f"❌ MaterialImage 图片压缩失败: {str(e)}")



# SupportTicket 创建后发送飞书通知
def get_user_display_name(user):
    """获取用户显示名称（优先使用真实姓名）"""
    if not user:
        return '匿名用户'
    
    # 方案1: 优先使用 first_name + last_name
    if user.first_name or user.last_name:
        full_name = f"{user.last_name}{user.first_name}".strip()  # 中文习惯：姓在前
        if full_name:
            return full_name
    
    # 方案2: 如果有 profile.chinese_name
    if hasattr(user, 'profile') and hasattr(user.profile, 'chinese_name'):
        if user.profile.chinese_name:
            return user.profile.chinese_name
    
    # 方案3: 回退到用户名
    return user.username or '匿名用户'


@receiver(post_save, sender=SupportTicket)
def notify_new_ticket(sender, instance, created, **kwargs):
    """新问题创建时发送 Lark 通知"""
    if created:
        try:
            detail_url = f"{settings.FRONTEND_URL}/supportticket"
            
            # 获取用户显示名称
            author_name = get_user_display_name(instance.author)
            local_time = timezone.localtime(instance.created_at)
            ticket_data = {
                'id': instance.id,
                'category': instance.category,
                'category_display': instance.get_category_display(),
                'question_text': instance.question_text,
                'author_name': author_name,  # 使用真实姓名
                'created_at': local_time.strftime('%Y-%m-%d %H:%M:%S'),
                'detail_url': detail_url
            }
            
            lark_notifier.send_new_question_card(ticket_data)
            logger.info(f"Lark notification sent for ticket {instance.id} by {author_name}")
        except Exception as e:
            logger.error(f"Failed to send Lark notification: {e}")