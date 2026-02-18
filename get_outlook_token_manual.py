
import asyncio
import sys
import webbrowser
from urllib.parse import urlencode, parse_qs, urlparse
import json
import httpx

# 配置
CLIENT_ID = "cdcec7ef-a48f-47f1-a978-5a9eed0d5dc7"
REDIRECT_URI = "http://localhost:8000/callback"
SCOPE = "offline_access https://outlook.office.com/IMAP.AccessAsUser.All https://outlook.office.com/SMTP.Send"
AUTHORITY = "https://login.microsoftonline.com/common"

async def get_token(client_id, client_secret=None, redirect_uri=REDIRECT_URI):
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
    print(auth_url)
    print("="*50 + "\n")
    print("注意：登录成功后，浏览器可能会显示“无法连接”或空白页，这是正常的！")
    print("请查看浏览器的地址栏，它会变成 http://localhost:8000/callback?code=...")
    print("请把那个完整的地址复制下来，粘贴到下面：")
    
    # 2. 手动输入回调 URL
    callback_url = input("\nPaste the full redirect URL here: ").strip()
    
    try:
        query = urlparse(callback_url).query
        params = parse_qs(query)
        auth_code = params.get("code", [None])[0]
    except:
        print("无效的 URL")
        return

    if not auth_code:
        print("未找到 Authorization Code，请检查链接是否正确。")
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
            print("-" * 50)
            print(tokens.get("refresh_token"))
            print("-" * 50)
            print("请复制上面这串 Token，填入 CSV 文件的 refresh_token 列。")
        else:
            print(f"\n❌ 获取 Token 失败: {resp.text}")

if __name__ == "__main__":
    cid = input(f"Enter Client ID [{CLIENT_ID}]: ").strip() or CLIENT_ID
    csec = input("Enter Client Secret (Empty if public client): ").strip()
    ruri = input(f"Enter Redirect URI [{REDIRECT_URI}]: ").strip() or REDIRECT_URI
    
    try:
        asyncio.run(get_token(cid, csec, ruri))
    except KeyboardInterrupt:
        print("\nAborted.")
