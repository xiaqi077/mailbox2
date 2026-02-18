#!/bin/bash

# 停止所有服务

SESSION_NAME="mailbox"

echo "=== 🛑 停止 Mailbox Manager ==="
echo ""

# 检查 tmux session 是否存在
if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "1. 停止 tmux session: $SESSION_NAME"
    tmux kill-session -t $SESSION_NAME
    echo "   ✅ 已停止"
else
    echo "1. tmux session '$SESSION_NAME' 不存在"
fi

echo ""
echo "2. 清理残留进程..."
pkill -f "uvicorn main:app" 2>/dev/null && echo "   ✅ 后端进程已清理" || echo "   无后端进程"
pkill -f "vite" 2>/dev/null && echo "   ✅ 前端进程已清理" || echo "   无前端进程"

echo ""
echo "=== ✅ 所有服务已停止 ==="
