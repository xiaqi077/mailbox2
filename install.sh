#!/bin/bash
# Mailbox Manager - Linux VPS 一键安装脚本
# 适用于 Ubuntu 20.04+ / Debian 11+ / CentOS 8+

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    else
        echo_error "无法检测操作系统"
        exit 1
    fi
    echo_info "检测到操作系统: $OS $VER"
}

# 检查是否为 root 用户
check_root() {
    if [ "$EUID" -eq 0 ]; then
        echo_warn "检测到 root 用户，建议使用普通用户运行"
        read -p "是否继续? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 安装系统依赖
install_system_deps() {
    echo_info "安装系统依赖..."
    
    if [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "debian" ]]; then
        sudo apt-get update
        sudo apt-get install -y \
            python3 \
            python3-pip \
            python3-venv \
            nodejs \
            npm \
            git \
            curl \
            wget \
            build-essential \
            sqlite3
    elif [[ "$OS" == "centos" ]] || [[ "$OS" == "rhel" ]]; then
        sudo yum install -y \
            python3 \
            python3-pip \
            nodejs \
            npm \
            git \
            curl \
            wget \
            gcc \
            gcc-c++ \
            make \
            sqlite
    else
        echo_error "不支持的操作系统: $OS"
        exit 1
    fi
    
    echo_info "系统依赖安装完成"
}

# 检查 Node.js 版本
check_nodejs() {
    echo_info "检查 Node.js 版本..."
    
    if ! command -v node &> /dev/null; then
        echo_error "Node.js 未安装"
        exit 1
    fi
    
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        echo_warn "Nod版本过低 (当前: v$NODE_VERSION), 建议升级到 v18+"
        echo_info "安装 Node.js 18..."
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi
    
    echo_info "Node.js 版本: $(node -v)"
}

# 检查 Python 版本
check_python() {
    echo_info "检查 Python 版本..."
    
    if ! command -v python3 &> /dev/null; then
        echo_error "Python3 未安装"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo_info "Python 版本: $PYTHON_VERSION"
    
    if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
        echo_error "Python 版本过低，需要 3.8+"
        exit 1
    fi
}

# 创建项目目录
create_project_dir() {
    echo_info "创建项目目录..."
    
    PROJECT_DIR="$HOME/mailbox-manager"
    
    if [ -d "$PROJECT_DIR" ]; then
        echo_warn "项目目录已存在: $PROJECT_DIR"
        read -p "是否删除并重新安装? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$PROJECT_DIR"
        else
            echo_info "使用现有目录"
        fi
    fi
    
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    echo_info "项目目录: $PROJECT_DIR"
}

# 安装后端
install_backend() {
    echo_info "安装后端..."
    
    cd "$PROJECT_DIR/backend"
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        echo_info "创建 Python 虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级 pip
    pip install --upgrade pip
    
    # 安装依赖
    echo_info "安装 Python 依赖..."
    pip install -r requirements.txt
    
    # 创建 .env 文件
    if [ ! -f ".env" ]; then
        echo_info "创建 .env 配置文件..."
        cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=sqlite+aiosqlite:///./mailbox.db
ENVIRONMENT=production
EOF
    fi
    
    deactivate
    
    echo_info "后端安装完成"
}

# 安装前端
install_frontend() {
    echo_info "安装前端..."
    
    cd "$PROJECT_DIR/frontend"
    
    # 安装依赖
    echo_info "安装 Node.js 依赖..."
    npm install
    
    # 构建生产版本
    echo_info "构建前端..."
    npm run build
    
    echo_info "前端安装完成"
}

# 创建 systemd 服务
create_systemd_service() {
    echo_info "创建 systemd 服务..."
    
    # 后端服务
    cat > /tmp/mailbox-backend.service << EOF
[Unit]
Description=Mailbox Manager Backend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR/backend
Environment="PATH=$PROJECT_DIR/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$PROJECT_DIR/backend/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    sudo mv /tmp/mailbox-backend.service /etc/systemd/system/
    
    # 前端服务 (使用 serve 提供静态文件)
    cat > /tmp/mailbox-frontend.service << EOF
[Unit]
Description=Mailbox Manager Frontend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR/frontend
ExecStart=/usr/bin/npx serve -s dist -l 5173
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    sudo mv /tmp/mailbox-frontend.service /etc/systemd/system/
    
    # 重载 systemd
    sudo systemctl daemon-reload
    
    echo_info "systemd 服务创建完成"
}

# 启动服务
start_services() {
    echo_info "启动服务..."
    
    # 启用并启动后端
    sudo systemctl enable mailbox-backend.service
    sudo systemctl start mailbox-backend.service
    
    # 安装 serve (用于提供前端静态文件)
    if ! command -v serve &> /dev/null; then
        echo_info "安装 serve..."
        sudo npm install -g serve
    fi
    
    # 启用并启动前端
    sudo systemctl enable mailbox-frontend.service
    sudo systemctl start mailbox-frontend.service
    
    # 等待服务启动
    sleep 3
    
    # 检查服务状态
    echo_info "检查服务状态..."
    sudo systemctl status mailbox-backend.service --no-pager | head -10
    sudo systemctl status mailbox-frontend.service --no-pager | head -10
    
    echo_info "服务启动完成"
}

# 配置防火墙
configure_firewall() {
    echo_info "配置防火墙..."
    
    if command -v ufw &> /dev/null; then
        sudo ufw allow 8000/tcp comment "Mailbox Backend"
        sudo ufw allow 5173/tcp comment "Mailbox Frontend"
        echo_info "UFW 防火墙规则已添加"
    elif command -v firewall-cmd &> /dev/null; then
        sudo firewall-cmd --permanent --add-port=8000/tcp
        sudo firewall-cmd --permanent --add-port=5173/tcp
        sudo firewall-cmd --reload
        echo_info "firewalld 防火墙规则已添加"
    else
        echo_warn "未检测到防火墙，请手动开放端口 8000 和 5173"
    fi
}

# 显示安装信息
show_info() {
    echo ""
    echo_info "=========================================="
    echo_info "  Mailbox Manager 安装完成！"
    echo_info "=========================================="
    echo ""
    echo_info "项目目录: $PROJECT_DIR"
    echo_info "后端地址: http://$(hostname -I | awk '{print $1}'):8000"
    echo_info "前端地址: http://$(hostname -I | awk '{print $1}'):5173"
    echo ""
    echo_info "服务管理命令:"
    echo "  启动: sudo systemctl start mailbox-{backend,frontend}.service"
    echo "  停止: sudo systemctl stop mailbox-{backend,frontend}.service"
    echo "  重启: sudo systemctl restart mailbox-{backend,frontend}.service"
    echo "  状态: sudo systemctl status mailbox-{backend,frontend}.service"
    echo "  日志: sudo journalctl -u mailbox-backend.service -f"
    echo ""
    echo_info "默认登录账号:"
    echo "  用户名: admin"
    echo "  密码: admin123"
    echo ""
    echo_warn "请及时修改默认密码！"
    echo ""
}

# 主函数
main() {
    echo_info "开始安装 Mailbox Manager..."
    echo ""
    
    detect_os
    check_root
    install_system_deps
    check_nodejs
    check_python
    create_project_dir
    
    # 检查是否已有代码
    if [ ! -d "$PROJECT_DIR/backend" ]; then
        echo_error "未找到项目代码，请先将代码复制到 $PROJECT_DIR"
        echo_info "提示: 可以使用 git clone 或 scp 上传代码"
        exit 1
    fi
    
    install_backend
    install_frontend
    create_systemd_service
    start_services
    configure_firewall
    show_info
    
    echo_info "安装完成！"
}

# 运行主函数
main
