from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.materials'
    
    def ready(self):
        # 导入信号处理
        import apps.materials.signals