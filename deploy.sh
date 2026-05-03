#!/bin/bash
# 部署脚本 - dorm-check 后端
# 用法: bash deploy.sh

set -e

echo "=== 部署 dorm-check 后端 ==="

# 1. 进入 backend 目录
cd "$(dirname "$0")/backend"

# 2. 激活虚拟环境
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
fi
source .venv/bin/activate

# 3. 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 4. 复制环境变量配置（如不存在）
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "请编辑 .env 文件，填入 ANTHROPIC_API_KEY 和 JWT_SECRET"
fi

# 5. 创建 data 目录（如不存在）
mkdir -p data

# 6. 初始化数据库（如尚未初始化）
if [ ! -f "data/dorm.db" ]; then
    echo "初始化数据库..."
    python -m scripts.init_db
fi

# 7. 停止旧进程
echo "停止旧进程..."
pkill -f "gunicorn.*main:app" 2>/dev/null || true

# 8. 启动服务
echo "启动服务..."
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000 --daemon

echo "部署完成，访问 http://localhost:8000/docs"
