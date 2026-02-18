# GitHub Actions 自动打包指南

本项目使用 GitHub Actions 自动构建 Windows EXE 文件。

## 触发方式

### 方式 1：推送版本标签（推荐）

```bash
# 创建版本标签
git tag v1.0.0

# 推送标签到 GitHub
git push origin v1.0.0
```

GitHub Actions 会自动：
1. 在 Windows 环境中构建 EXE
2. 创建 GitHub Release
3. 上传 ZIP 文件到 Release

### 方式 2：手动触发

1. 访问 GitHub 仓库页面
2. 点击 **Actions** 标签
3. 选择 **Build Windows EXE** 工作流
4. 点击 **Run workflow** 按钮
5. 选择分支（通常是 main）
6. 点击 **Run workflow** 确认

构建完成后，在 **Artifacts** 中下载 ZIP 文件（保留 7 天）。

---

## 工作流程

1. **检出代码** - 从 GitHub 拉取最新代码
2. **设置环境** - 安装 Python 3.11 和 Node.js 18
3. **安装依赖** - 安装 Python 和 npm 依赖
4. **构建前端** - 运行 `npm run build`
5. **创建启动器** - 生成 `launcher.py`
6. **打包 EXE** - 使用 PyInstaller 打包
7. **创建 ZIP** - 压缩所有文件
8. **发布 Release** - 自动创建 GitHub Release（仅标签触发）

---

## 下载构建产物

### 从 GitHub Release 下载（推荐）

1. 访问 https://github.com/xiaqi077/mailbox-manager/releases
2. 找到对应版本（如 v1.0.0）
3. 下载 `MailboxManager-Windows-x64.zip`

### 从 Artifacts 下载（手动触发）

1. 访问 https://github.com/xiaqi077/mailbox-manager/actions
2. 点击最新的 **Build Windows EXE** 工作流运行
3. 在 **Artifacts** 部分下载 ZIP 文件

---

## 版本管理

### 创建新版本

```bash
# 1. 更新版本号（可选）
# 编辑 backend/main.py 中的版本号

# 2. 提交更改
git add .
git commit -m "Release v1.0.1"
git push origin main

# 3. 创建标签
git tag v1.0.1
git push origin v1.0.1

# 4. 等待 GitHub Actions 自动构建
# 访问 https://github.com/xiaqi077/mailbox-manager/actions 查看进度
```

### 版本号规范

建议使用语义化版本号：
- `v1.0.0` - 主版本.次版本.修订号
- `v1.0.1` - 修复 bug
- `v1.1.0` - 新功能
- `v2.0.0` - 重大更新

---

## 构建时间

预计构建时间：**10-15 分钟**

- 安装依赖：3-5 分钟
- 构建前端：2-3 分钟
- 打包 EXE：5-7 分钟

---

## 构建产物

### 文件结构

```
MailboxManager-Windows-x64.zip
└── MailboxManager/
    ├── MailboxManager.exe       # 主程序
    ├── backend/                 # 后端代码
    ├── frontend/dist/           # 前端静态文件
    ├── _internal/               # Python 依赖
    ├── README.txt               # 使用说明
    └── .env.example             # 配置示例
```

### 文件大小

- **压缩前**: 约 300-400 MB
- **压缩后**: 约 150-200 MB

---

## 故障排查

### 构建失败

1. **查看日志**
   - 访问 Actions 页面
   - 点击失败的工作流
   - 查看详细日志

2. **常见问题**
   - 依赖安装失败 → 检查 `requirements.txt`
   - 前端构建失败 → 检查 `package.json`
   - PyInstaller 失败 → 检查隐藏导入

### 手动重试

如果构建失败，可以：
1. 修复问题
2. 推送新的提交
3. 重新推送标签：
```bash
git tag -d v1.0.0           # 删除本地标签
git push origin :v1.0.0     # 删除远程标签
git tag v1.0.0              # 重新创建标签
git push origin v1.0.0      # 重新推送
```

---

## 高级配置

### 修改 Python 版本

编辑 `.github/workflows/build-windows.yml`：
```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.12'  # 修改这里
```

### 修改 Node.js 版本

```yaml
- name: Set up Node.js
  uses: actions/setup-node@v3
  with:
    node-version: '20'  # 修改这里
```

### 添加代码签名

如果有代码签名证书：
```yaml
- name: Sign EXE
  run: |
    signtool sign /f certificate.pfx /p ${{ secrets.CERT_PASSWORD }} dist/MailboxManager/MailboxManager.exe
```

---

## 成本

GitHub Actions 免费额度：
- **公开仓库**: 无限制
- **私有仓库**: 每月 2000 分钟

本项目每次构建约 15 分钟，私有仓库每月可构建约 130 次。

---

## 安全说明

### Secrets 管理

如果需要使用敏感信息（如代码签名证书密码）：

1. 访问仓库 **Settings** → **Secrets and variables** → **Actions**
2. 点击 **New repository secret**
3. 添加密钥（如 `CERT_PASSWORD`）
4. 在工作流中使用 `${{ secretsRD }}`

### 权限

工作流使用 `GITHUB_TOKEN` 自动创建 Release，无需额外配置。

---

## 测试工作流

### 首次测试

```bash
# 1. 推送代码
git add .github/workflows/build-windows.yml
git commit -m "Add GitHub Actions workflow"
git push origin main

# 2. 手动触发测试
# 访问 GitHub Actions 页面，点击 "Run workflow"

# 3. 等待构建完成（约 15 分钟）

# 4. 下载 Artifacts 测试
```

### 正式发布

```bash
# 确认测试通过后，创建正式版本
git tag v1.0.0
git push origin v1.0.0

# 访问 Releases 页面查看自动发布的版本
```

---

## 持续集成建议

1. **每次重大更新创建 Release**
2. **使用语义化版本号**
3. **在 Release 中添加更新日志**
4. **测试构建产物后再分发**

---

## 相关链接

- GitHub Actions 文档: https://docs.github.com/actions
- PyInstaller 文档: https://pyinstaller.org/
- 语义化版本: https://semver.org/

---

## 快速开始

```bash
# 1. 提交工作流文件
git add .github/workflows/build-windows.yml
git commit -m "Add GitHub Actions for Windows build"
git push origin main

# 2. 创建第一个版本
git tag v1.0.0
git push origin v1.0.0

# 3. 等待构建完成
# 访问 https://github.com/xiaqi077/mailbox-manager/actions

# 4. 下载 Release
# 访问 https://github.com/xiaqi077/mailbox-manager/releases
```

就这么简单！🎉
