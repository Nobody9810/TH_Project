from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, filters, status, generics
from rest_framework.decorators import action,api_view, parser_classes
from django.core.cache import cache
from rest_framework.permissions import AllowAny
from .models import Destination, Material, SupportTicket
from .serializers import (
    UserSerializer,
    MaterialSerializer,
    DestinationSerializer,
    SupportTicketSerializer 
)
from django.http import FileResponse, HttpResponse
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from django.shortcuts import get_object_or_404
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont 
from django.conf import settings
import os
import requests
from io import BytesIO 
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter,A4
from reportlab.lib.utils import simpleSplit
from reportlab.platypus import Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from django.db.models import Q
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination

FONT_NAME = 'PuHuiTi'
FONT_PATH = settings.PDF_FONT_PATH 
FONT_REGISTERED = False 

try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont(FONT_NAME, str(FONT_PATH)))
        FONT_REGISTERED = True
    else:
        print(f"⚠️ 严重警告：ReportLab 字体文件未找到。路径: {FONT_PATH}")
except Exception as e:
    print(f"❌ 严重错误：ReportLab 字体注册失败。错误: {e}")

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


class MaterialViewSet(viewsets.ReadOnlyModelViewSet):
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

    @action(
        detail=True, 
        methods=['get'], 
        url_path='download-pdf',
        permission_classes=[AllowAny])
    def download_pdf(self, request, pk=None):
        """
        为单个素材生成并提供下载PDF文件的接口 - 修复边距问题
        """
        material = get_object_or_404(Material, pk=pk)

        # 对于路线规划类型且已有PDF文件，直接返回
        if material.material_type == 'route' and material.pdf_file:
            filename = os.path.basename(material.pdf_file.name)
            return FileResponse(
                material.pdf_file.open(), 
                as_attachment=True, 
                filename=filename
            )

        # 确保字体已注册
        font_name = 'PuHuiTi'
        font_path = settings.PDF_FONT_PATH
        
        if not os.path.exists(font_path):
            return Response(
                {"detail": "PDF生成服务暂时不可用，字体文件缺失"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        if font_name not in pdfmetrics.getRegisteredFontNames():
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
            except Exception as e:
                print(f"字体注册失败: {e}")
                return Response(
                    {"detail": "PDF生成服务暂时不可用"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        buffer = BytesIO()
        
        # 使用A4纸张，设置合理的边距
        pagesize = A4
        width, height = pagesize
        
        # 设置边距：上下左右各2.5cm
        margin = 72  # 1 inch = 72 points, 约2.54cm
        content_width = width - 2 * margin
        
        # 使用 Platypus 框架创建更复杂的布局
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
        
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=pagesize,
            rightMargin=margin,
            leftMargin=margin,
            topMargin=margin,
            bottomMargin=margin
        )
        
        # 创建故事（内容列表）
        story = []
        
        # 定义样式
        styles = getSampleStyleSheet()
        
        # 自定义样式 - 使用注册的中文字体
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=18,
            textColor=colors.darkblue,
            spaceAfter=30,
            alignment=TA_LEFT
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle', 
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=14,
            textColor=colors.darkblue,
            spaceAfter=12,
            alignment=TA_LEFT
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11,
            textColor=colors.black,
            spaceAfter=12,
            alignment=TA_JUSTIFY,  # 两端对齐
            wordWrap='CJK'  # 中文换行
        )
        
        info_style = ParagraphStyle(
            'CustomInfo',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11,
            textColor=colors.black,
            leftIndent=0,
            spaceAfter=6
        )
        
        # ==================== 头部区域 ====================
        
        story.append(Paragraph("旅游素材详情", title_style))
        
        # 添加分隔线（使用空格和边框模拟）
        story.append(Spacer(1, 1))
        line_style = ParagraphStyle(
            'LineStyle',
            parent=styles['Normal'],
            borderWidth=1,
            borderColor=colors.lightgrey,
            borderPadding=0,
            spaceAfter=20
        )
        story.append(Paragraph('<para borderWidth="1" borderColor="lightgrey"> </para>', line_style))
        
        # ==================== 图片区域 ====================
        
        if material.header_image:
            try:
                image_path = material.header_image.path
                # 使用 Platypus 的 Image 组件，自动处理尺寸和布局
                header_img = Image(image_path, width=content_width, height=150)
                header_img.hAlign = 'CENTER'
                story.append(header_img)
                story.append(Spacer(1, 20))
            except Exception as e:
                print(f"PDF生成：无法加载图片 {material.header_image.name}: {e}")
                # 图片加载失败时添加占位文本
                story.append(Paragraph("<para color='gray'>[图片加载失败]</para>", normal_style))
                story.append(Spacer(1, 20))
        
        # ==================== 主标题 ====================
        
        story.append(Paragraph(material.title, title_style))
        story.append(Spacer(1, 10))
        
        # ==================== 基本信息区域 ====================
        
        story.append(Paragraph("基本信息", subtitle_style))
        
        # 创建信息表格
        info_html = f"""
        <para>
        <b>素材类型:</b> {material.get_material_type_display()}<br/>
        <b>目的地:</b> {material.destination.name if material.destination else '通用'}<br/>
        <b>创建时间:</b> {material.created_at.strftime("%Y-%m-%d %H:%M")}<br/>
        """
        if material.price is not None:
            info_html += f"<b>价格:</b> <font color='red'>RM {material.price:.2f}</font><br/>"
        
        info_html += "</para>"
        
        story.append(Paragraph(info_html, info_style))
        story.append(Spacer(1, 20))
        
        # ==================== 详细描述区域 ====================
        
        story.append(Paragraph("详细描述", subtitle_style))
        
        # 添加分隔线
        story.append(Spacer(1, 1))
        story.append(Paragraph('<para borderWidth="1" borderColor="lightgrey"> </para>', line_style))
        story.append(Spacer(1, 10))
        
        # 处理描述文本 - 使用 Paragraph 自动处理换行和边距
        if material.description:
            # 将换行符转换为HTML换行
            description_text = material.description.replace('\n', '<br/>')
            story.append(Paragraph(description_text, normal_style))
        else:
            story.append(Paragraph("<para color='gray'>暂无详细描述</para>", normal_style))
        
        story.append(Spacer(1, 30))
        
        # ==================== 页脚信息 ====================
        
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=9,
            textColor=colors.gray,
            alignment=TA_LEFT
        )
        
        footer_html = f"""
        <para>
        生成时间: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
        </para>
        """
        story.append(Paragraph(footer_html, footer_style))
        
        # ==================== 构建PDF ====================
        
        try:
            doc.build(story)
        except Exception as e:
            print(f"PDF构建失败: {e}")
            return Response(
                {"detail": "PDF生成失败"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        buffer.seek(0)
        
        # 清理文件名中的非法字符
        import re
        clean_title = re.sub(r'[^\w\s-]', '', material.title)
        filename = f"{clean_title}_{material.get_material_type_display()}.pdf"
        
        response = FileResponse(buffer, as_attachment=True, filename=filename)
        response['Content-Type'] = 'application/pdf'
        
        return response

        def _split_text(self, canvas, text, font_name, font_size, max_width):
            """
            辅助方法：将文本分割为适合PDF宽度的行
            """
            if not text:
                return []
            
            # 处理换行符
            paragraphs = text.split('\n')
            lines = []
            
            for paragraph in paragraphs:
                if not paragraph.strip():
                    lines.append('')  # 空行
                    continue
                    
                words = paragraph.split()
                current_line = []
                
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    width = canvas.stringWidth(test_line, font_name, font_size)
                    
                    if width <= max_width:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                        current_line = [word]
                
                if current_line:
                    lines.append(' '.join(current_line))
            
            return lines



class DestinationViewSet(viewsets.ReadOnlyModelViewSet):
    """提供所有目的地的列表，用于前端筛选。"""
    queryset = Destination.objects.all().order_by('name')
    serializer_class = DestinationSerializer

# 自定义分页类
class SupportTicketPagination(PageNumberPagination):
    page_size = 10
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