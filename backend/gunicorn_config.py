import multiprocessing
import os

# 绑定地址
bind = "127.0.0.1:8000"

# Worker 进程数
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000

# 超时设置
timeout = 60
keepalive = 2
graceful_timeout = 30

# 日志配置
accesslog = "/home/django_user/TH_Project/backend/logs/gunicorn_access.log"
errorlog = "/home/django_user/TH_Project/backend/logs/gunicorn_error.log"
loglevel = "info"

# 进程命名
proc_name = "th_project_django"

# 安全
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
limit_request_body = 209715200 # 200 MB in bytes (200 * 1024 * 1024)
