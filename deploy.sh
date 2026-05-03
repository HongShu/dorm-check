#!/bin/bash
# 部署脚本 - dorm-check 后端
# 用法: bash deploy.sh

set -e

echo "=== 部署 dorm-check 后端 ==="

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
VENV_DIR="$BACKEND_DIR/.venv"

# 1. 激活虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo "创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

# 2. 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 3. 复制环境变量配置（如不存在）
if [ ! -f "$BACKEND_DIR/.env" ]; then
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
    echo "请编辑 $BACKEND_DIR/.env 文件，填入 ANTHROPIC_API_KEY 和 JWT_SECRET"
fi

# 4. 创建 data 目录（如不存在）
mkdir -p "$BACKEND_DIR/data"

# 5. 初始化数据库（如尚未初始化）
if [ ! -f "$BACKEND_DIR/data/dorm.db" ]; then
    echo "初始化数据库..."
    python -m scripts.init_db
fi

# 6. 安装 systemd 服务（如以 root 运行）
if [ "$(id -u)" -eq 0 ]; then
    SERVICE_FILE="/etc/systemd/system/dorm-check.service"
    cp "$SCRIPT_DIR/deploy/dorm-check.service" "$SERVICE_FILE"

    # 替换脚本路径占位符
    sed -i "s|/home/xxzx/dorm-check|$SCRIPT_DIR|g" "$SERVICE_FILE"
    sed -i "s|/home/xxzx/dorm-check/backend/.venv/bin|$VENV_DIR/bin|g" "$SERVICE_FILE"

    systemctl daemon-reload
    systemctl enable dorm-check
    systemctl restart dorm-check
    echo "服务已启动: systemctl status dorm-check"
else
    echo "请用 root 权限运行以安装 systemd 服务:"
    echo "  sudo bash $SCRIPT_DIR/deploy.sh"
fi

echo "部署完成"
