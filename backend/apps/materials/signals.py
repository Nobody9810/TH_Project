# api/signals.py - ✅ 完整优化版
import os
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.core.files.base import ContentFile

from ..users.models import UserProfile
from .models import Material, MaterialImage, MaterialVideo
from .utils.compression_handler import FileCompressionManager
import logging
from django.utils import timezone
from django.conf import settings
from ..lark_integration.services import lark_notifier
import subprocess
import shutil
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

# ==================== 压缩处理信号 ====================

@receiver(pre_save, sender=Material)
@receiver(pre_save, sender=MaterialImage)
@receiver(pre_save, sender=MaterialVideo)
def compress_files_before_save(sender, instance, **kwargs):
    """
    在保存模型之前压缩文件
    支持: Material头图, MaterialImage图片, MaterialVideo视频
    """
    
    # 获取旧实例,避免重复压缩
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
            should_compress = False
            
            if old_instance is None:
                should_compress = True
            elif not old_instance.header_image:
                should_compress = True
            elif old_instance.header_image.name != instance.header_image.name:
                should_compress = True
            
            if should_compress and hasattr(instance.header_image, 'file'):
                logger.info(f"🔄 开始压缩 Material 头图: {instance.header_image.name}")
                
                try:
                    if hasattr(instance.header_image.file, 'read'):
                        instance.header_image.file.seek(0)
                        original_content = instance.header_image.file.read()
                        
                        logger.info(f"📏 读取头图内容: {len(original_content)/1024/1024:.2f}MB")
                        
                        compressed_file, compression_info = FileCompressionManager.process_uploaded_file(
                            original_content, 
                            instance.header_image.name,
                            'image'
                        )
                        
                        if compressed_file and compression_info:
                            logger.info(f"✅ Material 头图压缩成功: {compression_info['compression_ratio']:.1f}%")
                            
                            if old_instance and old_instance.header_image:
                                try:
                                    old_instance.header_image.delete(save=False)
                                except:
                                    pass
                            
                            instance.header_image = compressed_file
                        else:
                            logger.info(f"ℹ️ Material 头图无需压缩或压缩失败")
                except Exception as e:
                    logger.warning(f"⚠️ 读取头图文件失败: {str(e)}")
                    
        except Exception as e:
            logger.error(f"❌ Material 头图压缩失败: {str(e)}", exc_info=True)
    
    # 处理 MaterialImage 的图片
    if hasattr(instance, 'image') and instance.image:
        try:
            should_compress = False
            
            if old_instance is None:
                should_compress = True
            elif not old_instance.image:
                should_compress = True
            elif old_instance.image.name != instance.image.name:
                should_compress = True
            
            if should_compress and hasattr(instance.image, 'file'):
                logger.info(f"🔄 开始压缩 MaterialImage 图片: {instance.image.name}")
                
                try:
                    if hasattr(instance.image.file, 'read'):
                        instance.image.file.seek(0)
                        original_content = instance.image.file.read()
                        
                        logger.info(f"📏 读取图片内容: {len(original_content)/1024/1024:.2f}MB")
                        
                        compressed_file, compression_info = FileCompressionManager.process_uploaded_file(
                            original_content, 
                            instance.image.name,
                            'image'
                        )
                        
                        if compressed_file and compression_info:
                            logger.info(f"✅ MaterialImage 图片压缩成功: {compression_info['compression_ratio']:.1f}%")
                            
                            if old_instance and old_instance.image:
                                try:
                                    old_instance.image.delete(save=False)
                                except:
                                    pass
                            
                            instance.image = compressed_file
                        else:
                            logger.info(f"ℹ️ MaterialImage 图片无需压缩")
                except Exception as e:
                    logger.warning(f"⚠️ 读取图片文件失败: {str(e)}")
                    
        except Exception as e:
            logger.error(f"❌ MaterialImage 图片压缩失败: {str(e)}", exc_info=True)
    
    # ✅ 处理 MaterialVideo 的视频
    if hasattr(instance, 'video') and instance.video:
        try:
            should_compress = False
            
            if old_instance is None:
                should_compress = True
            elif not old_instance.video:
                should_compress = True
            elif old_instance.video.name != instance.video.name:
                should_compress = True
            
            if should_compress and hasattr(instance.video, 'file'):
                logger.info(f"🔄 开始压缩 MaterialVideo 视频: {instance.video.name}")
                
                try:
                    if hasattr(instance.video.file, 'read'):
                        instance.video.file.seek(0)
                        original_content = instance.video.file.read()
                        
                        logger.info(f"📏 读取视频内容: {len(original_content)/1024/1024:.2f}MB")
                        
                        compressed_file, compression_info = FileCompressionManager.process_uploaded_file(
                            original_content, 
                            instance.video.name,
                            'video'
                        )
                        
                        if compressed_file and compression_info:
                            logger.info(f"✅ MaterialVideo 视频压缩成功: {compression_info['compression_ratio']:.1f}%")
                            
                            if old_instance and old_instance.video:
                                try:
                                    old_instance.video.delete(save=False)
                                except:
                                    pass
                            
                            instance.video = compressed_file
                        else:
                            logger.info(f"ℹ️ MaterialVideo 视频无需压缩或压缩失败")
                except Exception as e:
                    logger.warning(f"⚠️ 读取视频文件失败: {str(e)}")
                    
        except Exception as e:
            logger.error(f"❌ MaterialVideo 视频压缩失败: {str(e)}", exc_info=True)


# ==================== ✅ 新增: 自动生成视频缩略图 ====================

@receiver(post_save, sender=MaterialVideo)
def generate_video_thumbnail(sender, instance, created, **kwargs):
    """
    视频上传后自动生成缩略图
    优先级: 已有缩略图 > 自动生成 > 使用素材头图
    """
    # 只在新建且没有缩略图时生成
    if not created or instance.thumbnail or not instance.video:
        return
    
    temp_thumb = None
    try:
        video_path = instance.video.path
        
        # 创建临时缩略图目录
        thumb_dir = os.path.join(settings.MEDIA_ROOT, 'material_video_thumbnails', 'temp')
        os.makedirs(thumb_dir, exist_ok=True)
        
        thumb_filename = f"{os.path.splitext(os.path.basename(video_path))[0]}_thumb.jpg"
        temp_thumb = os.path.join(thumb_dir, thumb_filename)
        
        logger.info(f"🎬 开始为视频生成缩略图: {instance.id}")
        
        # 使用FFmpeg提取第1秒的帧作为缩略图
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-ss', '00:00:01.000',  # 提取第1秒
            '-vframes', '1',         # 只提取1帧
            '-vf', 'scale=1280:-1',  # 宽度1280,高度自适应
            '-q:v', '2',             # 高质量
            '-y',
            temp_thumb
        ]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and os.path.exists(temp_thumb):
            # 压缩缩略图
            with open(temp_thumb, 'rb') as f:
                thumb_content = f.read()
            
            # 使用PIL压缩缩略图到合理大小
            img = Image.open(BytesIO(thumb_content))
            img = img.convert('RGB')
            
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            compressed_thumb = output.getvalue()
            
            # 保存缩略图到数据库
            instance.thumbnail.save(
                thumb_filename,
                ContentFile(compressed_thumb),
                save=True
            )
            
            logger.info(f"✅ 视频缩略图生成成功: {instance.id} ({len(compressed_thumb)/1024:.1f}KB)")
        else:
            logger.warning(f"⚠️ 缩略图生成失败: {result.stderr[:200]}")
            
    except subprocess.TimeoutExpired:
        logger.warning(f"⚠️ 缩略图生成超时: {instance.id}")
    except Exception as e:
        logger.error(f"❌ 生成缩略图失败: {str(e)}", exc_info=True)
    finally:
        # 清理临时文件
        if temp_thumb and os.path.exists(temp_thumb):
            try:
                os.remove(temp_thumb)
            except:
                pass


# ==================== 文件清理信号 ====================

def _safe_delete_field_file(field_file):
    """安全删除文件字段的物理文件"""
    try:
        if field_file and hasattr(field_file, 'storage'):
            field_file.delete(save=False)
    except Exception as e:
        logger.warning(f"⚠️ 文件删除失败: {str(e)}")

@receiver(post_delete, sender=MaterialImage)
def delete_material_image_file(sender, instance, **kwargs):
    """删除MaterialImage记录时同步删除物理文件"""
    _safe_delete_field_file(instance.image)

@receiver(post_delete, sender=MaterialVideo)
def delete_material_video_file(sender, instance, **kwargs):
    """删除MaterialVideo记录时同步删除物理文件"""
    _safe_delete_field_file(instance.video)
    _safe_delete_field_file(instance.thumbnail)

@receiver(post_delete, sender=Material)
def delete_material_files(sender, instance, **kwargs):
    """删除Material记录时同步删除物理文件"""
    _safe_delete_field_file(instance.header_image)
    _safe_delete_field_file(instance.pdf_file)

@receiver(post_delete, sender=UserProfile)
def delete_user_avatar_file(sender, instance, **kwargs):
    """删除UserProfile记录时同步删除头像文件"""
    _safe_delete_field_file(instance.avatar)


# ==================== 文件替换时清理旧文件 ====================

def _delete_old_file_on_change(instance, sender, field_name):
    """当文件字段被替换时,删除旧文件"""
    try:
        if not instance.pk:
            return
        old = sender.objects.filter(pk=instance.pk).first()
        if not old:
            return
        old_file = getattr(old, field_name, None)
        new_file = getattr(instance, field_name, None)
        if old_file and new_file and old_file.name != new_file.name:
            _safe_delete_field_file(old_file)
    except Exception as e:
        logger.warning(f"⚠️ 清理旧文件失败: {str(e)}")

@receiver(pre_save, sender=Material)
def cleanup_material_replaced_files(sender, instance, **kwargs):
    """Material文件替换时清理"""
    _delete_old_file_on_change(instance, sender, 'header_image')
    _delete_old_file_on_change(instance, sender, 'pdf_file')

@receiver(pre_save, sender=MaterialImage)
def cleanup_materialimage_replaced_files(sender, instance, **kwargs):
    """MaterialImage文件替换时清理"""
    _delete_old_file_on_change(instance, sender, 'image')

@receiver(pre_save, sender=MaterialVideo)
def cleanup_materialvideo_replaced_files(sender, instance, **kwargs):
    """MaterialVideo文件替换时清理"""
    _delete_old_file_on_change(instance, sender, 'video')
    _delete_old_file_on_change(instance, sender, 'thumbnail')

@receiver(pre_save, sender=UserProfile)
def cleanup_userprofile_replaced_avatar(sender, instance, **kwargs):
    """UserProfile头像替换时清理"""
    _delete_old_file_on_change(instance, sender, 'avatar')

