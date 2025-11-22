from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, filters, status, generics
from rest_framework.decorators import action,api_view, parser_classes
from django.core.cache import cache

from .models import SupportTicket
from .serializers import (
    SupportTicketSerializer,
    
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
# Create your views here.
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