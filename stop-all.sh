#!/bin/bash

echo "=== 🛑 停止 Mailbox Manager ==="
echo ""

echo "1. 停止前端服务..."
pkill -f "npm run dev" 2>/dev/null
pkill -f "vite" 2>/dev/null
sleep 1
echo "   ✅ 前端已停止"

echo ""
echo "2. 停止后端服务..."
pkill -f "uvicorn main:app" 2>/dev/null
sleep 1
echo "   ✅ 后端已停止"

echo ""
echo "=== ✅ 所有服务已停止 ==="
