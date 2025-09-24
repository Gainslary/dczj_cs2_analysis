#!/bin/bash

# 5E对战平台比赛数据定时抓取启动脚本

echo "🚀 启动5E对战平台比赛数据定时抓取调度器"
echo "=================================================="

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 虚拟环境路径
VENV_DIR="$SCRIPT_DIR/venv"
PID_FILE="$SCRIPT_DIR/scheduler.pid"
LOG_FILE="$SCRIPT_DIR/logs/scheduler_startup.log"

# 创建必要的目录
mkdir -p data logs

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  调度器已经在运行中 (PID: $PID)"
        echo "如需重启，请先运行: ./stop_scheduler.sh"
        exit 1
    else
        echo "🧹 清理过期的PID文件"
        rm -f "$PID_FILE"
    fi
fi

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到python3，请先安装Python 3"
    exit 1
fi

# 检查或创建虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "❌ 创建虚拟环境失败"
        exit 1
    fi
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source "$VENV_DIR/bin/activate"

# 升级pip
echo "⬆️  升级pip..."
pip install --upgrade pip > /dev/null 2>&1

# 检查并安装依赖
echo "📦 检查依赖包..."
python -c "import requests, schedule, dateutil, pymysql" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📥 安装依赖包..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        pip install requests schedule python-dateutil pymysql
    fi
    
    if [ $? -ne 0 ]; then
        echo "❌ 依赖包安装失败"
        exit 1
    fi
fi

# 启动调度器（后台运行）
echo "🕐 启动调度器（后台运行）..."
nohup python scheduler.py > "$LOG_FILE" 2>&1 &
SCHEDULER_PID=$!

# 保存PID
echo $SCHEDULER_PID > "$PID_FILE"

# 等待一下确保启动成功
sleep 3

# 检查进程是否还在运行
if ps -p $SCHEDULER_PID > /dev/null 2>&1; then
    echo "✅ 调度器启动成功！"
    echo "   PID: $SCHEDULER_PID"
    echo "   日志文件: $LOG_FILE"
    echo "   停止调度器: ./stop_scheduler.sh"
    echo "   查看日志: tail -f $LOG_FILE"
else
    echo "❌ 调度器启动失败，请检查日志: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi