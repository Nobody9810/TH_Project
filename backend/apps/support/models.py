
from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings # 确保导入了 settings
from django_ckeditor_5.fields import CKEditor5Field
# Create your models here.
class SupportTicket(models.Model):
    CATEGORY_CHOICES = [
        ('faq', '常见问题'),
        ('ticket', '订票问题'),
        ('car', '汽车问题'),
        ('incident', '意外情况'),
    ]
    
    author = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='submitted_tickets',
        verbose_name="提问/创建者"
    )
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="问题分类")
    question_text = models.TextField(verbose_name="问题详细描述/标题") 
    created_at = models.DateTimeField(auto_now_add=True)

    is_answered = models.BooleanField(default=False, verbose_name="是否已回答")
    answer_content = CKEditor5Field('管理员回答内容', config_name='extends', blank=True)
    answered_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='answered_tickets',
        verbose_name="回答者"
    )
    answered_at = models.DateTimeField(blank=True, null=True, verbose_name="回答时间")
    
    is_public_faq = models.BooleanField(default=False, verbose_name="公开到知识库")
    
    class Meta:
        verbose_name = "问答"
        verbose_name_plural = "问答库"
        ordering = ['-created_at']

    def __str__(self):
        return self.question_text[:50] + ('...' if len(self.question_text) > 50 else '')
