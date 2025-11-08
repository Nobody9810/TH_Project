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
    
    ✅ 修复：
    1. 检查文件是否是新上传的
    2. 避免重复压缩
    3. 正确处理 Django 的临时文件
    """
    
    # ✅ 修复1: 获取旧实例，避免重复压缩
    try:
        if instance.pk:
            old_instance = sender.objects.get(pk=instance.pk)
        else:
            old_instance = None
    except sender.DoesNotExist:
        old_instance = None
    
    # 处理 Material 的头图
    if hasattr(instance, 'header_image') and instance.header_image:
        try:
            # ✅ 修复2: 检查是否是新上传的文件
            # 只有当文件发生变化时才压缩
            should_compress = False
            
            if old_instance is None:
                # 新建对象
                should_compress = True
            elif not old_instance.header_image:
                # 之前没有文件，现在有了
                should_compress = True
            elif old_instance.header_image.name != instance.header_image.name:
                # 文件名不同，说明是新上传的
                should_compress = True
            
            if should_compress and hasattr(instance.header_image, 'file'):
                print(f"🔍 开始压缩 Material 头图: {instance.header_image.name}")
                
                # ✅ 修复3: 安全地读取文件内容
                try:
                    # 先检查文件是否可读
                    if hasattr(instance.header_image.file, 'read'):
                        instance.header_image.file.seek(0)
                        original_content = instance.header_image.file.read()
                        
                        print(f"🔍 读取头图内容: {len(original_content)/1024/1024:.2f}MB")
                        
                        # 处理压缩
                        compressed_file, compression_info = FileCompressionManager.process_uploaded_file(
                            original_content, 
                            instance.header_image.name,
                            'image'
                        )
                        
                        if compressed_file and compression_info:
                            print(f"✅ Material 头图压缩成功: {compression_info['compression_ratio']:.1f}%")
                            
                            # ✅ 修复4: 删除旧文件（如果存在）
                            if old_instance and old_instance.header_image:
                                try:
                                    old_instance.header_image.delete(save=False)
                                except:
                                    pass
                            
                            # 替换文件
                            instance.header_image = compressed_file
                        else:
                            print(f"ℹ️ Material 头图无需压缩或压缩失败")
                except Exception as e:
                    print(f"⚠️ 读取头图文件失败: {str(e)}")
                    # 继续使用原文件
                    
        except Exception as e:
            print(f"❌ Material 头图压缩失败: {str(e)}")
            logger.error(f"Material header_image compression failed: {str(e)}", exc_info=True)
    
    # 处理 Material 的视频
    if hasattr(instance, 'video') and instance.video:
        try:
            # 检查是否是新上传的文件
            should_compress = False
            
            if old_instance is None:
                should_compress = True
            elif not old_instance.video:
                should_compress = True
            elif old_instance.video.name != instance.video.name:
                should_compress = True
            
            if should_compress and hasattr(instance.video, 'file'):
                print(f"🔍 开始压缩 Material 视频: {instance.video.name}")
                
                try:
                    if hasattr(instance.video.file, 'read'):
                        instance.video.file.seek(0)
                        original_content = instance.video.file.read()
                        
                        print(f"🔍 读取视频内容: {len(original_content)/1024/1024:.2f}MB")
                        
                        # 处理压缩
                        compressed_file, compression_info = FileCompressionManager.process_uploaded_file(
                            original_content, 
                            instance.video.name,
                            'video'
                        )
                        
                        if compressed_file and compression_info:
                            print(f"✅ Material 视频压缩成功: {compression_info['compression_ratio']:.1f}%")
                            
                            # 删除旧文件
                            if old_instance and old_instance.video:
                                try:
                                    old_instance.video.delete(save=False)
                                except:
                                    pass
                            
                            # 替换文件
                            instance.video = compressed_file
                        else:
                            print(f"ℹ️ Material 视频无需压缩或压缩失败")
                except Exception as e:
                    print(f"⚠️ 读取视频文件失败: {str(e)}")
                    
        except Exception as e:
            print(f"❌ Material 视频压缩失败: {str(e)}")
            logger.error(f"Material video compression failed: {str(e)}", exc_info=True)
    
    # 处理 MaterialImage 的图片
    if hasattr(instance, 'image') and instance.image:
        try:
            # 检查是否是新上传的文件
            should_compress = False
            
            if old_instance is None:
                should_compress = True
            elif not old_instance.image:
                should_compress = True
            elif old_instance.image.name != instance.image.name:
                should_compress = True
            
            if should_compress and hasattr(instance.image, 'file'):
                print(f"🔍 开始压缩 MaterialImage 图片: {instance.image.name}")
                
                try:
                    if hasattr(instance.image.file, 'read'):
                        instance.image.file.seek(0)
                        original_content = instance.image.file.read()
                        
                        print(f"🔍 读取图片内容: {len(original_content)/1024/1024:.2f}MB")
                        
                        # 处理压缩
                        compressed_file, compression_info = FileCompressionManager.process_uploaded_file(
                            original_content, 
                            instance.image.name,
                            'image'
                        )
                        
                        if compressed_file and compression_info:
                            print(f"✅ MaterialImage 图片压缩成功: {compression_info['compression_ratio']:.1f}%")
                            
                            # 删除旧文件
                            if old_instance and old_instance.image:
                                try:
                                    old_instance.image.delete(save=False)
                                except:
                                    pass
                            
                            # 替换文件
                            instance.image = compressed_file
                        else:
                            print(f"ℹ️ MaterialImage 图片无需压缩")
                except Exception as e:
                    print(f"⚠️ 读取图片文件失败: {str(e)}")
                    
        except Exception as e:
            print(f"❌ MaterialImage 图片压缩失败: {str(e)}")
            logger.error(f"MaterialImage compression failed: {str(e)}", exc_info=True)


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