# Linux VPS 部署指南

本指南适用于在 Linux VPS 上部署 Mailbox Manager。

## 系统要求

- **操作系统**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **Python**: 3.8+
- **Node.js**: 18+
- **内存**: 至少 1GB RAM
- **磁盘**: 至少 2GB 可用空间

## 快速安装

### 方法一：使用一键安装脚本（推荐）

1. **上传项目到 VPS**

```bash
# 方法 A: 使用 Git（推荐）
cd ~
git clone https://github.com/xiaqi077/mailbox-manager.git

# 方法 B: 使用 SCP 上传备份文件
scp mailbox-manager-backup-*.tar.gz user@your-vps-ip:~
ssh user@your-vps-ip
tar -xzf mailbox-manager-backup-*.tar.gz
```

2. **运行安装脚本**

```bash
cd mailbox-manager
chmod +x install.sh
./install.sh
```

脚本会自动完成：
- ✅ 检测操作系统
- ✅ 安装系统依赖（Python、Node.js、Git 等）
- ✅ 创建 Python 虚拟环境
- ✅ 安装后端依赖
- ✅ 安装前端依赖并构建
- ✅ 创建 systemd 服务
- ✅ 配置开机自启和自动重启
- ✅ 配置防火墙规则

3. **访问应用**

安装完成后，访问：
- 前端: `http://your-vps-ip:5173`
- 后端 API: `http://your-vps-ip:8000`

默认登录账号：
- 用户名: `admin`
- 密码: `admin123`

**⚠️ 请立即修改默认密码！**

---

### 方法二：手动安装

#### 1. 安装系统依赖

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv nodejs npm git curl wget build-essential sqlite3
```

**CentOS/RHEL:**
```bash
sudo yum install -y python3 python3-pip nodejs npm git curl wget gcc gcc-c++ make sqlite
```

#### 2. 安装 Node.js 18+

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### 3. 克隆项目

```bash
cd ~
git clone https://github.com/xiaqi077/mailbox-manager.git
cd mailbox-manager
```

#### 4. 安装后端

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 创建配置文件
cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=sqlite+aiosqlite:///./mailbox.db
ENVIRONMENT=production
EOF

deactivate
```

#### 5. 安装前端

```bash
cd ../frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 安装 serve（用于提供静态文件）
sudo npm install -g serve
```

#### 6. 创建 systemd 服务

**后端服务:**
```bash
sudo tee /etc/systemd/system/mailbox-backend.service > /dev/null << EOF
[Unit]
Description=Mailbox Manager Backend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/mailbox-manager/backend
Environment="PATH=$HOME/mailbox-manager/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$HOME/mailbox-manager/backend/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

**前端服务:**
```bash
sudo tee /etc/systemd/system/mailbox-frontend.service > /dev/null << EOF
[Unit]
Description=Mailbox Manager Frontend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/mailbox-manager/frontend
ExecStart=/usr/bin/npx serve -s dist -l 5173
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

#### 7. 启动服务

```bash
# 重载 systemd
sudo systemctl daemon-reload

# 启用并启动服务
sudo systemctl enable mailbox-backend.service
sudo systemctl enable mailbox-frontend.service
sudo systemctl start mailbox-backend.service
sudo systemctl start mailbox-frontend.service

# 检查状态
sudo systemctl status mailbox-backend.service
sudo systemctl status mailbox-frontend.service
```

#### 8. 配置防火墙

**UFW (Ubuntu/Debian):**
```bash
sudo ufw allow 8000/tcp
sudo ufw allow 5173/tcp
```

**firewalld (CentOS/RHEL):**
```bash
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent -173/tcp
sudo firewall-cmd --reload
```

---

## 服务管理

### 常用命令

```bash
# 启动服务
sudo systemctl start mailbox-backend.service
sudo systemctl start mailbox-frontend.service

# 停止服务
sudo systemctl stop mailbox-backend.service
sudo systemctl stop mailbox-frontend.service

# 重启服务
sudo systemctl restart mailbox-backend.service
sudo systemctl restart mailbox-frontend.service

# 查看状态
sudo systemctl status mailbox-backend.service
sudo systemctl status mailbox-frontend.service

# 查看日志
sudo journalctl -u mailbox-backend.service -f
sudo journalctl -u mailbox-frontend.service -f

# 禁用开机自启
sudo systemctl disable mailbox-backend.service
sudo systemctl disable mailbox-frontend.service
```

---

## 使用 Nginx 反向代理（推荐）

### 1. 安装 Nginx

```bash
sudo apt-get install -y nginx  # Ubuntu/Debian
sudo yum install -y nginx      # CentOS/RHEL
```

### 2. 配置 Nginx

```bash
sudo tee /etc/nginx/sites-available/mailbox-manager > /dev/null << 'EOF'
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名

    # 前端
    location / {
        proxy_pass http://127.0.0.1:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 启用配置
sudo ln -s /etc/nginx/sites-available/mailbox-manager /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

### 3. 配置 HTTPS（可选但推荐）

```bash
# 安装 Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# 获取 SSL 证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## 故障排查

### 服务无法启动

```bash
# 查看详细日志
sudo journalctl -u mailbox-backend.service -n 50 --no-pager
sudo journalctl -u mailbox-frontend.service -n 50 --no-pager

# 检查端口占用
sudo netstat -tlnp | grep -E '8000|5173'

# 手动测试后端
cd ~/mailbox-manager/backend
source venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 数据库问题

```bash
# 重建数据库
cd ~/mailbox-manager/backend
rm -f mailbox.db
sudo systemctl restart mailbox-backend.service
```

### 权限问题

```bash
# 确保文件所有权正确
sudo chown -R $USER:$USER ~/mailbox-manager
chmod +x ~/mailbox-manager/backend/venv/bin/*
```

---

## 更新部署

```bash
cd ~/mailbox-manager

# 拉取最新代码
git pull origin main

# 更新后端
cd backend
source venv/bin/activate
pip install -r requirements.txt
deactivate

# 更新前端
cd ../frontend
npm install
npm run build

# 重启服务
sudo systemctl restart mailbox-backend.service
sudo systemctl restart mailbox-frontend.service
```

---

## 备份与恢复

### 备份

```bash
# 备份数据库
cp ~/mailbox-manager/backend/mailbox.db ~/mailbox-backup-$(date +%Y%m%d).db

# 备份整个项目
tar -czf ~/mailbox-manager-backup-$(date +%Y%m%d).tar.gz \
  --exclude='node_modules' \
  --exclude='.git' \
  --exclude='__pycache__' \
  ~/mailbox-manager/
```

### 恢复

```bash
# 恢复数据库
cp ~/mailbox-backup-20260218.db ~/mailbox-manager/backend/mailbox.db
sudo systemctl restart mailbox-backend.service
```

---

## 安全建议

1. **修改默认密码** - 首次登录后立即修改
2. **使用 HTTPS** - 配置 SSL 证书
3. **配置防火墙** - 只开放必要端口
4. **定期备份** - 设置自动备份任务
5. **更新系统** - 定期更新系统和依赖包
6. **限制访问** - 使用 Nginx 限制 IP 访问（如需要）

---

## 性能优化

### 1. 使用 Gunicorn（生产环境推荐）

```bash
# 安装 Gunicorn
cd ~/mailbox-manager/backend
source venv/bin/activate
pip install gunicorn

# 修改 systemd 服务
sudo nano /etc/systemd/system/mailbox-backend.service
# 将 ExecStart 改为:
# ExecStart=/path/to/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 2. 配置数据库连接池

编辑 `backend/app/core/database.py`，调整连接池参数。

### 3. 启用 Gzip 压缩

在 Nginx 配置中添加：
```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
```

---

## 联系支持

如有问题，请查看：
- GitHub Issues: https://github.com/xiaqi077/mailbox-manager/issues
- 项目文档: README.md
