#!/bin/bash
# Gunicorn 生产环境启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
APP_NAME="PX_Tools"
APP_MODULE="app:app"
BIND_ADDRESS="0.0.0.0:10101"
WORKERS=1
WORKER_CLASS="sync"
TIMEOUT=600
LOG_DIR="./logs"
PID_FILE="./logs/gunicorn.pid"
ACCESS_LOG="./logs/access.log"
ERROR_LOG="./logs/error.log"

# 检查虚拟环境
if [ -d "venv" ]; then
    echo -e "${GREEN}检测到虚拟环境，激活中...${NC}"
    source venv/bin/activate
fi

# 检查 gunicorn 是否安装
if ! command -v gunicorn &> /dev/null; then
    echo -e "${RED}错误: gunicorn 未安装${NC}"
    echo "正在安装 gunicorn..."
    pip install gunicorn
    if [ $? -ne 0 ]; then
        echo -e "${RED}安装失败，请手动运行: pip install gunicorn${NC}"
        exit 1
    fi
fi

# 创建日志目录
mkdir -p "$LOG_DIR"

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}警告: 未找到 .env 文件${NC}"
fi

# 函数：启动服务
start_service() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}服务已在运行中 (PID: $PID)${NC}"
            return 1
        else
            echo -e "${YELLOW}清理旧的 PID 文件${NC}"
            rm -f "$PID_FILE"
        fi
    fi
    
    echo -e "${GREEN}启动 $APP_NAME 服务...${NC}"
    echo "绑定地址: $BIND_ADDRESS"
    echo "工作进程数: $WORKERS"
    echo "日志目录: $LOG_DIR"
    
    gunicorn \
        --bind "$BIND_ADDRESS" \
        --workers $WORKERS \
        --worker-class $WORKER_CLASS \
        --timeout $TIMEOUT \
        --pid "$PID_FILE" \
        --access-logfile "$ACCESS_LOG" \
        --error-logfile "$ERROR_LOG" \
        --log-level info \
        --daemon \
        "$APP_MODULE"
    
    sleep 2
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}服务启动成功 (PID: $PID)${NC}"
            echo "查看日志: tail -f $ERROR_LOG"
            return 0
        else
            echo -e "${RED}服务启动失败，请查看日志: $ERROR_LOG${NC}"
            return 1
        fi
    else
        echo -e "${RED}服务启动失败，PID 文件未创建${NC}"
        return 1
    fi
}

# 函数：停止服务
stop_service() {
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}服务未运行（未找到 PID 文件）${NC}"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    if ! ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}服务未运行（进程不存在）${NC}"
        rm -f "$PID_FILE"
        return 1
    fi
    
    echo -e "${YELLOW}停止服务 (PID: $PID)...${NC}"
    kill $PID
    
    # 等待进程结束
    for i in {1..10}; do
        if ! ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}服务已停止${NC}"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done
    
    # 强制杀死
    echo -e "${YELLOW}强制停止服务...${NC}"
    kill -9 $PID
    rm -f "$PID_FILE"
    echo -e "${GREEN}服务已强制停止${NC}"
}

# 函数：重启服务
restart_service() {
    echo -e "${YELLOW}重启服务...${NC}"
    stop_service
    sleep 2
    start_service
}

# 函数：查看状态
status_service() {
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}服务未运行${NC}"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}服务运行中 (PID: $PID)${NC}"
        echo "绑定地址: $BIND_ADDRESS"
        echo "工作进程数: $WORKERS"
        echo ""
        echo "进程信息:"
        ps -p $PID -o pid,ppid,cmd,etime,stat
        return 0
    else
        echo -e "${YELLOW}服务未运行（进程不存在）${NC}"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 函数：查看日志
view_logs() {
    if [ "$1" = "error" ]; then
        tail -f "$ERROR_LOG"
    elif [ "$1" = "access" ]; then
        tail -f "$ACCESS_LOG"
    else
        echo "用法: $0 logs [error|access]"
        echo "  error  - 查看错误日志"
        echo "  access - 查看访问日志"
    fi
}

# 主逻辑
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
        view_logs "$2"
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs [error|access]}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动服务"
        echo "  stop    - 停止服务"
        echo "  restart - 重启服务"
        echo "  status  - 查看服务状态"
        echo "  logs    - 查看日志（error 或 access）"
        echo ""
        echo "配置变量（可在脚本中修改）:"
        echo "  BIND_ADDRESS: $BIND_ADDRESS"
        echo "  WORKERS: $WORKERS"
        echo "  LOG_DIR: $LOG_DIR"
        exit 1
        ;;
esac

exit $?

