from django.contrib import admin
from django import forms
from .models import SupportTicket
from django_ckeditor_5.widgets import CKEditor5Widget
from django.urls import path
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.forms.widgets import ClearableFileInput
from django.utils.html import format_html

# ⭐ 导入 Unfold 组件
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

class SupportTicketAdmin(ModelAdmin):  # ✅ 使用 Unfold
    list_display = [
        'question_text_short',
        'show_category_badge',
        'author',
        'show_status',
        'created_at'
    ]
    list_filter = ['category', 'is_answered', 'created_at']
    search_fields = ['question_text', 'answer_content']
    readonly_fields = ['created_at', 'answered_at']
    
    fieldsets = [
        ('问题信息', {
            'fields': ['author', 'category', 'question_text', 'created_at']
        }),
        ('回答信息', {
            'fields': [
                'is_answered', 'answer_content', 
                'answered_by', 'answered_at'
            ]
        }),
        ('其他', {
            'fields': ['is_public_faq'],
            'classes': ['collapse']
        }),
    ]
    
    @display(description="分类")
    def show_category_badge(self, obj):
        colors = {
            'faq': '#06b6d4',
            'ticket': '#8b5cf6',
            'car': '#f97316',
            'incident': '#ef4444'
        }
        return format_html(
            '<span style="background: {}; color: white; '
            'padding: 4px 10px; border-radius: 9999px; '
            'font-size: 11px; font-weight: 500;">{}</span>',
            colors.get(obj.category, '#6b7280'),
            obj.get_category_display()
        )
    
    @display(description="状态", boolean=True)
    def show_status(self, obj):
        return obj.is_answered
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + (
            '...' if len(obj.question_text) > 50 else ''
        )
    question_text_short.short_description = '问题描述'




admin.site.register(SupportTicket, SupportTicketAdmin)
