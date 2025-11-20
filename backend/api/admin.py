from django.contrib import admin
from django import forms
from .models import (
    Destination, Material, MaterialImage, MaterialVideo, 
    SupportTicket, UserProfile
)
from django_ckeditor_5.widgets import CKEditor5Widget
from django.urls import path
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.forms.widgets import ClearableFileInput
from django.utils.html import format_html

# ⭐ 导入 Unfold 组件
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display


# ==================== 文件上传组件 (保持不变) ====================

class AdminMultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = AdminMultipleFileInput
    
    def to_python(self, data):
        if not data:
            return []
        if isinstance(data, (list, tuple)):
            return [super().to_python(item) for item in data]
        return [super().to_python(data)]
    
    def validate(self, data):
        if self.required and not data:
            raise forms.ValidationError(self.error_messages['required'])
        for item in data:
            super().validate(item)


# ==================== Inline 类 (使用 Unfold) ====================

class MaterialImageInline(TabularInline):  # ✅ 改用 Unfold 的 TabularInline
    """图片内联编辑"""
    model = MaterialImage
    extra = 3
    fields = ['image', 'description', 'order']
    ordering = ['order', 'id']


class MaterialVideoInline(TabularInline):  # ✅ 改用 Unfold 的 TabularInline
    """视频内联编辑"""
    model = MaterialVideo
    extra = 2
    fields = ['video', 'title', 'description', 'thumbnail', 'order']
    ordering = ['order', 'id']


# ==================== 表单类 (保持不变) ====================

class MaterialAdminForm(forms.ModelForm):
    uploaded_images = MultipleFileField(
        widget=AdminMultipleFileInput(attrs={'multiple': True}),
        required=False,
        label="批量上传图片"
    )
    uploaded_videos = MultipleFileField(
        widget=AdminMultipleFileInput(attrs={'multiple': True}),
        required=False,
        label="批量上传视频"
    )
    
    class Meta:
        model = Material
        fields = '__all__'
        widgets = {
            'description': CKEditor5Widget(
                attrs={"class": "django_ckeditor_5"}, 
                config_name="extends"
            )
        }


# ==================== Material Admin (使用 Unfold) ====================

class MaterialAdmin(ModelAdmin):  # ✅ 改用 Unfold 的 ModelAdmin
    form = MaterialAdminForm
    change_form_template = 'admin/api/material/change_form.html'
    
    # 列表页配置
    list_display = [
        'show_thumbnail',
        'title', 
        'show_type_badge',
        'destination', 
        'show_price',
        'created_at', 
        'show_media_count',

    ]
    
    list_filter = [
        'material_type',
        'destination',
        ('created_at', admin.DateFieldListFilter),
    ]
    
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    # Fieldsets 配置
    fieldsets = [
        ('类型选择', {
            'fields': ['material_type']
        }),
        ('基本信息', {
            'fields': ['title', 'destination', 'description', 'price']
        }),
        ('路线规划专属', {
            'fields': ['pdf_file'], 
            'description': '仅路线规划类型可用',

        }),
        ('批量上传', {
            'fields': ['uploaded_images', 'uploaded_videos'], 
        }),
       
        ('时间信息', {
            'fields': ['created_at', 'updated_at'], 
            'classes': ['collapse']
        }),
    ]

    
    # ==================== 自定义显示方法 ====================
    
    @display(description="预览")
    def show_thumbnail(self, obj):
        """显示缩略图"""
        if obj.header_image:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; '
                'object-fit: cover; border-radius: 8px; '
                'box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />',
                obj.header_image.url
            )
        return format_html(
            '<div style="width: 60px; height: 60px; background: #f3f4f6; '
            'border-radius: 8px; display: flex; align-items: center; '
            'justify-content: center; color: #9ca3af; font-size: 24px;">📦</div>'
        )
    
    @display(description="类型", ordering="material_type")
    def show_type_badge(self, obj):
        """类型徽章"""
        colors = {
            'hotel': '#3b82f6',      # 蓝色
            'ticket': '#ef4444',     # 红色
            'route': '#10b981',      # 绿色
            'transport': '#f59e0b',  # 橙色
            'restaurant': '#8b5cf6'  # 紫色
        }
        color = colors.get(obj.material_type, '#6b7280')
        return format_html(
            '<span style="display: inline-flex; align-items: center; '
            'background: {}; color: white; padding: 4px 12px; '
            'border-radius: 9999px; font-size: 12px; font-weight: 500; '
            'white-space: nowrap;">{}</span>',
            color,
            obj.get_material_type_display()
        )
    
    @admin.display(description="价格", ordering="price")
    def show_price(self, obj):
        """价格显示"""
        if obj.price is not None:
            # ✅ 正确做法：先使用 f-string 或 str.format() 格式化数字，得到一个普通字符串
            formatted_price = f"RM {obj.price:.2f}"
            
            # 将格式化后的字符串作为参数传递给 format_html (模板中只留一个空的 {})
            return format_html(
                '<span style="color: #ef4444; font-weight: 600; font-size: 14px;">{}</span>',
                formatted_price
            )
        
        # 确保返回的也是 format_html (保持一致性)
        return format_html('<span style="color: #9ca3af;">-</span>')
    
    @display(description="媒体")
    def show_media_count(self, obj):
        """媒体数量"""
        image_count = obj.images.count()
        video_count = obj.videos.count()
        return format_html(
            '<div style="display: flex; gap: 12px; font-size: 13px;">'
            '<span style="display: flex; align-items: center; gap: 4px;">'
            '📷 <strong>{}</strong></span>'
            '<span style="display: flex; align-items: center; gap: 4px;">'
            '🎬 <strong>{}</strong></span>'
            '</div>',
            image_count, video_count
        )
    

    
    def get_fieldsets(self, request, obj=None):
        """动态调整字段集"""
        fieldsets = super().get_fieldsets(request, obj)
        
        if not obj:
            return fieldsets
        
        new_fieldsets = []
        for fieldset in fieldsets:
            fieldset_name = fieldset[0]
            
            if fieldset_name == '路线规划专属' and obj.material_type != 'route':
                continue
                
            new_fieldsets.append(fieldset)
        
        return new_fieldsets
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """在详情页添加批量上传按钮"""
        extra_context = extra_context or {}
        extra_context['additional_buttons'] = [
            {
                'url': f'../{object_id}/upload-images/',
                'label': '批量上传图片'
            },
            {
                'url': f'../{object_id}/upload-videos/',
                'label': '批量上传视频'
            }
        ]
        return super().change_view(request, object_id, form_url, extra_context=extra_context)
    
    # ==================== 批量上传相关 (保持不变) ====================
    
    class BatchImagesForm(forms.Form):
        files = forms.FileField(
            widget=AdminMultipleFileInput(attrs={'multiple': True}), 
            required=True, 
            label="选择多个图片文件"
        )

    class BatchVideosForm(forms.Form):
        files = forms.FileField(
            widget=AdminMultipleFileInput(attrs={'multiple': True}), 
            required=True, 
            label="选择多个视频文件"
        )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:material_id>/upload-images/', 
                self.admin_site.admin_view(self.upload_images_view), 
                name='api_material_upload_images'
            ),
            path(
                '<int:material_id>/upload-videos/', 
                self.admin_site.admin_view(self.upload_videos_view), 
                name='api_material_upload_videos'
            ),
        ]
        return custom_urls + urls

    def upload_images_view(self, request, material_id: int):
        material = get_object_or_404(Material, pk=material_id)
        if request.method == 'POST':
            form = self.BatchImagesForm(request.POST, request.FILES)
            files = request.FILES.getlist('files')
            if files:
                created = 0
                for f in files:
                    MaterialImage.objects.create(material=material, image=f)
                    created += 1
                messages.success(request, f'已成功上传 {created} 张图片。')
                return redirect(f'../../{material_id}/change/')
        else:
            form = self.BatchImagesForm()
        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'title': f'批量上传图片: {material.title}',
            'form': form,
            'material': material,
        }
        return render(request, 'admin/batch_upload.html', context)

    def upload_videos_view(self, request, material_id: int):
        material = get_object_or_404(Material, pk=material_id)
        if request.method == 'POST':
            form = self.BatchVideosForm(request.POST, request.FILES)
            files = request.FILES.getlist('files')
            if files:
                created = 0
                for f in files:
                    MaterialVideo.objects.create(material=material, video=f)
                    created += 1
                messages.success(request, f'已成功上传 {created} 个视频。')
                return redirect(f'../../{material_id}/change/')
        else:
            form = self.BatchVideosForm()
        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'title': f'批量上传视频: {material.title}',
            'form': form,
            'material': material,
        }
        return render(request, 'admin/batch_upload.html', context)

    def save_model(self, request, obj, form, change):
        """保存素材并处理批量上传"""
        super().save_model(request, obj, form, change)
        
        # 处理图片
        images = form.cleaned_data.get('uploaded_images') or []
        if images:
            created = 0
            for f in images:
                MaterialImage.objects.create(material=obj, image=f)
                created += 1
            if created:
                messages.success(request, f'已批量上传 {created} 张图片。')
        
        # 处理视频
        videos = form.cleaned_data.get('uploaded_videos') or []
        if videos:
            created = 0
            for f in videos:
                MaterialVideo.objects.create(material=obj, video=f)
                created += 1
            if created:
                messages.success(request, f'已批量上传 {created} 个视频。')


# ==================== 其他 Admin 类 (使用 Unfold) ====================

class DestinationAdmin(ModelAdmin):  # ✅ 使用 Unfold
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


class MaterialImageAdmin(ModelAdmin):  # ✅ 使用 Unfold
    list_display = [
        'show_thumbnail', 
        'material', 
        'order', 
        'description', 
        'material_type'
    ]
    list_filter = ['material__material_type', 'material__destination']
    search_fields = ['material__title', 'description']
    list_editable = ['order']
    
    @display(description="预览")
    def show_thumbnail(self, obj):
        return format_html(
            '<img src="{}" style="width: 50px; height: 50px; '
            'object-fit: cover; border-radius: 6px; '
            'box-shadow: 0 1px 3px rgba(0,0,0,0.1);" />',
            obj.image.url
        )
    
    def material_type(self, obj):
        return obj.material.get_material_type_display()
    material_type.short_description = "素材类型"


class MaterialVideoAdmin(ModelAdmin):  # ✅ 使用 Unfold
    list_display = [
        'material', 
        'title', 
        'order', 
        'duration', 
        'material_type', 
        'created_at'
    ]
    list_filter = [
        'material__material_type', 
        'material__destination', 
        'created_at'
    ]
    search_fields = ['material__title', 'title', 'description']
    list_editable = ['order']
    readonly_fields = ['created_at']
    
    def material_type(self, obj):
        return obj.material.get_material_type_display()
    material_type.short_description = "素材类型"


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


class UserProfileAdmin(ModelAdmin):  # ✅ 使用 Unfold
    list_display = ['user', 'phone', 'created_at']
    search_fields = ['user__username', 'phone']


# ==================== 注册所有模型 ====================

admin.site.register(Destination, DestinationAdmin)
admin.site.register(Material, MaterialAdmin)
admin.site.register(MaterialImage, MaterialImageAdmin)
admin.site.register(MaterialVideo, MaterialVideoAdmin)
admin.site.register(SupportTicket, SupportTicketAdmin)
admin.site.register(UserProfile, UserProfileAdmin)