# backend/utils/compression_handler.py - ✅ 智能压缩策略版
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
import json
from django.utils import timezone

logger = logging.getLogger(__name__)
FFMPEG_PATH = '/usr/bin/ffmpeg'


class ImageCompressionHandler:
    """图片压缩处理器"""
    
    @staticmethod
    def compress_image_content(image_content, filename, max_size=(1920, 1080), quality=85):
        """压缩图片内容(在内存中处理)"""
        try:
            original_size = len(image_content)
            print(f"🔄 开始压缩图片: {filename}, 原始大小: {original_size/1024/1024:.2f}MB")
            
            image_buffer = BytesIO(image_content)
            img = Image.open(image_buffer)
            
            original_width, original_height = img.size
            print(f"📐 图片原始尺寸: {original_width}x{original_height}")
            
            if img.mode in ('P', 'RGBA'):
                img = img.convert('RGB')
                output_format = 'JPEG'
            else:
                output_format = img.format or 'JPEG'
            
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            new_width, new_height = img.size
            print(f"📐 压缩后尺寸: {new_width}x{new_height}")
            
            img = ImageOps.exif_transpose(img)
            
            output_buffer = BytesIO()
            
            save_kwargs = {
                'quality': quality, 
                'optimize': True
            }
            
            if output_format.upper() == 'JPEG':
                save_kwargs['progressive'] = True
            
            img.save(output_buffer, format=output_format.upper(), **save_kwargs)
            compressed_content = output_buffer.getvalue()
            compressed_size = len(compressed_content)
            
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            print(f"✅ 图片压缩完成: {original_size/1024/1024:.2f}MB -> {compressed_size/1024/1024:.2f}MB (压缩率: {compression_ratio:.1f}%)")
            
            name, ext = os.path.splitext(filename)
            if output_format.upper() == 'JPEG':
                new_ext = '.jpg'
            else:
                new_ext = ext
            
            compressed_filename = f"{name}_compressed{new_ext}"
            
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
            original_file = ContentFile(image_content)
            original_file.name = filename
            return original_file, None

    @staticmethod
    def should_compress_image(image_content, threshold_mb=0.1):
        """检查图片是否需要压缩"""
        size_mb = len(image_content) / (1024 * 1024)
        should_compress = size_mb > threshold_mb
        print(f"📊 图片压缩检查: {size_mb:.2f}MB > {threshold_mb}MB = {should_compress}")
        return should_compress


class VideoCompressionHandler:
    """视频压缩处理器 - 智能策略版"""
    
    @staticmethod
    def get_video_info(video_path):
        """获取视频详细信息"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            return None
        except Exception as e:
            print(f"⚠️ 获取视频信息失败: {str(e)}")
            return None
    
    @staticmethod
    def analyze_video_quality(video_info):
        """
        ✅ 新增: 分析视频质量,决定是否需要压缩
        返回: (should_compress, recommended_crf, reason)
        """
        if not video_info:
            return True, 28, "无法获取视频信息,使用默认压缩"
        
        format_info = video_info.get('format', {})
        video_stream = None
        audio_stream = None
        
        # 找到视频流和音频流
        for stream in video_info.get('streams', []):
            if stream.get('codec_type') == 'video' and not video_stream:
                video_stream = stream
            elif stream.get('codec_type') == 'audio' and not audio_stream:
                audio_stream = stream
        
        if not video_stream:
            return True, 28, "找不到视频流"
        
        # 获取关键参数
        try:
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            bit_rate = int(format_info.get('bit_rate', 0))
            duration = float(format_info.get('duration', 0))
            codec = video_stream.get('codec_name', '')
            
            # 计算视频码率 (bit/s)
            if bit_rate == 0 and duration > 0:
                size_bits = int(format_info.get('size', 0)) * 8
                bit_rate = int(size_bits / duration)
            
            # 转换为 kbps
            video_bitrate_kbps = bit_rate / 1000
            
            print(f"📹 视频分析: {width}x{height}, {codec}, {video_bitrate_kbps:.0f}kbps")
            
            # ✅ 智能判断策略
            
            # 1. 如果已经是低码率视频,不压缩
            if video_bitrate_kbps < 1500:
                return False, 0, f"已经是低码率视频 ({video_bitrate_kbps:.0f}kbps)"
            
            # 2. 如果分辨率已经很低,不压缩
            if width <= 854 and height <= 480:  # 480p 或更低
                return False, 0, f"分辨率已经很低 ({width}x{height})"
            
            # 3. 如果是 H.264 且码率合理,不压缩
            if codec in ['h264', 'avc'] and video_bitrate_kbps < 3000:
                return False, 0, f"已经是优化的 H.264 ({video_bitrate_kbps:.0f}kbps)"
            
            # 4. 高分辨率高码率视频需要压缩
            if width >= 1920 and video_bitrate_kbps > 5000:
                return True, 26, f"高分辨率高码率 ({width}x{height}, {video_bitrate_kbps:.0f}kbps)"
            
            # 5. 中等分辨率高码率视频
            if video_bitrate_kbps > 3000:
                return True, 28, f"码率较高 ({video_bitrate_kbps:.0f}kbps)"
            
            # 默认不压缩
            return False, 0, "视频质量已合理"
            
        except Exception as e:
            print(f"⚠️ 视频质量分析失败: {str(e)}")
            return True, 28, "分析失败,使用默认压缩"
    
    @staticmethod
    def compress_video_content(video_content, filename, max_width=1280, max_height=720, crf=None):
        """
        压缩视频内容 - 智能策略版
        crf=None 时会自动分析决定
        """
        temp_dir = None
        temp_input_path = None
        temp_output_path = None
        log_file = None
        
        try:
            original_size = len(video_content)
            print(f"🔄 开始分析视频: {filename}, 原始大小: {original_size/1024/1024:.2f}MB")

            temp_dir = tempfile.mkdtemp(prefix='video_compress_')
            input_ext = os.path.splitext(filename)[1]
            temp_input_path = os.path.join(temp_dir, f'input{input_ext}')

            with open(temp_input_path, 'wb') as f:
                f.write(video_content)

            # ✅ 获取视频信息并分析
            video_info = VideoCompressionHandler.get_video_info(temp_input_path)
            
            # ✅ 智能判断是否需要压缩
            should_compress, recommended_crf, reason = VideoCompressionHandler.analyze_video_quality(video_info)
            
            print(f"💡 压缩策略: {reason}")
            
            if not should_compress:
                print(f"ℹ️ 视频无需压缩,使用原文件")
                original_file = ContentFile(video_content)
                original_file.name = filename
                return original_file, None
            
            # 使用推荐的 CRF 值
            if crf is None:
                crf = recommended_crf
            
            print(f"🎯 使用 CRF={crf} 进行压缩")
            
            # 提取音频信息
            has_audio = False
            audio_bitrate = 0
            video_duration = 0
            
            if video_info:
                streams = video_info.get('streams', [])
                for stream in streams:
                    if stream.get('codec_type') == 'audio':
                        has_audio = True
                        audio_bitrate = int(stream.get('bit_rate', 128000)) / 1000  # 转为 kbps
                        print(f"🔊 音频: {stream.get('codec_name')}, {audio_bitrate:.0f}kbps")
                        break
                
                format_info = video_info.get('format', {})
                try:
                    video_duration = float(format_info.get('duration', 0))
                except:
                    pass

            temp_output_path = os.path.join(temp_dir, 'output.mp4')

            # ✅ 构建智能 FFmpeg 命令
            cmd = [
                'ffmpeg',
                '-i', temp_input_path,
                '-vf', f'scale=w=min({max_width}\\,iw):h=min({max_height}\\,ih):force_original_aspect_ratio=decrease',
                '-c:v', 'libx264',
                '-crf', str(crf),
                '-preset', 'medium',
                '-profile:v', 'main',
                '-level', '4.0',
            ]
            
            # ✅ 智能音频处理
            if has_audio:
                # 如果原音频码率低于128k,保持原样;否则压缩到128k
                if audio_bitrate > 0 and audio_bitrate < 128:
                    cmd.extend(['-c:a', 'copy'])  # 保持原音频
                    print(f"🔊 音频策略: 保持原音频 ({audio_bitrate:.0f}kbps)")
                else:
                    cmd.extend([
                        '-c:a', 'aac',
                        '-b:a', '96k',  # ✅ 降低音频码率到 96k
                        '-ar', '44100',
                    ])
                    print(f"🔊 音频策略: 压缩到 96kbps")
            else:
                cmd.extend(['-an'])
            
            cmd.extend([
                '-movflags', '+faststart',
                '-y',
                temp_output_path
            ])

            print(f"🎬 执行压缩...")

            # 动态超时
            if video_duration > 0:
                timeout = max(120, int(video_duration * 2 + 60))
            else:
                timeout = 300

            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=timeout
            )

            if result.returncode != 0:
                # 保存错误日志
                try:
                    log_dest_dir = os.path.join(settings.MEDIA_ROOT, 'compression_logs')
                    os.makedirs(log_dest_dir, exist_ok=True)
                    
                    log_filename = f"{os.path.splitext(filename)[0]}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.log"
                    log_dest = os.path.join(log_dest_dir, log_filename)
                    
                    with open(log_dest, 'w', encoding='utf-8') as f:
                        f.write(f"=== FFmpeg 命令 ===\n{' '.join(cmd)}\n\n")
                        f.write(f"=== 返回码 ===\n{result.returncode}\n\n")
                        f.write(f"=== STDERR ===\n{result.stderr}")
                    
                    print(f"📝 错误日志已保存: {log_dest}")
                except Exception as log_err:
                    print(f"⚠️ 保存日志失败: {str(log_err)}")
                
                raise Exception(f"FFmpeg压缩失败 (返回码: {result.returncode})")

            if not os.path.exists(temp_output_path):
                raise Exception("压缩后的文件未生成")

            with open(temp_output_path, 'rb') as f:
                compressed_content = f.read()

            compressed_size = len(compressed_content)
            
            # ✅ 只有压缩效果好才使用压缩版本
            if compressed_size >= original_size * 0.95:  # 压缩不到5%就放弃
                print(f"⚠️ 压缩效果不明显: {original_size/1024/1024:.2f}MB -> {compressed_size/1024/1024:.2f}MB (仅减少 {(1-compressed_size/original_size)*100:.1f}%)")
                print(f"ℹ️ 使用原始文件")
                original_file = ContentFile(video_content)
                original_file.name = filename
                return original_file, None

            compression_ratio = (1 - compressed_size / original_size) * 100
            print(f"✅ 视频压缩成功: {original_size/1024/1024:.2f}MB -> {compressed_size/1024/1024:.2f}MB (减少 {compression_ratio:.1f}%)")

            name, ext = os.path.splitext(filename)
            compressed_filename = f"{name}_compressed.mp4"

            compressed_file = ContentFile(compressed_content)
            compressed_file.name = compressed_filename

            compression_info = {
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': compression_ratio,
                'has_audio': has_audio,
                'duration': video_duration,
                'crf_used': crf,
                'strategy': reason
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
            try:
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"⚠️ 清理临时目录失败: {str(e)}")

    @staticmethod
    def should_compress_video(video_content, threshold_mb=10.0):  # ✅ 提高阈值到 10MB
        """检查视频是否需要压缩"""
        size_mb = len(video_content) / (1024 * 1024)
        should_compress = size_mb > threshold_mb
        print(f"📊 视频大小检查: {size_mb:.2f}MB > {threshold_mb}MB = {should_compress}")
        return should_compress


class FileCompressionManager:
    """文件压缩管理器"""
    
    @staticmethod
    def process_uploaded_file(file_content, filename, file_type=None):
        """处理上传的文件内容,进行压缩"""
        print(f"🔍 开始处理文件: {filename}, 大小: {len(file_content)/1024/1024:.2f}MB, 类型: {file_type}")
        
        if file_type is None:
            filename_lower = filename.lower()
            if any(filename_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif']):
                file_type = 'image'
            elif any(filename_lower.endswith(ext) for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']):
                file_type = 'video'
            else:
                print(f"⚠️ 不支持的文件类型: {filename}")
                original_file = ContentFile(file_content)
                original_file.name = filename
                return original_file, None
        
        if file_type == 'image':
            if ImageCompressionHandler.should_compress_image(file_content):
                result = ImageCompressionHandler.compress_image_content(file_content, filename)
                if result[1]:
                    print(f"✅ 图片压缩结果: 压缩率 {result[1]['compression_ratio']:.1f}%")
                else:
                    print(f"⚠️ 图片压缩失败,使用原文件")
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
                    print(f"✅ 视频压缩结果: 减少 {result[1]['compression_ratio']:.1f}%")
                else:
                    print(f"ℹ️ 视频无需压缩或压缩效果不佳,使用原文件")
                return result
            else:
                print(f"ℹ️ 视频文件较小,无需压缩: {filename}")
                original_file = ContentFile(file_content)
                original_file.name = filename
                return original_file, None
        
        print(f"ℹ️ 返回原始文件: {filename}")
        original_file = ContentFile(file_content)
        original_file.name = filename
        return original_file, None


def compress_uploaded_file(uploaded_file, file_type=None):
    """处理 Django UploadedFile 对象"""
    try:
        uploaded_file.seek(0)
        file_content = uploaded_file.read()
        
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