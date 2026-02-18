
import asyncio
import sys
import webbrowser
from urllib.parse import urlencode, parse_qs, urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json
import httpx

# 配置 (默认值)
CLIENT_ID = "cdcec7ef-a48f-47f1-a978-5a9eed0d5dc7" # 你的 Client ID
REDIRECT_URI = "http://localhost:8000/callback"
SCOPE = "offline_access https://outlook.office.com/IMAP.AccessAsUser.All https://outlook.office.com/SMTP.Send"
AUTHORITY = "https://login.microsoftonline.com/common"

# 全局变量存储 Code
auth_code = None
server = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        if self.path.startswith("/callback"):
            query = urlparse(self.path).query
            params = parse_qs(query)
            if "code" in params:
                auth_code = params["code"][0]
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Login Successful!</h1><p>You can close this window and check the terminal.</p>")
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"<h1>Error: No code found</h1>")
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port):
    global server
    server = HTTPServer(('localhost', port), CallbackHandler)
    print(f"Server listening on port {port}...")
    server.handle_request() # 只处理一次请求

async def get_token(client_id, client_secret=None, redirect_uri=REDIRECT_URI):
    global auth_code
    
    # 1. 构造授权 URL
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": SCOPE,
        "response_mode": "query"
    }
    auth_url = f"{AUTHORITY}/oauth2/v2.0/authorize?{urlencode(params)}"
    
    print("\n" + "="*50)
    print("请在浏览器中打开以下链接进行登录：")
    print("Please open this URL in your browser to login:")
    print(auth_url)
    print("="*50 + "\n")
    
    # 尝试自动打开浏览器
    try:
        webbrowser.open(auth_url)
    except:
        pass
        
    # 2. 启动本地服务器等待回调
    port = int(urlparse(redirect_uri).port or 80)
    server_thread = threading.Thread(target=run_server, args=(port,))
    server_thread.start()
    server_thread.join()
    
    if not auth_code:
        print("未获取到 Authorization Code，退出。")
        return

    print(f"\n获取到 Code: {auth_code[:20]}...")
    
    # 3. 用 Code 换取 Token
    token_url = f"{AUTHORITY}/oauth2/v2.0/token"
    data = {
        "client_id": client_id,
        "scope": SCOPE,
        "code": auth_code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    if client_secret:
        data["client_secret"] = client_secret
        
    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, data=data)
        if resp.status_code == 200:
            tokens = resp.json()
            print("\n" + "="*50)
            print("🎉 登录成功！新的 Refresh Token 如下：")
            print("Login Success! Here is your new Refresh Token:")
            print("-" * 50)
            print(tokens.get("refresh_token"))
            print("-" * 50)
            print("请复制上面这串 Token，填入 CSV 文件的 refresh_token 列。")
            print("Please copy the token above into your CSV file.")
        else:
            print(f"\n❌ 获取 Token 失败: {resp.text}")

if __name__ == "__main__":
    # 读取用户输入或使用默认值
    cid = input(f"Enter Client ID [{CLIENT_ID}]: ").strip() or CLIENT_ID
    csec = input("Enter Client Secret (Empty if public client): ").strip()
    ruri = input(f"Enter Redirect URI [{REDIRECT_URI}]: ").strip() or REDIRECT_URI
    
    try:
        asyncio.run(get_token(cid, csec, ruri))
    except KeyboardInterrupt:
        print("\nAborted.")
