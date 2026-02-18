#!/bin/bash

# 启动前端服务（保持运行）

cd "$(dirname "$0")/frontend"

echo "=== 启动 Mailbox Manager 前端 ==="
echo "日志输出到控制台"
echo ""

# 使用 exec 保持进程在前台运行
exec npm run dev
