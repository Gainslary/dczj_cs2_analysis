#!/bin/bash

# CS:GO API服务器控制脚本
# 适用于CentOS系统部署

# 配置变量
SERVICE_NAME="csgo-api"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_SCRIPT="$SCRIPT_DIR/api_server.py"
PID_FILE="$SCRIPT_DIR/csgo_api.pid"
LOG_FILE="$SCRIPT_DIR/logs/csgo_api.log"
VENV_PATH="$SCRIPT_DIR/venv"
PYTHON_CMD="python3"

# 创建日志目录
mkdir -p "$SCRIPT_DIR/logs"

# 激活虚拟环境
activate_venv() {
    if [ -f "$VENV_PATH/bin/activate" ]; then
        echo "激活虚拟环境: $VENV_PATH"
        source "$VENV_PATH/bin/activate"
        return 0
    else
        echo "警告: 虚拟环境不存在 ($VENV_PATH)"
        echo "将使用系统Python环境"
        return 1
    fi
}

# 检查Python和依赖
check_dependencies() {
    echo "检查Python环境和依赖..."
    
    # 激活虚拟环境
    activate_venv
    
    if ! command -v $PYTHON_CMD &> /dev/null; then
        echo "错误: Python3 未安装"
        exit 1
    fi
    
    if [ ! -f "$SCRIPT_DIR/requirements.txt" ]; then
        echo "警告: requirements.txt 文件不存在"
    else
        echo "安装Python依赖..."
        $PYTHON_CMD -m pip install -r "$SCRIPT_DIR/requirements.txt"
    fi
    
    if [ ! -f "$API_SCRIPT" ]; then
        echo "错误: API服务器脚本 $API_SCRIPT 不存在"
        exit 1
    fi
}

# 启动服务
start_service() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "$SERVICE_NAME 已经在运行 (PID: $PID)"
            return 1
        else
            echo "删除过期的PID文件"
            rm -f "$PID_FILE"
        fi
    fi
    
    echo "启动 $SERVICE_NAME..."
    check_dependencies
    
    # 激活虚拟环境并后台启动API服务器
    if [ -f "$VENV_PATH/bin/activate" ]; then
        nohup bash -c "source $VENV_PATH/bin/activate && $PYTHON_CMD $API_SCRIPT" > "$LOG_FILE" 2>&1 &
    else
        nohup $PYTHON_CMD "$API_SCRIPT" > "$LOG_FILE" 2>&1 &
    fi
    PID=$!
    
    # 保存PID
    echo $PID > "$PID_FILE"
    
    # 等待服务启动
    sleep 3
    
    if ps -p $PID > /dev/null 2>&1; then
        echo "$SERVICE_NAME 启动成功 (PID: $PID)"
        echo "日志文件: $LOG_FILE"
        return 0
    else
        echo "$SERVICE_NAME 启动失败"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 停止服务
stop_service() {
    if [ ! -f "$PID_FILE" ]; then
        echo "$SERVICE_NAME 未运行"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ps -p $PID > /dev/null 2>&1; then
        echo "停止 $SERVICE_NAME (PID: $PID)..."
        kill $PID
        
        # 等待进程结束
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done
        
        # 如果进程仍在运行，强制杀死
        if ps -p $PID > /dev/null 2>&1; then
            echo "强制停止 $SERVICE_NAME..."
            kill -9 $PID
        fi
        
        rm -f "$PID_FILE"
        echo "$SERVICE_NAME 已停止"
        return 0
    else
        echo "$SERVICE_NAME 未运行"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 重启服务
restart_service() {
    echo "重启 $SERVICE_NAME..."
    stop_service
    sleep 2
    start_service
}

# 查看服务状态
status_service() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "$SERVICE_NAME 正在运行 (PID: $PID)"
            echo "内存使用: $(ps -o pid,ppid,rss,vsz,comm -p $PID)"
            return 0
        else
            echo "$SERVICE_NAME 未运行 (PID文件存在但进程不存在)"
            return 1
        fi
    else
        echo "$SERVICE_NAME 未运行"
        return 1
    fi
}

# 查看日志
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "显示最近50行日志:"
        tail -n 50 "$LOG_FILE"
    else
        echo "日志文件不存在: $LOG_FILE"
    fi
}

# 实时查看日志
follow_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "实时查看日志 (Ctrl+C 退出):"
        tail -f "$LOG_FILE"
    else
        echo "日志文件不存在: $LOG_FILE"
    fi
}

# 主函数
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        status_service
        ;;
    logs)
        show_logs
        ;;
    follow)
        follow_logs
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs|follow}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动API服务器"
        echo "  stop    - 停止API服务器"
        echo "  restart - 重启API服务器"
        echo "  status  - 查看服务状态"
        echo "  logs    - 查看最近日志"
        echo "  follow  - 实时查看日志"
        exit 1
        ;;
esac

exit $?