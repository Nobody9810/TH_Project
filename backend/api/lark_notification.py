# =====================================================
# api/lark_notification.py
# =====================================================
import requests
import json
import hmac
import hashlib
import base64
import time
from django.conf import settings
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class LarkNotifier:
    """飞书/Lark 机器人通知工具类"""
    
    def __init__(self):
        self.webhook_url = getattr(settings, 'LARK_WEBHOOK_URL', '')
        self.secret = getattr(settings, 'LARK_WEBHOOK_SECRET', '')
        self.enabled = getattr(settings, 'LARK_ENABLE_NOTIFICATIONS', True)
    
    def _generate_sign(self, timestamp: int) -> str:
        """生成签名（如果启用了签名验证）"""
        if not self.secret:
            return ""
        
        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return sign
    
    def send_message(self, msg_type: str = "interactive", **kwargs) -> bool:
        """
        发送消息到 Lark
        
        Args:
            msg_type: 消息类型 (text, post, interactive, share_chat)
            **kwargs: 消息内容
        
        Returns:
            bool: 是否发送成功
        """
        if not self.enabled or not self.webhook_url:
            logger.warning("Lark notifications disabled or webhook URL not configured")
            return False
        
        timestamp = int(time.time())
        payload = {
            "timestamp": str(timestamp),
            "msg_type": msg_type,
        }
        
        # 添加签名（如果需要）
        if self.secret:
            payload["sign"] = self._generate_sign(timestamp)
        
        # 根据消息类型添加内容
        if msg_type == "text":
            payload["content"] = {"text": kwargs.get("text", "")}
        elif msg_type == "post":
            payload["content"] = {"post": kwargs.get("post", {})}
        elif msg_type == "interactive":
            payload["card"] = kwargs.get("card", {})
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == 0:
                logger.info(f"Lark notification sent successfully: {result}")
                return True
            else:
                logger.error(f"Lark notification failed: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Lark notification: {e}")
            return False
    
    def send_text(self, text: str) -> bool:
        """发送简单文本消息"""
        return self.send_message(msg_type="text", text=text)
    
    def send_new_question_card(self, ticket_data: Dict[str, Any]) -> bool:
        """
        发送新问题通知卡片（美化版）
        
        Args:
            ticket_data: 包含问题信息的字典
                - id: 问题ID
                - category: 分类
                - question_text: 问题内容
                - author_name: 提问者姓名（已格式化）
                - created_at: 创建时间
                - detail_url: 详情链接
        """
        # 分类emoji映射
        category_emoji = {
            'faq': '❓',
            'ticket': '🎫',
            'car': '🚗',
            'incident': '🚨'
        }
        
        # 分类颜色映射
        category_color = {
            'faq': 'blue',
            'ticket': 'green',
            'car': 'orange',
            'incident': 'red'
        }
        
        category = ticket_data.get('category', 'faq')
        emoji = category_emoji.get(category, '📝')
        color = category_color.get(category, 'blue')
        
        # 构造卡片消息
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "template": color,
                "title": {
                    "tag": "plain_text",
                    "content": f"{emoji} 新的支持问题"
                }
            },
            "elements": [
                # 问题分类
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**问题ID:**\n{ticket_data.get('id', 'N/A')}"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**分类:**\n{ticket_data.get('category_display', category)}"
                            }
                        }
                    ]
                },
                # 提问者和时间
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**提问者:**\n{ticket_data.get('author_name', '匿名用户')}"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**创建时间:**\n{ticket_data.get('created_at', '')}"
                            }
                        }
                    ]
                },
                # 分隔线
                {
                    "tag": "hr"
                },
                # 问题内容
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**问题详情:**\n{ticket_data.get('question_text', '')[:500]}"
                    }
                },
            ]
        }
        
        # 添加查看详情按钮
        if ticket_data.get('detail_url'):
            card["elements"].append({
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "查看详情并回答"
                        },
                        "type": "primary",
                        "url": ticket_data['detail_url']
                    }
                ]
            })
        
        return self.send_message(msg_type="interactive", card=card)
    
    def send_answer_notification_card(self, ticket_data: Dict[str, Any]) -> bool:
        """
        发送问题已被回答的通知卡片
        
        Args:
            ticket_data: 包含回答信息的字典
        """
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "template": "green",
                "title": {
                    "tag": "plain_text",
                    "content": "✅ 问题已被回答"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**问题ID:** {ticket_data.get('id')}\n**回答者:** {ticket_data.get('answered_by_name', 'N/A')}\n**回答时间:** {ticket_data.get('answered_at', '')}"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**原问题:**\n{ticket_data.get('question_text', '')[:200]}"
                    }
                }
            ]
        }
        
        if ticket_data.get('detail_url'):
            card["elements"].append({
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "查看完整回答"
                        },
                        "type": "default",
                        "url": ticket_data['detail_url']
                    }
                ]
            })
        
        return self.send_message(msg_type="interactive", card=card)


# 全局实例
lark_notifier = LarkNotifier()