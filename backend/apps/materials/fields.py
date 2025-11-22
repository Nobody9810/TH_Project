from django.db.models import FileField, ImageField
from django.db.models.fields.files import FileField, ImageFieldFile
from .utils.compression_handler import FileCompressionManager
import logging

logger = logging.getLogger(__name__)

class CompressedFileField(FileField):
    """自动压缩的文件字段"""
    
    def __init__(self, *args, **kwargs):
        # 先提取自定义参数，然后再调用父类构造函数
        self.compression_enabled = kwargs.pop('compression_enabled', True)
        self.file_type = kwargs.pop('file_type', None)
        super().__init__(*args, **kwargs)
    
    def pre_save(self, model_instance, add):
        """在保存前处理文件压缩"""
        file = super().pre_save(model_instance, add)
        
        print(f"🔍 CompressedFileField.pre_save 被调用: {file.name if file else 'No file'}")
        
        if file and self.compression_enabled and not getattr(model_instance, '_compression_processed', False):
            print(f"🔍 开始处理文件压缩: {file.name}")
            try:
                # 读取文件内容
                file.open('rb')
                original_content = file.read()
                file.close()
                
                print(f"🔍 读取文件内容: {len(original_content)} bytes")
                
                # 处理压缩
                compressed_file, compression_info = FileCompressionManager.process_uploaded_file(
                    original_content, 
                    file.name,
                    self.file_type
                )
                
                if compressed_file and compression_info:
                    print(f"✅ 压缩成功，设置新文件")
                    # 保存压缩信息到模型实例
                    if not hasattr(model_instance, '_compression_data'):
                        model_instance._compression_data = {}
                    model_instance._compression_data[self.name] = compression_info
                    
                    # 设置压缩后的文件
                    setattr(model_instance, self.name, compressed_file)
                    
                    # 标记已处理，避免重复处理
                    model_instance._compression_processed = True
                    
                    print(f"✅ 文件字段 {self.name} 压缩完成")
                else:
                    print(f"⚠️ 压缩失败或未压缩，使用原文件")
                
            except Exception as e:
                print(f"❌ 文件压缩处理失败 {file.name}: {str(e)}")
        
        return file


class CompressedImageField(ImageField):
    """自动压缩的图片字段"""
    
    def __init__(self, *args, **kwargs):
        # 先提取自定义参数，然后再调用父类构造函数
        self.compression_enabled = kwargs.pop('compression_enabled', True)
        self.file_type = 'image'
        super().__init__(*args, **kwargs)
    
    def pre_save(self, model_instance, add):
        """在保存前处理文件压缩"""
        file = super().pre_save(model_instance, add)
        
        print(f"🔍 CompressedImageField.pre_save 被调用: {file.name if file else 'No file'}")
        
        if file and self.compression_enabled and not getattr(model_instance, '_compression_processed', False):
            print(f"🔍 开始处理图片压缩: {file.name}")
            try:
                # 读取文件内容
                file.open('rb')
                original_content = file.read()
                file.close()
                
                print(f"🔍 读取图片内容: {len(original_content)} bytes")
                
                # 处理压缩
                compressed_file, compression_info = FileCompressionManager.process_uploaded_file(
                    original_content, 
                    file.name,
                    self.file_type
                )
                
                if compressed_file and compression_info:
                    print(f"✅ 图片压缩成功，设置新文件")
                    # 保存压缩信息到模型实例
                    if not hasattr(model_instance, '_compression_data'):
                        model_instance._compression_data = {}
                    model_instance._compression_data[self.name] = compression_info
                    
                    # 设置压缩后的文件
                    setattr(model_instance, self.name, compressed_file)
                    
                    # 标记已处理，避免重复处理
                    model_instance._compression_processed = True
                    
                    print(f"✅ 图片字段 {self.name} 压缩完成")
                else:
                    print(f"⚠️ 图片压缩失败或未压缩，使用原文件")
                
            except Exception as e:
                print(f"❌ 图片压缩处理失败 {file.name}: {str(e)}")
        
        return file