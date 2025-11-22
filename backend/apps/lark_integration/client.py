"""
Lark (飞书) OAuth 登录工具类 - 修复版
支持企业用户和个人用户使用同一套配置
"""
import requests
import logging
import uuid
from typing import Dict, Tuple
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth.models import User
from django.db import transaction

logger = logging.getLogger(__name__)


class LarkOAuthError(Exception):
    """Lark OAuth 相关错误"""
    pass


class LarkOAuthClient:
    """
    Lark OAuth 客户端 - 修复版
    使用统一的配置处理企业和个人用户登录
    """
    
    def __init__(self):
        self.config = settings.LARK_CONFIG
        self.app_id = settings.LARK_APP_ID
        self.app_secret = settings.LARK_APP_SECRET
        self.redirect_uri = settings.LARK_REDIRECT_URI
        
    def generate_state(self) -> str:
        """生成随机state参数用于CSRF保护"""
        state = str(uuid.uuid4())
        # 将state存储到缓存中，有效期10分钟
        cache.set(f"lark_oauth_state:{state}", True, 600)
        return state
    
    def verify_state(self, state: str) -> bool:
        """验证state参数"""
        cache_key = f"lark_oauth_state:{state}"
        is_valid = cache.get(cache_key) is not None
        if is_valid:
            cache.delete(cache_key)  # 使用后删除
        return is_valid
    
    def get_auth_url(self, state: str) -> str:
        """
        获取授权URL
        ⚠️ 修复：不指定 scope，让飞书使用默认权限
        """
        params = {
            'app_id': self.app_id,
            'redirect_uri': self.redirect_uri,
            'state': state
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        auth_url = f"{self.config['AUTH_URL']}?{query_string}"
        
        logger.info(f"生成授权URL: {auth_url}")
        return auth_url
    
    def get_app_access_token(self) -> str:
        """
        获取应用访问令牌
        """
        cache_key = "lark_app_token"
        token = cache.get(cache_key)
        
        if token:
            logger.info("✅ 使用缓存的应用访问令牌")
            return token
            
        url = f"{self.config['OPEN_API_HOST']}/open-apis/auth/v3/app_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            logger.info(f"📤 请求应用访问令牌: {url}")
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"📥 响应: {data}")
            
            if data.get('code') != 0:
                raise LarkOAuthError(f"获取应用令牌失败: {data.get('msg', '未知错误')}")
                
            token = data['app_access_token']
            expire_time = data.get('expire', 3600) - 300  # 提前5分钟刷新
            cache.set(cache_key, token, expire_time)
            
            logger.info("✅ 成功获取应用访问令牌")
            return token
            
        except requests.RequestException as e:
            logger.error(f"❌ 获取Lark应用令牌网络错误: {str(e)}")
            raise LarkOAuthError(f"网络请求失败: {str(e)}")
    
    def exchange_code_for_token(self, code: str) -> Dict:
        """
        使用授权码换取用户访问令牌
        
        Args:
            code: 授权码
            
        Returns:
            包含access_token等信息的字典
        """
        url = self.config['TOKEN_URL']
        headers = {
            'Authorization': f'Bearer {self.get_app_access_token()}',
            'Content-Type': 'application/json'
        }
        payload = {
            'grant_type': 'authorization_code',
            'code': code
        }
        
        try:
            logger.info(f"📤 换取用户访问令牌: {url}")
            logger.info(f"   Payload: {payload}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"📥 响应: {data}")
            
            if data.get('code') != 0:
                error_msg = data.get('msg', '未知错误')
                logger.error(f"❌ 换取用户令牌失败: {error_msg}")
                raise LarkOAuthError(f"换取用户令牌失败: {error_msg}")
                
            logger.info("✅ 成功换取用户访问令牌")
            return data['data']
            
        except requests.RequestException as e:
            logger.error(f"❌ 换取Lark用户令牌网络错误: {str(e)}")
            raise LarkOAuthError(f"网络请求失败: {str(e)}")
    
    def get_user_info(self, access_token: str) -> Dict:
        """
        获取用户信息
        
        Args:
            access_token: 用户访问令牌
            
        Returns:
            用户信息字典
        """
        url = self.config['USER_INFO_URL']
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            logger.info(f"📤 获取用户信息: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"📥 用户信息响应: {data}")
            
            if data.get('code') != 0:
                error_msg = data.get('msg', '未知错误')
                logger.error(f"❌ 获取用户信息失败: {error_msg}")
                raise LarkOAuthError(f"获取用户信息失败: {error_msg}")
            
            user_data = data.get('data', {})
            logger.info(f"✅ 成功获取用户信息")
            logger.info(f"   用户数据字段: {list(user_data.keys())}")
            
            return user_data
            
        except requests.RequestException as e:
            logger.error(f"❌ 获取Lark用户信息网络错误: {str(e)}")
            raise LarkOAuthError(f"网络请求失败: {str(e)}")
    
    def create_or_update_user(self, user_info: Dict) -> User:
        """
        根据Lark用户信息创建或更新Django用户
        
        Args:
            user_info: Lark用户信息
            
        Returns:
            Django User对象
        """
        try:
            logger.info(f"🔄 处理用户信息: {user_info}")
            
            with transaction.atomic():
                # ⚠️ 修复：尝试多种方式获取用户标识
                lark_user_id = (
                    user_info.get('user_id') or 
                    user_info.get('sub') or 
                    user_info.get('open_id') or 
                    user_info.get('union_id')
                )
                
                # 获取其他信息
                email = user_info.get('email', '')
                name = user_info.get('name', '') or user_info.get('en_name', '')
                avatar_url = user_info.get('avatar_url', '') or user_info.get('picture', '')
                
                logger.info(f"   提取的信息:")
                logger.info(f"   - user_id: {lark_user_id}")
                logger.info(f"   - email: {email}")
                logger.info(f"   - name: {name}")
                logger.info(f"   - avatar_url: {avatar_url}")
                
                if not lark_user_id:
                    logger.error(f"❌ 无法从用户信息中获取ID")
                    logger.error(f"   可用字段: {list(user_info.keys())}")
                    raise LarkOAuthError(f"无法获取用户ID，可用字段: {list(user_info.keys())}")
                
                # 构造用户名
                if email:
                    username_base = email.split('@')[0]
                else:
                    username_base = f"lark_user_{lark_user_id}"
                
                username = username_base
                
                # 尝试通过邮箱或用户名查找现有用户
                user = None
                if email:
                    user = User.objects.filter(email=email).first()
                    if user:
                        logger.info(f"   ✅ 通过邮箱找到现有用户: {user.username}")
                
                if not user:
                    user = User.objects.filter(username=username).first()
                    if user:
                        logger.info(f"   ✅ 通过用户名找到现有用户: {user.username}")
                
                if user:
                    # 更新现有用户信息
                    updated = False
                    if name and not user.first_name:
                        names = name.split(' ', 1)
                        user.first_name = names[0]
                        if len(names) > 1:
                            user.last_name = names[1]
                        updated = True
                    
                    if email and not user.email:
                        user.email = email
                        updated = True
                    
                    if updated:
                        user.save()
                        logger.info(f"   ✅ 更新现有用户信息")
                else:
                    # 创建新用户
                    names = name.split(' ', 1) if name else ['', '']
                    first_name = names[0]
                    last_name = names[1] if len(names) > 1 else ''
                    
                    # 确保用户名唯一性
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}_{counter}"
                        counter += 1
                    
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        is_active=True
                    )
                    logger.info(f"   ✅ 创建新用户: {user.username}")
                
                # 更新用户资料中的头像（如果有UserProfile模型）
                if avatar_url and hasattr(user, 'profile'):
                    try:
                        # 这里可以选择下载并保存头像
                        # 为了简化，这里先跳过
                        pass
                    except Exception as e:
                        logger.warning(f"   ⚠️ 更新用户头像失败: {str(e)}")
                
                logger.info(f"✅ 用户处理完成: {user.username} (ID: {user.id})")
                return user
                
        except Exception as e:
            logger.error(f"❌ 创建/更新用户失败: {str(e)}")
            raise LarkOAuthError(f"用户处理失败: {str(e)}")
    
    def complete_oauth_flow(self, code: str, state: str) -> Tuple[User, Dict]:
        """
        完整的OAuth流程
        
        Args:
            code: 授权码
            state: 状态参数
            
        Returns:
            (User对象, 用户信息字典)
        """
        logger.info("="*60)
        logger.info("🚀 开始完整的 OAuth 流程")
        
        # 验证state
        if not self.verify_state(state):
            logger.error("❌ State参数验证失败")
            raise LarkOAuthError("无效的state参数，可能存在CSRF攻击")
        
        logger.info("✅ State验证通过")
        
        # 换取访问令牌
        try:
            logger.info("📝 步骤1: 换取访问令牌")
            token_data = self.exchange_code_for_token(code)
            access_token = token_data['access_token']
            logger.info(f"✅ 获得访问令牌: {access_token[:20]}...")
            
            # 获取用户信息
            logger.info("📝 步骤2: 获取用户信息")
            user_info = self.get_user_info(access_token)
            
            # 创建或更新用户
            logger.info("📝 步骤3: 创建/更新用户")
            user = self.create_or_update_user(user_info)
            
            logger.info(f"✅ OAuth流程完成，用户: {user.username}")
            logger.info("="*60)
            
            return user, user_info
            
        except LarkOAuthError:
            raise
        except Exception as e:
            logger.error(f"❌ OAuth流程异常: {str(e)}", exc_info=True)
            raise LarkOAuthError(f"登录流程失败: {str(e)}")


# 全局实例
lark_oauth_client = LarkOAuthClient()