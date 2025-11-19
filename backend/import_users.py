import os
import sys
import openpyxl
from django.db import transaction # 导入事务
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError
import django # 保持 django 导入在顶部


# 尝试导入拼音库
try:
    from pypinyin import lazy_pinyin
    HAS_PINYIN = True
except ImportError:
    HAS_PINYIN = False

# ======================================
# Django 初始化
# ======================================
# 确保项目路径正确设置
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(project_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.contrib.auth.models import User, Group
# 假设 UserProfile 模型位于 api.models (用于联系手机字段)
try:
    from api.models import UserProfile
except ImportError:
    UserProfile = None


def to_username(name):
    """将中文姓名转为拼音，如果无拼音库则用安全 fallback 方案"""
    name = str(name).strip()
    if HAS_PINYIN:
        # 使用 pypinyin 将中文转为拼音小写，并去除空格
        return "".join(lazy_pinyin(name, style=2)).lower().replace(' ', '')
    
    # 安全的 fallback 方案: 移除非字母数字字符
    return ''.join(c for c in name if c.isalnum()).lower()


DEFAULT_PASSWORD = "TrippalHoliday123"


def import_users_from_excel(path, target_group=None):
    """
    从 Excel 导入用户，并设置 is_staff=True，同时将用户分配到目标组。
    """
    print(f"📄 正在读取 Excel 文件: {path}")

    try:
        wb = openpyxl.load_workbook(path)
    except FileNotFoundError:
        print(f"❌ 错误: 找不到文件 {path}")
        return
    
    sheet = wb.active

    created_count = 0
    skipped = 0

    # 自动识别表头
    headers = {str(cell.value).strip(): idx for idx, cell in enumerate(sheet[1]) if cell.value is not None}

    name_col = headers.get("姓名")
    phone_col = headers.get("联系手机")
    email_col = headers.get("工作邮箱")

    if name_col is None or phone_col is None or email_col is None:
        print("❌ Excel 缺少必要的表头：姓名 / 联系手机 / 工作邮箱")
        return

    # 从第二行开始遍历数据
    for row in sheet.iter_rows(min_row=2):
        
        try:
            name_val = row[name_col].value
            phone_val = row[phone_col].value
            email_val = row[email_col].value
        except IndexError:
            continue
            
        name = str(name_val).strip() if name_val else ''
        phone = str(phone_val).strip() if phone_val else ''
        email = str(email_val).strip() if email_val else ''


        if not name:
            continue

        # email 作为唯一性判断
        if email and User.objects.filter(email=email).exists():
            skipped += 1
            print(f"⏭ 邮箱已存在，跳过: {email}")
            continue

        # 生成 username
        username_base = to_username(name)
        original = username_base
        counter = 1
        username = original
        while User.objects.filter(username=username).exists():
            username = f"{original}{counter}"
            counter += 1

        # --- 创建用户事务 ---
        try:
            with transaction.atomic():
                # 1. 创建 User
                user = User.objects.create(
                    username=username,
                    email=email,
                    first_name=name
                )
                user.set_password(DEFAULT_PASSWORD)
                
                # 2. 关键：设置 is_staff=True (满足 Admin 登录要求)
                user.is_staff = True
                user.save()

                # 3. 关键：分配到目标组
                if target_group:
                    user.groups.add(target_group)
                
                # 4. Profile 自动由 signal 创建/更新
                if UserProfile and hasattr(user, 'profile'):
                    profile = user.profile
                    profile.phone = phone
                    profile.save()

                created_count += 1
                print(f"✅ 已创建用户：{name}（username={username}, email={email}）")
        
        except IntegrityError as e:
            skipped += 1
            print(f"❌ 错误: 创建用户 {name} 时发生数据库完整性错误 - {e}")
        except Exception as e:
            skipped += 1
            print(f"❌ 错误: 创建用户 {name} 时发生未知错误 - {e}")


    print("\n===============================")
    print(f"🎉 导入完成！新增 {created_count} 个用户，跳过 {skipped} 个")
    print("===============================")


if __name__ == "__main__":
    
    print("--- 任务开始 ---")

    # 1. 关键修改：删除所有用户
    print("\n🧹 正在删除所有现有用户...")
    deleted_count, _ = User.objects.all().delete()
    print(f"✅ 已成功删除 {deleted_count} 个现有用户。")
    
    
    # 2. 查找目标用户组
    GROUP_NAME = "用户"
    target_group = None
    try:
        target_group = Group.objects.get(name=GROUP_NAME)
        print(f"✅ 找到目标用户组: {target_group.name}")
    except Group.DoesNotExist:
        print(f"❌ 错误: 找不到名为 '{GROUP_NAME}' 的用户组。请先在 Admin 后台创建该组。")
        sys.exit(1) # 找不到组，终止脚本
        
        
    # 3. 导入用户
    excel_path = "用户导入模板.xlsx"  # 确保文件名正确
    import_users_from_excel(excel_path, target_group=target_group)
    
    
    # 4. 创建超级用户
    ADMIN_USERNAME = "Admin"
    ADMIN_EMAIL = "admin@example.com"
    ADMIN_PASSWORD = "112233" 
    
    print(f"\n⭐ 正在创建超级用户: {ADMIN_USERNAME}...")
    try:
        if not User.objects.filter(username=ADMIN_USERNAME).exists():
            User.objects.create_superuser(
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                password=ADMIN_PASSWORD
            )
            print(f"✅ 成功创建超级用户 '{ADMIN_USERNAME}'，密码为 '{ADMIN_PASSWORD}'")
        else:
            print(f"⏭ 超级用户 '{ADMIN_USERNAME}' 已存在，跳过创建。")
    except Exception as e:
        print(f"❌ 错误: 创建超级用户 '{ADMIN_USERNAME}' 时失败 - {e}")
    
    print("\n--- 任务结束 ---")