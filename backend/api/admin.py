# from django.contrib import admin
# from django import forms
# from .models import Destination, Material, MaterialImage, SupportTicket, UserProfile
# from django_ckeditor_5.widgets import CKEditor5Widget
# class MaterialImageInline(admin.TabularInline):
#     model = MaterialImage
#     extra = 3
#     fields = ['image', 'description', 'order']
#     ordering = ['order', 'id']
    
#     def get_formset(self, request, obj=None, **kwargs):
#         formset = super().get_formset(request, obj, **kwargs)
#         if obj and obj.material_type != 'hotel':
#             formset.max_num = 0
#         return formset

# class MaterialAdminForm(forms.ModelForm):
#     class Meta:
#         model = Material
#         fields = '__all__'
#         widgets = {
#             'description': CKEditor5Widget(
#                 attrs={"class": "django_ckeditor_5"}, config_name="extends"
#             )
#         }

# class MaterialAdmin(admin.ModelAdmin):
#     form = MaterialAdminForm
#     list_display = ['title', 'material_type', 'destination', 'price', 'created_at', 'compression_status']
#     list_filter = ['material_type', 'destination', 'created_at']
#     search_fields = ['title', 'description']
#     readonly_fields = ['created_at', 'updated_at', 'compression_info']
    
#     fieldsets = [
#         ('类型选择', {'fields': ['material_type']}),
#         ('基本信息', {'fields': ['title', 'destination', 'description', 'price', 'header_image']}),
#         ('酒店专属', {'fields': ['video'], 'description': '仅酒店类型可用'}),
#         ('路线规划专属', {'fields': ['pdf_file'], 'description': '仅路线规划类型可用'}),
#         ('压缩信息', {'fields': ['compression_info'], 'classes': ['collapse']}),
#         ('时间信息', {'fields': ['created_at', 'updated_at'], 'classes': ['collapse']}),
#     ]
    
#     inlines = [MaterialImageInline]
    
#     def compression_status(self, obj):
#         """在列表页显示压缩状态"""
#         if obj.compression_data:
#             return "已压缩"
#         return "未压缩"
#     compression_status.short_description = "压缩状态"
    
#     def compression_info(self, obj):
#         """在详情页显示压缩信息"""
#         if not obj.compression_data:
#             return "无压缩信息"
        
#         info_html = "<div style='padding: 10px; background: #f8f9fa; border-radius: 5px;'>"
        
#         for field_name, comp_info in obj.compression_data.items():
#             if comp_info:
#                 original_mb = comp_info['original_size'] / (1024 * 1024)
#                 compressed_mb = comp_info['compressed_size'] / (1024 * 1024)
#                 ratio = comp_info['compression_ratio']
                
#                 info_html += f"""
#                 <div style='margin-bottom: 15px; padding: 10px; border-left: 4px solid #007cba; background: white;'>
#                     <strong>{field_name}:</strong><br>
#                     原始大小: {original_mb:.2f} MB<br>
#                     压缩后: {compressed_mb:.2f} MB<br>
#                     压缩率: {ratio:.1f}%
#                 </div>
#                 """
        
#         info_html += "</div>"
#         return info_html
#     compression_info.short_description = "压缩详情"
#     compression_info.allow_tags = True
    
#     def get_fieldsets(self, request, obj=None):
#         fieldsets = super().get_fieldsets(request, obj)
        
#         if not obj:
#             return fieldsets
        
#         new_fieldsets = []
#         for fieldset in fieldsets:
#             fieldset_name = fieldset[0]
            
#             if fieldset_name == '酒店专属' and obj.material_type != 'hotel':
#                 continue
                
#             if fieldset_name == '路线规划专属' and obj.material_type != 'route':
#                 continue
                
#             new_fieldsets.append(fieldset)
        
#         return new_fieldsets
    
#     def get_inline_instances(self, request, obj=None):
#         if not obj or obj.material_type == 'hotel':
#             return [MaterialImageInline(self.model, self.admin_site)]
#         return []
    
#     def get_exclude(self, request, obj=None):
#         exclude = super().get_exclude(request, obj) or []
        
#         if obj:
#             if obj.material_type != 'hotel':
#                 exclude = list(exclude) + ['video']
#             if obj.material_type != 'route':
#                 exclude = list(exclude) + ['pdf_file']
                
#         return exclude
    
#     def save_model(self, request, obj, form, change):
#         if obj.material_type == 'route' and obj.video:
#             obj.video.delete(save=False)
#             obj.video = None
            
#         if obj.material_type != 'hotel' and obj.video:
#             obj.video.delete(save=False)
#             obj.video = None
            
#         super().save_model(request, obj, form, change)

# class DestinationAdmin(admin.ModelAdmin):
#     list_display = ['name', 'slug', 'created_at']
#     search_fields = ['name']
#     prepopulated_fields = {'slug': ('name',)}

# class MaterialImageAdmin(admin.ModelAdmin):
#     list_display = ['material', 'image', 'order', 'description']
#     list_filter = ['material__material_type', 'material__destination']
#     search_fields = ['material__title', 'description']
#     list_editable = ['order']
    
#     # 只显示酒店类型的图片
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         return qs.filter(material__material_type='hotel')

# class SupportTicketAdmin(admin.ModelAdmin):
#     list_display = ['question_text_short', 'category', 'author', 'is_answered', 'created_at']
#     list_filter = ['category', 'is_answered', 'created_at']
#     search_fields = ['question_text', 'answer_content']
#     readonly_fields = ['created_at', 'answered_at']
    
#     fieldsets = [
#         ('问题信息', {
#             'fields': ['author', 'category', 'question_text', 'created_at']
#         }),
#         ('回答信息', {
#             'fields': [
#                 'is_answered', 'answer_content', 'answered_by', 'answered_at'
#             ]
#         }),
#         ('其他', {
#             'fields': ['is_public_faq'],
#             'classes': ['collapse']
#         }),
#     ]
    
#     def question_text_short(self, obj):
#         return obj.question_text[:50] + ('...' if len(obj.question_text) > 50 else '')
#     question_text_short.short_description = '问题描述'

# class UserProfileAdmin(admin.ModelAdmin):
#     list_display = ['user', 'phone', 'created_at']
#     search_fields = ['user__username', 'phone']

# # 注册模型到Admin
# admin.site.register(Destination, DestinationAdmin)
# admin.site.register(Material, MaterialAdmin)
# admin.site.register(MaterialImage, MaterialImageAdmin)
# admin.site.register(SupportTicket, SupportTicketAdmin)
# admin.site.register(UserProfile, UserProfileAdmin)






from django.contrib import admin
from django import forms
from .models import Destination, Material, MaterialImage, MaterialVideo, SupportTicket, UserProfile  # ✅ 添加MaterialVideo
from django_ckeditor_5.widgets import CKEditor5Widget


class MaterialImageInline(admin.TabularInline):
    """图片内联编辑 - 所有素材类型通用"""
    model = MaterialImage
    extra = 3
    fields = ['image', 'description', 'order']
    ordering = ['order', 'id']


class MaterialVideoInline(admin.TabularInline):
    """✅ 新增:视频内联编辑 - 所有素材类型通用"""
    model = MaterialVideo
    extra = 2
    fields = ['video', 'title', 'description', 'thumbnail', 'order']
    ordering = ['order', 'id']


class MaterialAdminForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = '__all__'
        widgets = {
            'description': CKEditor5Widget(
                attrs={"class": "django_ckeditor_5"}, config_name="extends"
            )
        }


class MaterialAdmin(admin.ModelAdmin):
    form = MaterialAdminForm
    list_display = ['title', 'material_type', 'destination', 'price', 'created_at', 'media_count', 'compression_status']
    list_filter = ['material_type', 'destination', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'compression_info']
    
    fieldsets = [
        ('类型选择', {'fields': ['material_type']}),
        ('基本信息', {'fields': ['title', 'destination', 'description', 'price', 'header_image']}),
        ('路线规划专属', {'fields': ['pdf_file'], 'description': '仅路线规划类型可用'}),
        ('压缩信息', {'fields': ['compression_info'], 'classes': ['collapse']}),
        ('时间信息', {'fields': ['created_at', 'updated_at'], 'classes': ['collapse']}),
    ]
    
    # ✅ 更新:添加视频内联
    inlines = [MaterialImageInline, MaterialVideoInline]
    
    def media_count(self, obj):
        """显示素材的图片和视频数量"""
        image_count = obj.images.count()
        video_count = obj.videos.count()
        return f"📷 {image_count} | 🎬 {video_count}"
    media_count.short_description = "媒体数量"
    
    def compression_status(self, obj):
        """在列表页显示压缩状态"""
        if obj.compression_data:
            return "已压缩"
        return "未压缩"
    compression_status.short_description = "压缩状态"
    
    def compression_info(self, obj):
        """在详情页显示压缩信息"""
        if not obj.compression_data:
            return "无压缩信息"
        
        info_html = "<div style='padding: 10px; background: #f8f9fa; border-radius: 5px;'>"
        
        for field_name, comp_info in obj.compression_data.items():
            if comp_info:
                original_mb = comp_info['original_size'] / (1024 * 1024)
                compressed_mb = comp_info['compressed_size'] / (1024 * 1024)
                ratio = comp_info['compression_ratio']
                
                info_html += f"""
                <div style='margin-bottom: 15px; padding: 10px; border-left: 4px solid #007cba; background: white;'>
                    <strong>{field_name}:</strong><br>
                    原始大小: {original_mb:.2f} MB<br>
                    压缩后: {compressed_mb:.2f} MB<br>
                    压缩率: {ratio:.1f}%
                </div>
                """
        
        info_html += "</div>"
        return info_html
    compression_info.short_description = "压缩详情"
    compression_info.allow_tags = True
    
    def get_fieldsets(self, request, obj=None):
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


class DestinationAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


class MaterialImageAdmin(admin.ModelAdmin):
    """图片管理 - 所有素材类型通用"""
    list_display = ['material', 'image', 'order', 'description', 'material_type']
    list_filter = ['material__material_type', 'material__destination']
    search_fields = ['material__title', 'description']
    list_editable = ['order']
    
    def material_type(self, obj):
        return obj.material.get_material_type_display()
    material_type.short_description = "素材类型"


class MaterialVideoAdmin(admin.ModelAdmin):
    """✅ 新增:视频管理 - 所有素材类型通用"""
    list_display = ['material', 'title', 'order', 'duration', 'material_type', 'created_at']
    list_filter = ['material__material_type', 'material__destination', 'created_at']
    search_fields = ['material__title', 'title', 'description']
    list_editable = ['order']
    readonly_fields = ['created_at']
    
    def material_type(self, obj):
        return obj.material.get_material_type_display()
    material_type.short_description = "素材类型"


class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['question_text_short', 'category', 'author', 'is_answered', 'created_at']
    list_filter = ['category', 'is_answered', 'created_at']
    search_fields = ['question_text', 'answer_content']
    readonly_fields = ['created_at', 'answered_at']
    
    fieldsets = [
        ('问题信息', {
            'fields': ['author', 'category', 'question_text', 'created_at']
        }),
        ('回答信息', {
            'fields': [
                'is_answered', 'answer_content', 'answered_by', 'answered_at'
            ]
        }),
        ('其他', {
            'fields': ['is_public_faq'],
            'classes': ['collapse']
        }),
    ]
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + ('...' if len(obj.question_text) > 50 else '')
    question_text_short.short_description = '问题描述'


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'created_at']
    search_fields = ['user__username', 'phone']


# 注册模型到Admin
admin.site.register(Destination, DestinationAdmin)
admin.site.register(Material, MaterialAdmin)
admin.site.register(MaterialImage, MaterialImageAdmin)
admin.site.register(MaterialVideo, MaterialVideoAdmin) 
admin.site.register(SupportTicket, SupportTicketAdmin)
admin.site.register(UserProfile, UserProfileAdmin)