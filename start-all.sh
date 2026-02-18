#!/bin/bash

# 启动 Mailbox Manager - 前端和后端一起启动

cd "$(dirname "$0")"

echo "=== 🚀 启动 Mailbox Manager ==="
echo ""

# 停止已存在的服务
echo "1. 清理旧进程..."
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "vite" 2>/dev/null
sleep 2

# 创建日志目录
mkdir -p logs

echo ""
echo "2. 启动后端服务 (http://localhost:8000)..."
cd backend
mkdir -p data

# 使用 nohup 让后端在后台运行
nohup ~/.local/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "   后端 PID: $BACKEND_PID"
cd ..

# 等待后端启动
echo "   等待后端启动..."
sleep 3

# 检查后端是否成功启动
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "   ✅ 后端启动成功"
else
    echo "   ⚠️  后端启动中，可能需要等待更长时间"
fi

echo ""
echo "3. 启动前端服务 (http://localhost:5173)..."
cd frontend

# 使用 nohup 让前端在后台运行
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   前端 PID: $FRONTEND_PID"
cd ..

# 等待前端启动
echo "   等待前端启动..."
sleep 5

# 检查前端是否成功启动
if curl -s http://localhost:5173/ > /dev/null 2>&1; then
    echo "   ✅ 前端启动成功"
else
    echo "   ⚠️  前端启动中，可能需要等待更长时间"
fi

echo ""
echo "=== ✅ 服务启动完成 ==="
echo ""
echo "📍 访问地址:"
echo "   🌐 前端界面: http://localhost:5173"
echo "   🔌 后端 API: http://localhost:8000"
echo "   📚 API 文档: http://localhost:8000/docs"
echo ""
echo "📁 日志文件:"
echo "   后端日志: ./logs/backend.log"
echo "   前端日志: ./logs/frontend.log"
echo ""
echo "🛑 停止服务:"
echo "   执行: ./stop-all.sh"
echo ""
echo "查看运行状态:"
echo "   后端: curl http://localhost:8000/"
echo "   前端: curl http://localhost:5173/"
