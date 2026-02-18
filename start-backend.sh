#!/bin/bash

# 启动后端服务（保持运行）

cd "$(dirname "$0")/backend"

# 确保数据目录存在
mkdir -p data

echo "=== 启动 Mailbox Manager 后端 ==="
echo "日志文件: backend/logs/backend.log"
echo ""

# 使用 exec 保持进程在前台运行
exec ~/.local/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info
