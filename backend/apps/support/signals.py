import os
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.core.files.base import ContentFile
import logging
from django.utils import timezone
from django.conf import settings
from ..lark_integration.services import lark_notifier
from .models import SupportTicket
import subprocess
import shutil
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

# ==================== SupportTicket 飞书通知 ====================

def get_user_display_name(user):
    """获取用户显示名称(优先使用真实姓名)"""
    if not user:
        return '匿名用户'
    
    if user.first_name or user.last_name:
        full_name = f"{user.last_name}{user.first_name}".strip()
        if full_name:
            return full_name
    
    if hasattr(user, 'profile') and hasattr(user.profile, 'chinese_name'):
        if user.profile.chinese_name:
            return user.profile.chinese_name
    
    return user.username or '匿名用户'


@receiver(post_save, sender=SupportTicket)
def notify_new_ticket(sender, instance, created, **kwargs):
    """新问题创建时发送 Lark 通知"""
    if created:
        try:
            detail_url = f"{settings.FRONTEND_URL}/admin"
            
            author_name = get_user_display_name(instance.author)
            local_time = timezone.localtime(instance.created_at)
            ticket_data = {
                'id': instance.id,
                'category': instance.category,
                'category_display': instance.get_category_display(),
                'question_text': instance.question_text,
                'author_name': author_name,
                'created_at': local_time.strftime('%Y-%m-%d %H:%M:%S'),
                'detail_url': detail_url
            }
            
            lark_notifier.send_new_question_card(ticket_data)
            logger.info(f"✅ Lark通知已发送: Ticket {instance.id} by {author_name}")
        except Exception as e:
            logger.error(f"❌ Lark通知发送失败: {e}", exc_info=True)