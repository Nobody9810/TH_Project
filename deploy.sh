#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_DIR="/home/django_user/TH_Project"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
SERVICE_NAME="th-project"

echo -e "${YELLOW}=== TH Project 部署开始 ===${NC}"

# 1. 进入项目目录
cd $PROJECT_DIR || exit

# 2. 拉取最新代码
echo -e "${YELLOW}[1/8] 拉取最新代码...${NC}"
git pull origin main
if [ $? -ne 0 ]; then
    echo -e "${RED}Git pull 失败！${NC}"
    exit 1
fi

# 3. 更新后端
echo -e "${YELLOW}[2/8] 更新后端依赖...${NC}"
cd $BACKEND_DIR
source venv/bin/activate
pip install -r requirements.txt

# 4. 运行数据库迁移
echo -e "${YELLOW}[3/8] 运行数据库迁移...${NC}"
python manage.py migrate

# 5. 收集静态文件
echo -e "${YELLOW}[4/8] 收集静态文件...${NC}"
python manage.py collectstatic --noinput

# 6. 构建前端
echo -e "${YELLOW}[5/8] 构建前端...${NC}"
cd $FRONTEND_DIR
npm install
npm run build

# 7. 重启后端服务
echo -e "${YELLOW}[6/8] 重启后端服务...${NC}"
sudo systemctl restart $SERVICE_NAME

# 8. 重启 Nginx
echo -e "${YELLOW}[7/8] 重启 Nginx...${NC}"
sudo systemctl restart nginx

# 9. 等待服务启动
sleep 3

# 10. 检查服务状态
echo -e "${YELLOW}[8/8] 检查服务状态...${NC}"
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${GREEN}✓ 后端服务运行正常${NC}"
else
    echo -e "${RED}✗ 后端服务启动失败${NC}"
    sudo journalctl -u $SERVICE_NAME -n 20 --no-pager
    exit 1
fi

if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx 运行正常${NC}"
else
    echo -e "${RED}✗ Nginx 启动失败${NC}"
    exit 1
fi

echo -e "${GREEN}=== 部署完成！===${NC}"
echo -e "后端 API: https://api.trippalholiday.my"
echo -e "前端: https://trippalholiday.my"
