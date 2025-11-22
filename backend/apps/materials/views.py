from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, filters, status, generics
from rest_framework.decorators import action,api_view, parser_classes
from django.core.cache import cache

from .models import Destination, Material
from .serializers import (
    MaterialSerializer,
    DestinationSerializer,
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

import re
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from django.template.loader import render_to_string

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
    url_path='download-pdf',  # ✅ 使用新的 URL
    permission_classes=[AllowAny])
    def download_pdf(self, request, pk=None):
        """
        使用 WeasyPrint 生成 PDF（支持 emoji 表情）
        """
        material = get_object_or_404(Material, pk=pk)
        
        # 如果是路线类型且已有上传的 PDF
        if material.material_type == 'route' and material.pdf_file:
            filename = f"{material.get_material_type_display()}_{material.title}_{material.id}.pdf"
            filename = re.sub(r'[<>:"/\\|?*]', '', filename).strip()
            from urllib.parse import quote
            encoded_filename = quote(filename)
            
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
        
        # ===== 准备数据 =====
        site_url = request.build_absolute_uri('/')[:-1]
        
         # ✅ 获取头图 URL(第一张图片)
        header_image_url = None
        first_image = material.images.first()
        if first_image:
            header_image_url = site_url + first_image.image.url

        # 处理描述中的图片路径
        description_html = material.description or ''
        if description_html:
            description_html = description_html.replace('src="/media/', f'src="{site_url}/media/')
            description_html = description_html.replace("src='/media/", f"src='{site_url}/media/")
        

        gallery_images = [
        {
            'url': site_url + img.image.url,
            'description': img.description or ''
            } 
            for img in material.images.all()[1:]  # [1:] 跳过第一张
            ]
        
        # ===== 构造 HTML 内容 =====
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
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
                    border-radius: 6px;
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
                
                .description img {{
                    width: 100%;
                    height: 180px;
                    object-fit: cover;
                    border-radius: 6px;
                    margin: 15px 0;
                    display: block;
                }}
                
                .price {{
                    color: #e74c3c;
                    font-size: 13pt;
                    font-weight: bold;
                }}
                
                .footer {{
                    margin-top: 40px;
                    padding-top: 15px;
                    border-top: 1px solid #ddd;
                    font-size: 9pt;
                    color: #999;
                }}
            </style>
        </head>
        <body>
            <h1>{material.get_material_type_display()}素材</h1>
            <h2>{material.title}</h2>
            
            {f'<img src="{site_url + material.header_image.url}" class="header-image" />' if material.header_image else ''}
            
            <div class="info-box">
                <p><strong>素材类型:</strong> {material.get_material_type_display()}</p>
                <p><strong>目的地:</strong> {material.destination.name if material.destination else '通用'}</p>
                <p><strong>创建时间:</strong> {material.created_at.strftime('%Y年%m月%d日 %H:%M')}</p>
                {f'<p><strong>价格:</strong> <span class="price">RM {material.price:.2f}</span></p>' if material.price else ''}
            </div>

            <h2>详细描述</h2>
            <div class="description">
                {description_html if description_html else '<p style="color: #999;">暂无详细描述</p>'}
            </div>

            {f'''
            <h2>素材库 ({len(gallery_images)} 张图片)</h2>
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
                <p>生成时间: {timezone.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
                <p>本文档由系统自动生成</p>
            </div>
        </body>
        </html>
        """
        
        # ===== 使用 WeasyPrint 生成 PDF =====
        try:
            # ✅ 配置字体支持
            font_config = FontConfiguration()
            
            # ✅ 生成 PDF
            html = HTML(string=html_content, base_url=site_url)
            pdf_content = html.write_pdf(font_config=font_config)
            
            # ✅ 返回响应
            response = HttpResponse(pdf_content, content_type='application/pdf')
            filename = f"{material.get_material_type_display()}_{material.title}_{material.id}.pdf"
            filename = re.sub(r'[<>:"/\\|?*]', '', filename).strip()
            from urllib.parse import quote
            encoded_filename = quote(filename)
            response['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
            
            return response
            
        except Exception as e:
            print(f"❌ WeasyPrint PDF生成错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return HttpResponse(f"PDF生成失败: {str(e)}", status=500)



class DestinationViewSet(viewsets.ReadOnlyModelViewSet):
    """提供所有目的地的列表，用于前端筛选。"""
    queryset = Destination.objects.all().order_by('name')
    serializer_class = DestinationSerializer