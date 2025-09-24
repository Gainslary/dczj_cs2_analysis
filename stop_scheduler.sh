#!/bin/bash

# 5E对战平台比赛数据定时抓取停止脚本

echo "🛑 停止5E对战平台比赛数据定时抓取调度器"
echo "=================================================="

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE="$SCRIPT_DIR/scheduler.pid"

# 检查PID文件是否存在
if [ ! -f "$PID_FILE" ]; then
    echo "⚠️  未找到PID文件，调度器可能未运行"
    exit 1
fi

# 读取PID
PID=$(cat "$PID_FILE")

# 检查进程是否存在
if ! ps -p $PID > /dev/null 2>&1; then
    echo "⚠️  进程 $PID 不存在，清理PID文件"
    rm -f "$PID_FILE"
    exit 1
fi

# 停止进程
echo "🔄 正在停止调度器 (PID: $PID)..."
kill $PID

# 等待进程结束
for i in {1..10}; do
    if ! ps -p $PID > /dev/null 2>&1; then
        echo "✅ 调度器已成功停止"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# 如果进程仍然存在，强制杀死
echo "⚠️  进程未响应，强制停止..."
kill -9 $PID

# 再次检查
if ! ps -p $PID > /dev/null 2>&1; then
    echo "✅ 调度器已强制停止"
    rm -f "$PID_FILE"
else
    echo "❌ 无法停止调度器进程"
    exit 1
fi