from django.contrib import admin
from django import forms
from .models import UserProfile
from django_ckeditor_5.widgets import CKEditor5Widget
from django.urls import path
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.forms.widgets import ClearableFileInput
from django.utils.html import format_html

# ⭐ 导入 Unfold 组件
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display





class UserProfileAdmin(ModelAdmin):  # ✅ 使用 Unfold
    list_display = ['user', 'phone', 'created_at']
    search_fields = ['user__username', 'phone']





admin.site.register(UserProfile, UserProfileAdmin)