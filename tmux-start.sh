#!/bin/bash

# 使用 tmux 启动所有服务

SESSION_NAME="mailbox"

cd "$(dirname "$0")"

# 检查是否已有同名 session
if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "Session '$SESSION_NAME' 已存在"
    echo "连接到现有 session: tmux attach -t $SESSION_NAME"
    exit 0
fi

# 创建新的 tmux session
tmux new-session -d -s $SESSION_NAME -n "backend"

# 在第一个窗口启动后端
tmux send-keys -t $SESSION_NAME:backend "./start-backend.sh" C-m

# 创建第二个窗口用于前端
tmux new-window -t $SESSION_NAME -n "frontend"
tmux send-keys -t $SESSION_NAME:frontend "./start-frontend.sh" C-m

# 回到第一个窗口
tmux select-window -t $SESSION_NAME:backend

echo "=== ✅ 服务已启动 ==="
echo ""
echo "tmux session: $SESSION_NAME"
echo "窗口 1 (backend): 后端服务 http://localhost:8000"
echo "窗口 2 (frontend): 前端服务 http://localhost:5173"
echo ""
echo "查看服务: tmux attach -t $SESSION_NAME"
echo "切换窗口: 按 Ctrl+b 然后按数字键 0 或 1"
echo "分离 session: 按 Ctrl+b 然后按 d"
echo "停止服务: ./tmux-stop.sh"
