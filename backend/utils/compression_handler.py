# backend/utils/compression_handler.py
import os
import logging
from io import BytesIO
from PIL import Image, ImageOps
import subprocess
import tempfile
from django.core.files.base import ContentFile
from django.conf import settings
import traceback
import shutil

logger = logging.getLogger(__name__)
FFMPEG_PATH = '/usr/bin/ffmpeg'
class ImageCompressionHandler:
    """图片压缩处理器"""
    
    @staticmethod
    def compress_image_content(image_content, filename, max_size=(1920, 1080), quality=85):
        """
        压缩图片内容（在内存中处理）
        """
        try:
            original_size = len(image_content)
            print(f"🔍 开始压缩图片: {filename}, 原始大小: {original_size/1024/1024:.2f}MB")
            
            # 将二进制内容转换为PIL图像
            image_buffer = BytesIO(image_content)
            img = Image.open(image_buffer)
            
            # 记录原始信息
            original_width, original_height = img.size
            
            print(f"🔍 图片原始尺寸: {original_width}x{original_height}")
            
            # 转换模式
            if img.mode in ('P', 'RGBA'):
                img = img.convert('RGB')
                output_format = 'JPEG'
            else:
                output_format = img.format or 'JPEG'
            
            # 调整尺寸，保持宽高比
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            new_width, new_height = img.size
            
            print(f"🔍 压缩后尺寸: {new_width}x{new_height}")
            
            # 处理方向信息
            img = ImageOps.exif_transpose(img)
            
            # 保存到内存缓冲区
            output_buffer = BytesIO()
            
            # 设置保存参数
            save_kwargs = {
                'quality': quality, 
                'optimize': True
            }
            
            if output_format.upper() == 'JPEG':
                save_kwargs['progressive'] = True
            
            img.save(output_buffer, format=output_format.upper(), **save_kwargs)
            compressed_content = output_buffer.getvalue()
            compressed_size = len(compressed_content)
            
            # 计算压缩信息
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            print(f"✅ 图片压缩完成: {original_size/1024/1024:.2f}MB -> {compressed_size/1024/1024:.2f}MB (压缩率: {compression_ratio:.1f}%)")
            
            # 创建新的文件名
            name, ext = os.path.splitext(filename)
            if output_format.upper() == 'JPEG':
                new_ext = '.jpg'
            else:
                new_ext = ext
            
            compressed_filename = f"{name}_compressed{new_ext}"
            
            # 创建ContentFile - 确保使用正确的文件名
            compressed_file = ContentFile(compressed_content)
            compressed_file.name = compressed_filename
            
            compression_info = {
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': compression_ratio,
                'original_dimensions': (original_width, original_height),
                'compressed_dimensions': (new_width, new_height),
                'format': output_format
            }
            
            return compressed_file, compression_info
            
        except Exception as e:
            print(f"❌ 图片压缩失败 {filename}: {str(e)}")
            traceback.print_exc()
            # 返回原始内容
            original_file = ContentFile(image_content)
            original_file.name = filename
            return original_file, None

    @staticmethod
    def should_compress_image(image_content, threshold_mb=0.1):
        """检查图片是否需要压缩"""
        size_mb = len(image_content) / (1024 * 1024)
        should_compress = size_mb > threshold_mb
        print(f"🔍 图片压缩检查: {size_mb:.2f}MB > {threshold_mb}MB = {should_compress}")
        return should_compress


class VideoCompressionHandler:
    """视频压缩处理器"""
    
    @staticmethod
    def compress_video_content(video_content, filename, max_width=1280, max_height=720, crf=23):
        """
        压缩视频内容
        修复：确保在处理完成前不删除原始临时文件
        """
        temp_input_path = None
        temp_output_path = None
        
        try:
            original_size = len(video_content)
            print(f"🔍 开始压缩视频: {filename}, 原始大小: {original_size/1024/1024:.2f}MB")

            temp_dir = tempfile.mkdtemp(prefix='video_compress_')

            input_ext = os.path.splitext(filename)[1]
            temp_input_path = os.path.join(temp_dir, f'input{input_ext}')

            with open(temp_input_path, 'wb') as f:
                f.write(video_content)

            temp_output_path = os.path.join(temp_dir, 'output.mp4')

            cmd = [
                'ffmpeg',  
                '-i', temp_input_path,
                '-vf', f'scale=min({max_width},iw):min({max_height},ih):force_original_aspect_ratio=decrease',
                '-c:v', 'libx264',
                '-crf', str(crf),
                '-preset', 'medium',
                '-c:a', 'copy',
                '-movflags', '+faststart',
                '-y',
                temp_output_path
            ]

            print(f"🔍 执行FFmpeg命令: {' '.join(cmd)}")

            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=300  
            )

            if result.returncode != 0:
                print(f"❌ 视频压缩命令执行失败: {result.stderr}")
                raise Exception(f"FFmpeg error: {result.stderr}")

            if not os.path.exists(temp_output_path):
                raise Exception("压缩后的文件未生成")

            with open(temp_output_path, 'rb') as f:
                compressed_content = f.read()

            compressed_size = len(compressed_content)

            if compressed_size >= original_size:
                print(f"⚠️ 视频压缩导致文件变大 ({compressed_size/1024/1024:.2f}MB >= {original_size/1024/1024:.2f}MB)。将使用原始文件。")
                original_file = ContentFile(video_content)
                original_file.name = filename
                return original_file, None

            compression_ratio = (1 - compressed_size / original_size) * 100
            print(f"✅ 视频压缩完成: {original_size/1024/1024:.2f}MB -> {compressed_size/1024/1024:.2f}MB (压缩率: {compression_ratio:.1f}%)")

            name, ext = os.path.splitext(filename)
            compressed_filename = f"{name}_compressed.mp4"

            compressed_file = ContentFile(compressed_content)
            compressed_file.name = compressed_filename

            compression_info = {
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': compression_ratio
            }
            
            return compressed_file, compression_info

        except subprocess.TimeoutExpired:
            print(f"❌ 视频压缩超时 {filename}")
            original_file = ContentFile(video_content)
            original_file.name = filename
            return original_file, None
            
        except Exception as e:
            print(f"❌ 视频压缩失败 {filename}: {str(e)}")
            traceback.print_exc()
            original_file = ContentFile(video_content)
            original_file.name = filename
            return original_file, None

        finally:
            # ✅ 修复6: 清理整个临时目录
            try:
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    print(f"🗑️ 已清理临时目录: {temp_dir}")
            except Exception as e:
                print(f"⚠️ 清理临时目录失败: {str(e)}")

    @staticmethod
    def should_compress_video(video_content, threshold_mb=0.5):
        """检查视频是否需要压缩"""
        size_mb = len(video_content) / (1024 * 1024)
        should_compress = size_mb > threshold_mb
        print(f"🔍 视频压缩检查: {size_mb:.2f}MB > {threshold_mb}MB = {should_compress}")
        return should_compress


class FileCompressionManager:
    """文件压缩管理器"""
    
    @staticmethod
    def process_uploaded_file(file_content, filename, file_type=None):
        """
        处理上传的文件内容，进行压缩
        file_content: 文件的二进制内容（bytes）
        filename: 原始文件名
        file_type: 文件类型 ('image' 或 'video')，None则自动检测
        """
        print(f"🔍 开始处理文件: {filename}, 大小: {len(file_content)/1024/1024:.2f}MB, 类型: {file_type}")
        
        if file_type is None:
            # 自动检测文件类型
            filename_lower = filename.lower()
            if any(filename_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif']):
                file_type = 'image'
            elif any(filename_lower.endswith(ext) for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']):
                file_type = 'video'
            else:
                # 不支持的文件类型，直接返回
                print(f"⚠️ 不支持的文件类型: {filename}")
                original_file = ContentFile(file_content)
                original_file.name = filename
                return original_file, None
        
        # 根据文件类型选择处理器
        if file_type == 'image':
            if ImageCompressionHandler.should_compress_image(file_content):
                result = ImageCompressionHandler.compress_image_content(file_content, filename)
                if result[1]:
                    print(f"✅ 图片压缩结果: 压缩率 {result[1]['compression_ratio']:.1f}%")
                else:
                    print(f"⚠️ 图片压缩失败，使用原文件")
                return result
            else:
                print(f"ℹ️ 图片无需压缩: {filename}")
                original_file = ContentFile(file_content)
                original_file.name = filename
                return original_file, None
        
        elif file_type == 'video':
            if VideoCompressionHandler.should_compress_video(file_content):
                result = VideoCompressionHandler.compress_video_content(file_content, filename)
                if result[1]:
                    print(f"✅ 视频压缩结果: 压缩率 {result[1]['compression_ratio']:.1f}%")
                else:
                    print(f"⚠️ 视频压缩失败或文件变大，使用原文件")
                return result
            else:
                print(f"ℹ️ 视频无需压缩: {filename}")
                original_file = ContentFile(video_content)
                original_file.name = filename
                return original_file, None
        
        # 默认返回原始文件
        print(f"ℹ️ 返回原始文件: {filename}")
        original_file = ContentFile(file_content)
        original_file.name = filename
        return original_file, None

# ✅ 新增: 辅助函数 - 用于在 Django 视图/信号中处理文件
def compress_uploaded_file(uploaded_file, file_type=None):
    """
    处理 Django UploadedFile 对象
    
    参数:
        uploaded_file: Django UploadedFile 对象
        file_type: 'image' 或 'video'，None 则自动检测
    
    返回:
        (compressed_file, compression_info) 元组
    """
    try:
        # 读取文件内容
        uploaded_file.seek(0)  # 确保从头开始读
        file_content = uploaded_file.read()
        
        # 处理文件
        compressed_file, compression_info = FileCompressionManager.process_uploaded_file(
            file_content,
            uploaded_file.name,
            file_type
        )
        
        return compressed_file, compression_info
        
    except Exception as e:
        print(f"❌ 文件压缩处理失败: {str(e)}")
        traceback.print_exc()
        uploaded_file.seek(0)
        return uploaded_file, None
