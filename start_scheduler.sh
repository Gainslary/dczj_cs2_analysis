#!/bin/bash

# 5E对战平台比赛数据定时抓取启动脚本

echo "🚀 启动5E对战平台比赛数据定时抓取调度器"
echo "=" * 50

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到python3，请先安装Python 3"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖包..."
python3 -c "import requests, schedule, dateutil" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📥 安装依赖包..."
    pip3 install requests schedule python-dateutil
fi

# 创建必要的目录
mkdir -p data logs

# 启动调度器
echo "🕐 启动调度器..."
python3 scheduler.py