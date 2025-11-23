#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import django
import requests
from getpass import getpass
from bs4 import BeautifulSoup
import redis
from django.conf import settings

# ================== 初始化 Django ==================
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')  # 根据你的项目修改
django.setup()

# ================== 用户输入 ==================
print("=== Django Admin Session 验证 ===")
admin_url = input("请输入 Admin URL (例如 https://trippalholiday.my/admin/): ").strip()
sessionid = getpass("请输入 Admin sessionid: ").strip()

if not admin_url.endswith('/'):
    admin_url += '/'

# ================== 模式1：Admin 页面访问验证 ==================
def check_admin_page(sessionid, admin_url):
    session = requests.Session()
    session.cookies.set('sessionid', sessionid, domain=admin_url.split("//")[1].split("/")[0])

    try:
        resp = session.get(admin_url, allow_redirects=True, timeout=10)
        if resp.status_code == 200 and "Log in" not in resp.text:
            print(f"[页面验证] ✅ Admin 页面访问成功，状态码: {resp.status_code}")
        elif "Log in" in resp.text:
            print(f"[页面验证] ❌ Session 无效或已过期，页面返回登录页")
        else:
            print(f"[页面验证] ⚠️ Admin 页面访问异常，状态码: {resp.status_code}")

        # 显示 CSRF Token（可选）
        soup = BeautifulSoup(resp.text, "html.parser")
        csrf_input = soup.find("input", {"name": "csrfmiddlewaretoken"})
        if csrf_input:
            print(f"[页面验证] CSRF Token: {csrf_input.get('value')}")
        else:
            print("[页面验证] ⚠️ 页面中未找到 CSRF Token")
    except requests.RequestException as e:
        print(f"[页面验证] ❌ 请求异常: {e}")

# ================== 模式2：Redis 验证 session ==================
def check_redis_session(sessionid):
    try:
        # 使用 settings 中的 Redis 配置，如果不存在，使用默认
        redis_url = getattr(settings, 'REDIS_URL', "redis://127.0.0.1:6379/1")

        r = redis.StrictRedis.from_url(redis_url, decode_responses=True)
        
        # 尝试匹配 Django cache session 前缀
        keys = r.keys(f"*{sessionid}*")
        if keys:
            print(f"[Redis验证] ✅ Redis 中存在 session: {keys}")
        else:
            print(f"[Redis验证] ❌ Redis 中 session 不存在: {sessionid}")
    except Exception as e:
        print(f"[Redis验证] ⚠️ Redis 连接异常: {e}")

# ================== 执行验证 ==================
print("\n=== 模式1：Admin 页面访问验证 ===")
check_admin_page(sessionid, admin_url)

print("\n=== 模式2：Redis 验证 session ===")
check_redis_session(sessionid)