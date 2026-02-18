# Windows 打包指南

本指南说明如何将 Mailbox Manager 打包成 Windows 可执行文件（.exe）。

## 前提条件

在 Windows 系统上需要安装：
- Python 3.8+ (https://www.python.org/downloads/)
- Node.js 18+ (https://nodejs.org/)
- Git (可选，用于克隆代码)

## 方法一：使用 Python 打包脚本（推荐）

### 1. 准备代码

```bash
# 克隆或下载项目到 Windows 系统
git clone https://github.com/xiaqi077/mailbox-manager.git
cd mailbox-manager
```

### 2. 运行打包脚本

```bash
python build_windows.py
```

脚本会自动完成：
- ✅ 检查 Python 和 Node.js 环境
- ✅ 安装 Python 依赖（包括 PyInstaller）
- ✅ 构建前端（npm install + npm run build）
- ✅ 创建启动器脚本
- ✅ 使用 PyInstaller 打包成 EXE
- ✅ 生成安装说明文件

### 3. 获取打包结果

打包完成后，在 `dist/MailboxManager/` 目录下会生成：
- `MailboxManager.exe` - 主程序
- `backend/` - 后端代码
- `frontend/dist/` - 前端静态文件
- `README.txt` - 使用说明
- 其他依赖文件

### 4. 分发

将整个 `dist/MailboxManager/` 文件夹打包成 ZIP，分发给用户即可。

---

## 方法二：使用批处理脚本

### 1. 运行批处理

```cmd
build_windows.bat
```

### 2. 等待完成

脚本会自动完成所有步骤，最后在 `dist/MailboxManager/` 生成可执行文件。

---

## 打包说明

### 打包内容

- **后端**: FastAPI + SQLAlchemy + 所有 Python 依赖
- **前端**: Vue 3 构建产物（静态 HTML/CSS/JS）
- **数据库**: SQLite（首次运行时自动创建）
- **配置**: .env.example 示例配置

### 打包大小

预计打包后大小：**150-200 MB**（包含所有依赖）

### 启动流程

1. 用户双击 `MailboxManager.exe`
2. 程序查找可用端口（8000-8100）
3. 启动后端服务（FastAPI + Uvicorn）
4. 自动打开浏览器访问前端界面
5. 用户可以正常使用所有功能

---

## 常见问题

### Q: 打包失败，提示缺少模块

**A**: 确保已安装所有依赖：
```bash
pip install -r backend/requirements.txt
pip install pyinstaller
```

### Q: 前端构建失败

**A**: 检查 Node.js 版本，确保 >= 18：
```bash
node --version
npm install -g npm@latest
```

### Q: EXE 文件太大

**A**: 这是正常的，因为包含了：
- Python 解释器
- 所有 Python 库
- Node.js 运行时（如果需要）
- 前端静态文件

可以使用 UPX 压缩（可选）：
```bash
pip install pyinstaller[encryption]
# 在 build_windows.py 中添加 --upx-dir 参数
```

### Q: 杀毒软件报毒

**A**: PyInstaller 打包的程序可能被误报，解决方法：
1. 添加到杀毒软件白名单
2. 使用代码签名证书签名 EXE
3. 向杀毒软件厂商提交误报

### Q: 程序无法启动

**A**: 检查：
1. 是否有杀毒软件拦截
2. 端口 8000-8100 是否被占用
3. 以管理员身份运行
4. 查看 `MailboxManager.log`（如果有）

---

## 高级选项

### 自定义图标

1. 准备 `.ico` 文件（256x256）
2. 修改 `build_windows.py` 中的：
```python
"--icon=path/to/your/icon.ico",
```

### 单文件打包

修改 `build_windows.py`：
```python
"--onefile",  # 替换 --onedir
```

**注意**: 单文件打包会更慢，且首次启动需要解压。

### 添加版本信息

创建 `version.txt`：
```
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    ...
  ),
  ...
)
```

在 PyInstaller 参数中添加：
```python
"--version-file=version.txt",
```

---

## 使用 Inno Setup 创建安装程序（可选）

### 1. 下载 Inno Setup

https://jrsoftware.org/isdl.php

### 2. 创建安装脚本

```iss
[Setup]
AppName=Mailbox Manager
AppVersion=1.0.0
DefaultDirName={pf}\MailboxManager
DefaultGroupName=Mailbox Manager
OutputDir=installer
OutputBaseFilename=MailboxManager-Setup

[Files]
Source: "dist\MailboxManager\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\Mailbox Manager"; Filename: "{app}\MailboxManager.exe"
Name: "{commondesktop}\Mailbox Manager"; Filename: "{app}\MailboxManager.exe"

[Run]
Filename: "{app}\MailboxManager.exe"; Description: "Launch Mailbox Manager"; Flags: postinstall nowait skipifsilent
```

### 3. 编译安装程序

使用 Inno Setup Compiler 编译脚本，生成 `MailboxManager-Setup.exe`。

---

## 测试清单

打包完成后，在干净的 Windows 系统上测试：

- [ ] 双击 EXE 能否正常启动
- [ ] 浏览器是否自动打开
- [ ] 能否正常登录（admin/admin123）
- [ ] 能否添加邮箱账户
- [ ] 能否同步邮件
- [ ] 能否导入/导出账户
- [ ] 代理功能是否正常
- [ ] 关闭程序后重新打开，数据是否保留

---

## 分发建议

### 文件结构

```
MailboxManager-v1.0.0-Windows.zip
├── MailboxManager.exe
├── backend/
├── frontend/
├── _interREADME.txt
└── LICENSE.txt
```

### 发布渠道

1. **GitHub Releases** - 上传 ZIP 文件
2. **网盘分享** - 百度网盘、阿里云盘等
3. **官网下载** - 自建下载页面

### 版本命名

建议格式：`MailboxManager-v1.0.0-Windows-x64.zip`

---

## 更新机制（可选）

可以添加自动更新功能：

1. 在启动器中检查 GitHub Releases
2. 对比版本号
3. 提示用户下载新版本
4. 自动下载并替换文件

---

## 许可证

确保在分发时包含：
- MIT License 文件
- 第三方库的许可证声明
- 版权信息

---

## 技术支持

- GitHub: https://github.com/xiaqi077/mailbox-manager
- Issues: https://github.com/xiaqi077/mailbox-manager/issues
