"""
Mailbox Manager - Windows Launcher
"""
import os
import sys
import webbrowser
import time
from pathlib import Path
import socket


def find_free_port(start_port=8000):
    """Find an available port"""
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None


def main():
    """Main launcher function"""
    # Get application directory
    if getattr(sys, 'frozen', False):
        app_dir = Path(sys._MEIPASS)
        exe_dir = Path(sys.executable).parent
    else:
        app_dir = Path(__file__).parent
        exe_dir = app_dir
    
    print("=" * 60)
    print("Mailbox Manager - Windows Edition")
    print("=" * 60)
    print(f"Program directory: {exe_dir}")
    
    # Find available port
    backend_port = find_free_port(8000)
    if not backend_port:
        print("Error: Cannot find available port (8000-8100)")
        input("Press Enter to exit...")
        return
    
    print(f"Backend port: {backend_port}")
    os.environ['PORT'] = str(backend_port)
    
    # Check database
    db_file = exe_dir / "mailbox.db"
    if not db_file.exists():
        print(f"Initializing database: {db_file}")
    
    # Start backend service
    print("\nStarting backend service...")
    try:
        # Add backend to path
        backend_path = app_dir / "backend"
        if backend_path.exists():
            sys.path.insert(0, str(backend_path))
        
        from uvicorn import run
        from main import app
        
        # Start server in background thread
        import threading
        server_thread = threading.Thread(
            target=lambda: run(
                app,
                host="127.0.0.1",
                port=backend_port,
                log_level="info"
            ),
            daemon=True
        )
        server_thread.start()
        
        # Wait for server to start
        print("Waiting for server to start...")
        time.sleep(3)
        
        # Open browser
        frontend_url = f"http://127.0.0.1:{backend_port}"
        print(f"\nOpening browser: {frontend_url}")
        webbrowser.open(frontend_url)
        
        print("\n" + "=" * 60)
        print("Service started successfully!")
        print(f"Access URL: {frontend_url}")
        print("Default login: admin / admin123")
        print("\nPress Ctrl+C to stop the service")
        print("=" * 60 + "\n")
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping service...")
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
