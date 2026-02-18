#!/bin/bash

# 设置颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. 清理旧进程
echo -e "${GREEN}正在停止旧服务...${NC}"
pkill -f "uvicorn main:app"
pkill -f "vite"
sleep 2

# 2. 检查端口占用
if lsof -i :8000 > /dev/null; then
    echo -e "${RED}警告: 端口 8000 (Backend) 依然被占用，尝试强制关闭...${NC}"
    fuser -k 8000/tcp
fi
if lsof -i :5173 > /dev/null; then
    echo -e "${RED}警告: 端口 5173 (Frontend) 依然被占用，尝试强制关闭...${NC}"
    fuser -k 5173/tcp
fi

# 3. 启动后端
echo -e "${GREEN}正在启动后端 (Port 8000)...${NC}"
cd /home/xia/.openclaw/workspace/mailbox-manager/backend
# 清理 __pycache__ 以防万一
find . -name "__pycache__" -type d -exec rm -rf {} +
# 启动
nohup ~/.local/bin/uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/uvicorn.log 2>&1 &
BACKEND_PID=$!
echo "后端 PID: $BACKEND_PID"

# 等待后端启动检测
echo "等待后端初始化..."
for i in {1..10}; do
    if curl -s http://localhost:8000/api/v1/health > /dev/null; then
        echo -e "${GREEN}后端启动成功!${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 10 ]; then
        echo -e "${RED}后端启动超时或失败! 请检查日志: /tmp/uvicorn.log${NC}"
        tail -n 20 /tmp/uvicorn.log
        exit 1
    fi
done

# 4. 启动前端
echo -e "${GREEN}正在启动前端 (Port 5173)...${NC}"
cd /home/xia/.openclaw/workspace/mailbox-manager/frontend
nohup npm run dev > /tmp/vite.log 2>&1 &
FRONTEND_PID=$!
echo "前端 PID: $FRONTEND_PID"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}服务已全部启动!${NC}"
echo -e "后端日志: tail -f /tmp/uvicorn.log"
echo -e "前端日志: tail -f /tmp/vite.log"
echo -e "访问地址: http://localhost:5173"
echo -e "${GREEN}========================================${NC}"
