"""
Mailbox Manager - Windows 打包脚本
使用 PyInstaller 将项目打包成 Windows 可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"

def print_step(step, message):
    """打印步骤信息"""
    print(f"\n{'='*60}")
    print(f"[{step}] {message}")
    print('='*60)

def check_requirements():
    """检查构建环境"""
    print_step("1/6", "检查构建环境")
    
    # 检查 Python
    try:
        result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
        print(f"✓ Python: {result.stdout.strip()}")
    except Exception as e:
        print(f"✗ Python 未安装: {e}")
        return False
    
    # 检查 Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        print(f"✓ Node.js: {result.stdout.strip()}")
    except Exception as e:
        print(f"✗ Node.js 未安装: {e}")
        return False
    
    # 检查 npm
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        print(f"✓ npm: {result.stdout.strip()}")
    except Exception as e:
        print(f"✗ npm 未安装: {e}")
        return False
    
    return True

def install_dependencies():
    """安装 Python 依赖"""
    print_step("2/6", "安装 Python 依赖")
    
    requirements_file = BACKEND_DIR / "requirements.txt"
    if not requirements_file.exists():
        print(f"✗ 未找到 {requirements_file}")
        return False
    
    try:
        # 安装项目依赖
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True)
        
        # 安装 PyInstaller
        subprocess.run([
            sys.executable, "-m", "pip", "install", "pyinstaller"
        ], check=True)
        
        print("✓ Python 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 依赖安装失败: {e}")
        return False

def build_frontend():
    """构建前端"""
    print_step("3/6", "构建前端")
    
    if not FRONTEND_DIR.exists():
        print(f"✗ 未找到前端目录: {FRONTEND_DIR}")
        return False  try:
        # 安装前端依赖
        print("安装 npm 依赖...")
        subprocess.run(["npm", "install"], cwd=FRONTEND_DIR, check=True, shell=True)
        
        # 构建前端
        print("构建前端...")
        subprocess.run(["npm", "run", "build"], cwd=FRONTEND_DIR, check=True, shell=True)
        
        # 检查构建产物
        dist_dir = FRONTEND_DIR / "dist"
        if not dist_dir.exists():
            print(f"✗ 前端构建失败，未找到 {dist_dir}")
            return False
        
        print(f"✓ 前端构建完成: {dist_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 前端构建失败: {e}")
        return False

def create_launcher():
    """创建启动器脚本"""
    print_step("4/6", "创建启动器")
    
    launcher_content = '''
import os
import sys
import webbrowser
import time
import subprocess
from pathlib import Path
import socket

def find_free_port(start_port=8000):
    """查找可用端口"""
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

def main():
    # 获取程序目录
    if getattr(sys, 'frozen', False):
        app_dir = Path(sys._MEIPASS)
        exe_dir = Path(sys.executable).parent
    else:
        app_dir = Path(__file__).parent
        exe_dir = app_dir
    
    print("="*60)
    print("Mailbox Manager - Windows 版本")
    print("="*60)
    print(f"程序目录: {exe_dir}")
    print(f"资源目录: {app_dir}")
    
    # 查找可用端口
    backend_port = find_free_port(8000)
    if not backend_port:
        print("错误: 无法找到可用端口")
        input("按回车键退出...")
        return
    
    print(f"\\n后端端口: {backend_port}")
    
    # 设置环境变量
    os.environ['PORT'] = str(backend_port)
    
    # 检查数据库
    db_file = exe_dir / "mailbox.db"
    if not db_file.exists():
        print(f"初始化数据库: {db_file}")
    
    # 启动后端
    print("\\n启动后端服务...")
    try:
        # 添加后端路径到 sys.path
        backend_path = app_dir / "backend"
        if backend_path.exists():
            sys.path.insert(0, str(backend_path))
        
        from uvicorn import run
        from main import app
        
        # 在新线程中启动服务器
        import threading
        server_thread = threading.Thread(
            target=lambda: run(app, host="127.0.0.1", port=backend_port, log_level="info"),
            daemon=True
        )
        server_thread.start()
        
        # 等待服务器启动
        print("等待服务器启动...")
        time.sleep(3)
        
        # 打开浏览器
        frontend_url = f"http://127.0.0.1:{backend_port}"
        print(f"\\n打开浏览器: {frontend_url}")
        webbrowser.open(frontend_url)
        
        print("\\n" + "="*60)
        print("服务已启动！")
        print(f"访问地址: {frontend_url}")
        print("按 Ctrl+C 停止服务")
        print("="*60 + "\\n")
        
        # 保持运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\\n正在停止服务...")
            
    except Exception as e:
        print(f"\\n错误: {e}")
        import traceback
        traceback.print_exc()
        input("\\n按回车键退出...")

if __name__ == "__main__":
    main()
'''
    
    launcher_file = ROOT_DIR / "launcher.py"
    with open(launcher_file, 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    
    print(f"✓ 启动器创建完成: {launcher_file}")
    return True

def build_exe():
    """使用 PyInstaller 打包"""
    print_step("5/6", "打包 EXE")
    
    # 清理旧的构建文件
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    
    # PyInstaller 参数
    pyinstaller_args = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--name=MailboxManager",
        "--onedir",    # 打包成文件夹
        "--icon=NONE",
        
        # 添加后端代码
        f"--add-data={BACKEND_DIR};backend",
        
        # 添加前端构建产物
        f"--add-data={FRONTEND_DIR / 'dist'};frontend/dist",
        
        # 添加配置文件示例
        f"--add-data={BACKEND_DIR / '.env.example'};.",
        
        # 隐藏导入
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.protocols.websockets",
        "--hidden-import=uvicorn.protocols.websockets.auto",
        "--hidden-import=uvicorn.lifespan",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=sqlalchemy.ext.asyncio",
        "--hidden-import=sqlalchemy.dialects.sqlite",
        "--hidden-import=aiosqlite",
        "--hidden-import=httpx",
        "--hidden-import=socks",
        "--hidden-import=socksio",
        
        # 启动器脚本
        str(ROOT_DIR / "launcher.py")
    ]
    
    try:
        subprocess.run(pyinstaller_args, check=True)
        print("✓ EXE 打包完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 打包失败: {e}")
        return False

def create_installer():
    """创建安装包（可选）"""
    print_step("6/6", "创建安装说明")
    
    readme_content = """
# Mailbox Manager - Windows 版本

## 安装说明

1. 解压所有文件到任意目录
2. 双击 `MailboxManager.exe` 启动程序
3. 程序会自动打开浏览器访问管理界面

## 默认登录信息

- 用户名: admin
- 密码: admin123

**请在首次登录后立即修改密码！**

## 数据存储

所有数据存储在程序目录下的 `mailbox.db` 文件中。

## 备份数据

定期备份 `mailbox.db` 文件即可。

## 卸载

直接删除程序文件夹即可。

## 故障排查

如果程序无法启动：
1. 检查是否有杀毒软件拦截
2. 确保端口 8000-8100 未被占用
3. 以管理员身份运行

## 技术支持

GitHub: https://github.com/xiaqi077/mailbox-manager
"""
    
    dist_exe_dir = DIST_DIR / "MailboxManager"
    if dist_exe_dir.exists():
        readme_file = dist_exe_dir / "README.txt"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"✓ 安装说明创建完成: {readme_file}")
    
    return True

def main():
    """主函数"""
    print("\n" + "="*60)
    print("Mailbox Manager - Windows 打包工具")
    print("="*60)
    
    # 检查环境
    if not check_requirements():
        print("\n✗ 环境检查失败")
        input("按回车键退出...")
        return False
    
    # 安装依赖
    if not install_dependencies():
        print("\n✗ 依赖安装失败")
        input("按回车键退出...")
        return False
    
    # 构建前端
    if not build_frontend():
        print("\n✗ 前端构建失败")
        input("按回车键退出...")
        return False
    
    # 创建启动器
    if not create_launcher():
        print("\n✗ 启动器创建失败")
        input("按回车键退出...")
        return False
    
    # 打包 EXE
    if not build_exe():
        print("\n✗ EXE 打包失败")
        input("按回车键退出...")
        return False
    
    # 创建安装说明
    create_installer()
    
    # 完成
    print("\n" + "="*60)
    print("✓ 打包完成！")
    print("="*60)
    print(f"\n输出目录: {DIST_DIR / 'MailboxManager'}")
    print(f"可执行文件: {DIST_DIR / 'MailboxManager' / 'MailboxManager.exe'}")
    print("\n将整个 MailboxManager 文件夹分发给用户即可。")
    input("\n按回车键退出...")
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
        sys.exit(1)
