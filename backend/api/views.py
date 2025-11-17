from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, filters, status, generics
from rest_framework.decorators import action,api_view, parser_classes
from django.core.cache import cache

from .models import Destination, Material, SupportTicket
from .serializers import (
    UserSerializer,
    MaterialSerializer,
    DestinationSerializer,
    SupportTicketSerializer,
    MaterialImageSerializer,
    MaterialVideoSerializer
)
from django.http import FileResponse, HttpResponse
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from django.shortcuts import get_object_or_404

from django.conf import settings
import os
import requests
from io import BytesIO 

from django.db.models import Q
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination
from xhtml2pdf import pisa
import re



class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class AvatarUploadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        user = request.user
        avatar_file = request.FILES.get('avatars') 
        
        if not avatar_file:
            return Response(
                {"detail": "未提供头像文件"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 验证文件类型
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if avatar_file.content_type not in allowed_types:
            return Response(
                {"detail": "只支持 JPEG、PNG 和 GIF 格式的图片"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 验证文件大小 (最大 2MB)
        if avatar_file.size > 2 * 1024 * 1024:
            return Response(
                {"detail": "头像文件不能超过 2MB"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 保存头像
            user.profile.avatar = avatar_file
            user.profile.save()
            
            # 返回更新后的用户信息
            serializer = UserSerializer(user)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {"detail": f"上传失败: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MaterialPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100

class MaterialViewSet(viewsets.ModelViewSet):
    """
    提供素材库的只读列表和详情接口。
    支持通过查询参数进行过滤:
    - ?material_type=hotel
    - ?destination__slug=kuala-lumpur
    - ?search=...
    """
    serializer_class = MaterialSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description', 'destination__name']
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = MaterialPagination 
    def get_queryset(self):
        queryset = Material.objects.all().select_related('destination').prefetch_related('images')
        
        # 根据类型过滤
        material_type = self.request.query_params.get('material_type')
        if material_type:
            queryset = queryset.filter(material_type=material_type)
            
        # 根据目的地过滤
        destination_slug = self.request.query_params.get('destination__slug')
        if destination_slug:
            queryset = queryset.filter(destination__slug=destination_slug)
            
        return queryset


    def create(self, request, *args, **kwargs):
        # 处理多图片上传
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # 处理多图片上传
        return super().update(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        # 优化缓存 key
        query_params = request.query_params.urlencode()
        cache_key = f"material_list_{query_params}"
        data = cache.get(cache_key)
        if not data:
            response = super().list(request, *args, **kwargs)
            cache.set(cache_key, response.data, 60 * 5)  # 缓存 5 分钟
            return response
        return Response(data)

    @action(detail=True, methods=['post'], url_path='upload-images', permission_classes=[IsAuthenticated])
    def upload_images(self, request, pk=None):
        """
        批量上传图片到指定素材:
        - multipart/form-data with files[] multiple
        - 自动触发压缩逻辑(通过 signals)
        """
        material = get_object_or_404(Material, pk=pk)
        files = request.FILES.getlist('files')
        if not files:
            return Response({"detail": "未提供任何文件，参数名: files"}, status=status.HTTP_400_BAD_REQUEST)
        created = []
        from .models import MaterialImage
        for f in files:
            created.append(MaterialImage.objects.create(material=material, image=f))
        serializer = MaterialImageSerializer(created, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='upload-videos', permission_classes=[IsAuthenticated])
    def upload_videos(self, request, pk=None):
        """
        批量上传视频到指定素材:
        - multipart/form-data with files[] multiple
        - 自动触发压缩逻辑(通过 signals)
        """
        material = get_object_or_404(Material, pk=pk)
        files = request.FILES.getlist('files')
        if not files:
            return Response({"detail": "未提供任何文件，参数名: files"}, status=status.HTTP_400_BAD_REQUEST)
        created = []
        from .models import MaterialVideo
        for f in files:
            created.append(MaterialVideo.objects.create(material=material, video=f))
        serializer = MaterialVideoSerializer(created, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    @action(
        detail=True, 
        methods=['get'], 
        url_path='download-pdf',
        permission_classes=[AllowAny])


    def download_pdf(self, request, pk=None):
        """使用 xhtml2pdf 高保真导出素材详情为 PDF（支持酒店图库和CKEditor内容）"""
        material = get_object_or_404(Material, pk=pk)


        if material.material_type == 'route' and material.pdf_file:
            filename = f"{material.get_material_type_display()}_{material.title}_{material.id}.pdf"
            # 清理文件名
            filename = re.sub(r'[<>:"/\\|?*]', '', filename).strip()
            
            # 使用 URL 编码处理中文文件名
            from urllib.parse import quote
            encoded_filename = quote(filename)
            
            # 返回上传的PDF文件
            response = FileResponse(
                material.pdf_file.open('rb'), 
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
            return response

        # ===== 1. 检查字体文件 =====
        font_path = settings.PDF_FONT_PATH
        if not os.path.exists(font_path):
            return HttpResponse("PDF生成失败：字体文件未找到", status=500)
        
        # 获取字体的绝对路径
        font_abs_path = os.path.abspath(font_path)

        # ===== 2. 准备数据 =====
        site_url = request.build_absolute_uri('/')[:-1]
        header_img_url = site_url + material.header_image.url if material.header_image else None
        
        # 获取酒店图库
        gallery_images = []
        if material.material_type == 'hotel':
            gallery_images = [
                {
                    'url': site_url + img.image.url,
                    'description': img.description or ''
                } 
                for img in material.images.all()
            ]

        # 处理CKEditor内容 - 确保图片路径完整
        description_html = material.description or ''
        if description_html:
            description_html = description_html.replace('src="/media/', f'src="{site_url}/media/')
            description_html = description_html.replace("src='/media/", f"src='{site_url}/media/")

        # ===== 3. 构造 HTML 模板（使用绝对路径的字体）=====
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
            <style>
                @page {{
                    size: A4;
                    margin: 2cm 1.5cm;
                }}
                @font-face {{
                    font-family: ChineseFont;
                    src: url("file://{font_abs_path}");
                }}
                * {{
                    font-family: ChineseFont;
                }}
                body {{
                    color: #222;
                    line-height: 1.6;
                    font-size: 11pt;
                }}
                h1 {{
                    color: #2C3E50;
                    font-size: 20pt;
                    margin-bottom: 15px;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 8px;
                }}
                h2 {{
                    color: #34495E;
                    font-size: 14pt;
                    border-bottom: 2px solid #95a5a6;
                    padding-bottom: 4px;
                    margin-top: 25px;
                    margin-bottom: 12px;
                }}
                h3 {{
                    color: #555;
                    font-size: 12pt;
                    margin-top: 15px;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                    margin: 10px 0;
                    border-radius: 6px;
                }}
                .header-image {{
                    width: 85%;
                    height: 500px;
                    object-fit: cover;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    display: block;
                }}
                .info-box {{
                    background: #f8f9fa;
                    border-left: 4px solid #3498db;
                    padding: 12px 15px;
                    margin: 15px 0;
                    border-radius: 4px;
                }}
                .info-box p {{
                    margin: 5px 0;
                }}
                .gallery {{
                    margin-top: 20px;
                }}
                .gallery-item {{
                    margin-bottom: 20px;
                    page-break-inside: avoid;
                }}
                .gallery-item img {{
                    width: 85%;
                    height: 400px;
                    object-fit: cover;
                    border: 0px solid #ddd;
                    border-radius: 6px;
                    display: block;
                }}
                .description img {{
                    width: 100%;
                    height: 180px;
                    object-fit: cover;
                    border-radius: 6px;
                    margin: 15px 0;
                    display: block;
                }}
                .gallery-item p {{
                    font-size: 9pt;
                    color: #666;
                    margin-top: 5px;
                    font-style: italic;
                }}
                .description {{
                    margin-top: 20px;
                    text-align: justify;
                }}
                .description p {{
                    margin: 8px 0;
                }}
                .description ul, .description ol {{
                    margin: 10px 0;
                    padding-left: 25px;
                }}
                .description li {{
                    margin: 5px 0;
                }}
                .description table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }}
                .description table td, .description table th {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    font-size: 10pt;
                }}
                .description table th {{
                    background-color: #f2f2f2;
                    font-weight: bold;
                }}
                .description blockquote {{
                    border-left: 3px solid #ccc;
                    padding-left: 15px;
                    color: #666;
                    font-style: italic;
                    margin: 15px 0;
                }}
                .description strong {{
                    font-weight: bold;
                }}
                .description em {{
                    font-style: italic;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 15px;
                    border-top: 1px solid #ddd;
                    font-size: 9pt;
                    color: #999;
                }}
                .price {{
                    color: #e74c3c;
                    font-size: 13pt;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <h1>{material.get_material_type_display()}素材</h1>
            <h2>{material.title}</h2>
            {f'<img src="{header_img_url}" class="header-image" />' if header_img_url else ''}
            <div class="info-box">
                <p><strong>素材类型：</strong> {material.get_material_type_display()}</p>
                <p><strong>目的地：</strong> {material.destination.name if material.destination else '通用'}</p>
                <p><strong>创建时间：</strong> {material.created_at.strftime('%Y年%m月%d日 %H:%M')}</p>
                {f'<p><strong>价格：</strong> <span class="price">RM {material.price:.2f}</span></p>' if material.price else ''}
            </div>

   

            <h2>详细描述</h2>
            <div class="description">
                {description_html if description_html else '<p style="color: #999;">暂无详细描述</p>'}
            </div>

            {f'''
            <h2>酒店图库 ({len(gallery_images)} 张图片)</h2>
            <div class="gallery">
                {"".join([f"""
                <div class="gallery-item">
                    <img src="{img['url']}" />
                    {f"<p>{img['description']}</p>" if img['description'] else ""}
                </div>
                """ for img in gallery_images])}
            </div>
            ''' if gallery_images else ''}

            <div class="footer">
                <p>生成时间：{timezone.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
                <p>本文档由系统自动生成</p>
            </div>
        </body>
        </html>
        """

        # ===== 4. 关键：link_callback 处理资源（字体和图片）=====
        # def link_callback(uri, rel):
        #     """
        #     将URL转换为文件系统路径
        #     这是让 xhtml2pdf 找到字体和图片的关键！
        #     """
        #     # 处理字体文件
        #     if uri.startswith('file://'):
        #         return uri.replace('file://', '')
            
        #     # 处理图片
        #     if uri.startswith('http://') or uri.startswith('https://'):
        #         if '/media/' in uri:
        #             file_path = uri.split('/media/')[-1]
        #             full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        #         else:
        #             return uri
        #     elif uri.startswith('/media/'):
        #         file_path = uri.replace('/media/', '')
        #         full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        #     else:
        #         return uri
            
        #     if os.path.exists(full_path):
        #         return full_path
        #     else:
        #         print(f"⚠️ 文件未找到: {full_path}")
        #         return uri
        def link_callback(uri, rel):
            """
            将URL转换为文件系统路径
            这是让 xhtml2pdf 找到字体和图片的关键!
            """
            # 1️⃣ 处理字体文件(必须在最前面)
            if uri.startswith('file://'):
                return uri.replace('file://', '')
            
            # 2️⃣ 处理完整URL的图片(从CKEditor来的)
            if uri.startswith('http://') or uri.startswith('https://'):
                # 提取/media/后面的路径
                if '/media/' in uri:
                    # 使用split获取最后一个/media/后的内容
                    file_path = uri.split('/media/', 1)[-1]  # 只分割一次
                    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                    
                    # 调试:打印路径信息
                    print(f"🔍 处理URL: {uri}")
                    print(f"📁 提取路径: {file_path}")
                    print(f"💾 完整路径: {full_path}")
                    print(f"✅ 文件存在: {os.path.exists(full_path)}")
                    
                    if os.path.exists(full_path):
                        return full_path
                    else:
                        print(f"⚠️ 文件未找到: {full_path}")
                        return uri
                else:
                    # 外部URL,直接返回
                    return uri
            
            # 3️⃣ 处理相对路径的图片
            elif uri.startswith('/media/'):
                file_path = uri.replace('/media/', '')
                full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                
                print(f"🔍 处理相对路径: {uri}")
                print(f"💾 完整路径: {full_path}")
                
                if os.path.exists(full_path):
                    return full_path
                else:
                    print(f"⚠️ 文件未找到: {full_path}")
                    return uri
            
            # 4️⃣ 其他情况,直接返回原URI
            else:
                return uri

        # ===== 5. 生成 PDF =====
        response = HttpResponse(content_type='application/pdf')
        # 文件名格式：类型+标题+ID
        filename = f"{material.get_material_type_display()}_{material.title}_{material.id}.pdf"
        # 清理文件名中的特殊字符，但保留中文
        filename = re.sub(r'[<>:"/\\|?*]', '', filename).strip()
        
        # 使用 URL 编码处理中文文件名（支持各种浏览器）
        from urllib.parse import quote
        encoded_filename = quote(filename)
        
        # RFC 5987 标准格式，兼容所有浏览器
        response['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"

        # 创建PDF - 关键参数
        pisa_status = pisa.CreatePDF(
            html.encode('UTF-8'),  # 明确编码为 UTF-8
            dest=response,
            link_callback=link_callback,  # 使用 callback 处理资源
            encoding='UTF-8'
        )

        if pisa_status.err:
            print(f"❌ PDF生成错误: {pisa_status.err}")
            return HttpResponse("PDF生成失败，请查看日志", status=500)

        return response



class DestinationViewSet(viewsets.ReadOnlyModelViewSet):
    """提供所有目的地的列表，用于前端筛选。"""
    queryset = Destination.objects.all().order_by('name')
    serializer_class = DestinationSerializer

# 自定义分页类
class SupportTicketPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100

class SupportTicketViewSet(viewsets.ModelViewSet):
    queryset = SupportTicket.objects.all().order_by('-created_at')
    serializer_class = SupportTicketSerializer
    pagination_class = SupportTicketPagination  # 添加分页
    permission_classes = [AllowAny]  # 临时改为 AllowAny 进行测试
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]  # 添加 SearchFilter
    ordering_fields = ['created_at', 'category']
    ordering = ['-created_at']
    search_fields = ['question_text', 'answer_content']  # 添加搜索字段

    def get_queryset(self):
        qs = super().get_queryset().select_related('author', 'answered_by')
        
        # 状态筛选
        status_filter = self.request.query_params.get('status', 'all') 
        if status_filter == 'answered':
            qs = qs.filter(is_answered=True)
        elif status_filter == 'unanswered':
            qs = qs.filter(is_answered=False)
            
        # 关键词搜索 - 使用 DRF 的 SearchFilter 替代手动处理
        query = self.request.query_params.get('query', None)
        if query:
            qs = qs.filter(
                Q(question_text__icontains=query) |
                Q(answer_content__icontains=query)
            )
            
        # 分类筛选
        category = self.request.query_params.get('category', None)
        if category and category != 'all':
            qs = qs.filter(category=category)
            
        return qs

    def perform_create(self, serializer):
        # 如果没有用户信息，创建一个匿名用户或使用默认用户
        if self.request.user.is_authenticated:
            serializer.save(author=self.request.user)
        else:
            # 如果没有认证用户，可以设置为 None 或默认用户
            # 根据您的业务需求决定
            from django.contrib.auth.models import User
            default_user = User.objects.filter(is_staff=True).first()
            serializer.save(author=default_user)
        
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        answer_content = request.data.get('answer_content')
        
        if answer_content is not None:
            # 权限检查
            if not request.user.is_staff:
                return Response({"detail": "只有员工可以回答工单。"}, 
                                status=status.HTTP_403_FORBIDDEN)
            
            # 自动设置回答元数据
            if not instance.is_answered or answer_content != instance.answer_content:
                request.data['is_answered'] = True
                request.data['answered_by'] = request.user.pk
                request.data['answered_at'] = timezone.now()
        
        return super().partial_update(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """单个问题详情"""
        instance = self.get_object()
        cache_key = f"question_detail_{instance.id}"
        data = cache.get(cache_key)
        if not data:
            serializer = self.get_serializer(instance)
            data = serializer.data
            cache.set(cache_key, data, 60 * 5)
        return Response(data)

    # 添加 list 方法以确保正确响应格式
    def list(self, request, *args, **kwargs):
        # 清除缓存以确保获取最新数据
        cache.clear()
        return super().list(request, *args, **kwargs)