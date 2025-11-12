# api/management/commands/check_compression.py
# ✅ 创建目录: api/management/commands/ (如果不存在)
# ✅ 同时创建 __init__.py 文件在 management 和 commands 目录

from django.core.management.base import BaseCommand
from api.models import MaterialVideo, MaterialImage, Material
import os
from django.db.models import Sum, Count
from django.conf import settings

class Command(BaseCommand):
    help = '检查素材压缩状态和存储统计'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='显示详细的文件列表',
        )
        parser.add_argument(
            '--large-files',
            type=float,
            default=50.0,
            help='显示大于指定大小(MB)的文件,默认50MB',
        )

    def handle(self, *args, **options):
        detailed = options['detailed']
        large_threshold = options['large_files']
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('📊 素材压缩状态报告'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
        
        # ========== 视频统计 ==========
        self.stdout.write(self.style.HTTP_INFO('🎬 视频压缩统计:'))
        self.stdout.write('-'*60)
        
        videos = MaterialVideo.objects.all()
        total_videos = videos.count()
        
        if total_videos == 0:
            self.stdout.write(self.style.WARNING('  ⚠️  暂无视频数据\n'))
        else:
            total_video_size = 0
            compressed_count = 0
            large_videos = []
            missing_thumbs = 0
            
            for vid in videos:
                if vid.video:
                    try:
                        video_path = vid.video.path
                        if os.path.exists(video_path):
                            size_mb = os.path.getsize(video_path) / (1024*1024)
                            total_video_size += size_mb
                            
                            if '_compressed' in vid.video.name:
                                compressed_count += 1
                            
                            if size_mb > large_threshold:
                                large_videos.append((vid.id, vid.video.name, size_mb))
                            
                            if not vid.thumbnail:
                                missing_thumbs += 1
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'  ⚠️  视频 {vid.id} 文件访问失败: {str(e)}'))
            
            self.stdout.write(f'  📦 总视频数: {total_videos}')
            self.stdout.write(f'  ✅ 已压缩: {compressed_count} ({compressed_count/total_videos*100:.1f}%)')
            self.stdout.write(f'  ❌ 未压缩: {total_videos - compressed_count} ({(total_videos-compressed_count)/total_videos*100:.1f}%)')
            self.stdout.write(f'  🖼️  缺少缩略图: {missing_thumbs}')
            self.stdout.write(f'  💾 总存储: {total_video_size:.2f} MB ({total_video_size/1024:.2f} GB)')
            self.stdout.write(f'  📊 平均大小: {total_video_size/total_videos:.2f} MB')
            
            if large_videos:
                self.stdout.write(f'\n  ⚠️  大文件 (>{large_threshold}MB):')
                for vid_id, name, size in sorted(large_videos, key=lambda x: x[2], reverse=True)[:10]:
                    self.stdout.write(f'      ID {vid_id}: {os.path.basename(name)} - {size:.2f} MB')
            
            self.stdout.write('')
        
        # ========== 图片统计 ==========
        self.stdout.write(self.style.HTTP_INFO('🖼️  图片压缩统计:'))
        self.stdout.write('-'*60)
        
        images = MaterialImage.objects.all()
        total_images = images.count()
        
        if total_images == 0:
            self.stdout.write(self.style.WARNING('  ⚠️  暂无图片数据\n'))
        else:
            total_image_size = 0
            compressed_img_count = 0
            large_images = []
            
            for img in images:
                if img.image:
                    try:
                        image_path = img.image.path
                        if os.path.exists(image_path):
                            size_mb = os.path.getsize(image_path) / (1024*1024)
                            total_image_size += size_mb
                            
                            if '_compressed' in img.image.name:
                                compressed_img_count += 1
                            
                            if size_mb > 5:  # 图片超过5MB算大文件
                                large_images.append((img.id, img.image.name, size_mb))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'  ⚠️  图片 {img.id} 文件访问失败: {str(e)}'))
            
            self.stdout.write(f'  📦 总图片数: {total_images}')
            self.stdout.write(f'  ✅ 已压缩: {compressed_img_count} ({compressed_img_count/total_images*100:.1f}%)')
            self.stdout.write(f'  ❌ 未压缩: {total_images - compressed_img_count} ({(total_images-compressed_img_count)/total_images*100:.1f}%)')
            self.stdout.write(f'  💾 总存储: {total_image_size:.2f} MB ({total_image_size/1024:.2f} GB)')
            self.stdout.write(f'  📊 平均大小: {total_image_size/total_images:.2f} MB')
            
            if large_images:
                self.stdout.write(f'\n  ⚠️  大图片 (>5MB):')
                for img_id, name, size in sorted(large_images, key=lambda x: x[2], reverse=True)[:10]:
                    self.stdout.write(f'      ID {img_id}: {os.path.basename(name)} - {size:.2f} MB')
            
            self.stdout.write('')
        
        # ========== Material 头图统计 ==========
        self.stdout.write(self.style.HTTP_INFO('📸 Material 头图统计:'))
        self.stdout.write('-'*60)
        
        materials = Material.objects.exclude(header_image='')
        total_headers = materials.count()
        
        if total_headers == 0:
            self.stdout.write(self.style.WARNING('  ⚠️  暂无头图数据\n'))
        else:
            total_header_size = 0
            compressed_header_count = 0
            
            for mat in materials:
                if mat.header_image:
                    try:
                        header_path = mat.header_image.path
                        if os.path.exists(header_path):
                            size_mb = os.path.getsize(header_path) / (1024*1024)
                            total_header_size += size_mb
                            
                            if '_compressed' in mat.header_image.name:
                                compressed_header_count += 1
                    except:
                        pass
            
            self.stdout.write(f'  📦 总头图数: {total_headers}')
            self.stdout.write(f'  ✅ 已压缩: {compressed_header_count} ({compressed_header_count/total_headers*100:.1f}%)')
            self.stdout.write(f'  💾 总存储: {total_header_size:.2f} MB')
            self.stdout.write(f'  📊 平均大小: {total_header_size/total_headers:.2f} MB')
            self.stdout.write('')
        
        # ========== 总体统计 ==========
        total_size = total_video_size + total_image_size + total_header_size
        total_files = total_videos + total_images + total_headers
        
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('📈 总体统计:'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'  📦 总文件数: {total_files}')
        self.stdout.write(f'  💾 总存储空间: {total_size:.2f} MB ({total_size/1024:.2f} GB)')
        if total_files > 0:
            self.stdout.write(f'  📊 平均文件大小: {total_size/total_files:.2f} MB')
        self.stdout.write('')
        
        # ========== 优化建议 ==========
        self.stdout.write(self.style.WARNING('💡 优化建议:'))
        self.stdout.write('-'*60)
        
        suggestions = []
        
        if total_videos > 0:
            uncompressed_videos = total_videos - compressed_count
            if uncompressed_videos > 0:
                suggestions.append(f'  🔧 有 {uncompressed_videos} 个视频未压缩,建议重新上传或手动触发压缩')
        
        if missing_thumbs > 0:
            suggestions.append(f'  🖼️  有 {missing_thumbs} 个视频缺少缩略图,建议运行缩略图生成任务')
        
        if large_videos:
            suggestions.append(f'  ⚠️  有 {len(large_videos)} 个大视频文件(>{large_threshold}MB),考虑降低质量或分段')
        
        if total_size > 10240:  # 超过10GB
            suggestions.append(f'  💾 总存储空间已超过 {total_size/1024:.1f}GB,建议清理或归档旧文件')
        
        if suggestions:
            for suggestion in suggestions:
                self.stdout.write(self.style.WARNING(suggestion))
        else:
            self.stdout.write(self.style.SUCCESS('  ✅ 当前压缩状态良好,无需特别优化'))
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✅ 报告生成完成'))
        self.stdout.write('='*60 + '\n')
        
        # ========== 详细列表 ==========
        if detailed:
            self.stdout.write(self.style.HTTP_INFO('\n📋 详细文件列表:\n'))
            
            self.stdout.write('视频文件:')
            for vid in videos[:20]:
                if vid.video:
                    try:
                        size = os.path.getsize(vid.video.path) / (1024*1024)
                        status = '✅' if '_compressed' in vid.video.name else '❌'
                        thumb_status = '🖼️ ' if vid.thumbnail else '⚠️ '
                        self.stdout.write(f'  {status} {thumb_status} ID {vid.id}: {os.path.basename(vid.video.name)} ({size:.2f}MB)')
                    except:
                        pass
            
            if videos.count() > 20:
                self.stdout.write(f'  ... 还有 {videos.count()-20} 个视频')
            
            self.stdout.write('')