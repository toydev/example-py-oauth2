"""
OAuth 2.0 クライアントアプリケーション

認可コードフローを使用してアクセストークンを取得し、
保護されたAPIに継続的にアクセスする
"""

from fastapi import FastAPI, Request, Cookie, Response
from fastapi.responses import HTMLResponse, RedirectResponse
import httpx
import secrets
from typing import Optional
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime

app = FastAPI(title="OAuth 2.0 Client")

# セッション署名用の秘密鍵（本番環境では環境変数から読み込む）
SECRET_KEY = "fastapi-custom-client-secret-key-change-in-production"
serializer = URLSafeTimedSerializer(SECRET_KEY)

# OAuth 2.0設定
OAUTH_CONFIG = {
    "client_id": "demo-client-id",
    "client_secret": "demo-client-secret",
    "authorization_endpoint": "http://localhost:5000/authorize",
    "token_endpoint": "http://localhost:5000/token",
    "redirect_uri": "http://localhost:5001/callback",
    "api_base": "http://localhost:5000/api",
}

# セッションストレージ（本番環境ではRedisなどを使用）
sessions = {}


def get_session_id(session_cookie: Optional[str]) -> Optional[str]:
    """CookieからセッションIDを取得"""
    if not session_cookie:
        return None
    try:
        return serializer.loads(session_cookie, max_age=3600)
    except:
        return None


def get_access_token(session_id: Optional[str]) -> Optional[str]:
    """セッションIDからアクセストークンを取得"""
    if not session_id or session_id not in sessions:
        return None
    return sessions[session_id].get("access_token")


@app.get("/")
async def home(session: Optional[str] = Cookie(None)):
    """
    ホーム画面
    """
    session_id = get_session_id(session)
    access_token = get_access_token(session_id)

    if access_token:
        # ログイン済み - ダッシュボードにリダイレクト
        return RedirectResponse(url="/dashboard", status_code=302)

    # 未ログイン - ログイン画面を表示
    html_content = """
    <html>
        <head><title>OAuth 2.0 Client Demo</title></head>
        <body>
            <h1>OAuth 2.0 クライアントデモ</h1>
            <p>このアプリは OAuth 2.0 認可コードフローのデモです</p>
            <h2>ステップ：</h2>
            <ol>
                <li><a href="/login">ログイン</a> をクリック</li>
                <li>認可サーバーでログイン・同意</li>
                <li>コールバックでアクセストークン取得</li>
                <li>ダッシュボードで継続的にAPIを呼び出し</li>
            </ol>
            <a href="/login" style="
                display: inline-block;
                margin-top: 20px;
                padding: 10px 20px;
                background-color: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
            ">ログイン</a>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/login")
async def login():
    """
    認可フローの開始
    ユーザーを認可サーバーにリダイレクト
    """
    # 古いセッションデータをクリア
    sessions.clear()

    # CSRF対策用のstateパラメータを生成
    state = secrets.token_urlsafe(16)
    sessions[state] = {"status": "pending"}

    # 認可リクエストのURLを構築
    auth_url = (
        f"{OAUTH_CONFIG['authorization_endpoint']}"
        f"?response_type=code"
        f"&client_id={OAUTH_CONFIG['client_id']}"
        f"&redirect_uri={OAUTH_CONFIG['redirect_uri']}"
        f"&state={state}"
        f"&scope=read"
    )

    return RedirectResponse(url=auth_url, status_code=302)


@app.get("/callback")
async def callback(code: str, state: Optional[str] = None):
    """
    認可サーバーからのコールバック
    認可コードを受け取り、アクセストークンに交換
    """
    # stateの検証（CSRF対策）
    if not state or state not in sessions:
        return HTMLResponse(
            content="<h1>Error: Invalid state parameter</h1>",
            status_code=400,
        )

    # トークンエンドポイントにリクエスト
    async with httpx.AsyncClient() as client:
        response = await client.post(
            OAUTH_CONFIG["token_endpoint"],
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": OAUTH_CONFIG["redirect_uri"],
                "client_id": OAUTH_CONFIG["client_id"],
                "client_secret": OAUTH_CONFIG["client_secret"],
            },
        )

    if response.status_code != 200:
        return HTMLResponse(
            content=f"<h1>Error: {response.text}</h1>",
            status_code=400,
        )

    token_data = response.json()
    access_token = token_data["access_token"]

    # セッションにアクセストークンを保存
    sessions[state]["access_token"] = access_token
    sessions[state]["status"] = "authorized"
    sessions[state]["token_data"] = token_data

    # セッションCookieを設定してダッシュボードにリダイレクト
    response = RedirectResponse(url="/dashboard", status_code=302)
    session_cookie = serializer.dumps(state)
    response.set_cookie(
        key="session",
        value=session_cookie,
        httponly=True,
        max_age=3600,
    )
    return response


@app.get("/dashboard")
async def dashboard(session: Optional[str] = Cookie(None)):
    """
    ダッシュボード画面
    ログイン後、継続的にAPIを呼び出せる
    """
    session_id = get_session_id(session)
    access_token = get_access_token(session_id)

    if not access_token:
        # 未ログイン - ホームにリダイレクト
        return RedirectResponse(url="/", status_code=302)

    # セッション情報を取得
    session_data = sessions.get(session_id, {})
    token_data = session_data.get("token_data", {})

    html_content = f"""
    <html>
        <head>
            <title>Dashboard - OAuth 2.0 Client</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 1000px; margin: 0 auto; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .button {{
                    display: inline-block;
                    padding: 10px 20px;
                    margin: 5px;
                    background-color: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    cursor: pointer;
                    border: none;
                }}
                .button:hover {{ background-color: #0056b3; }}
                .logout {{ background-color: #dc3545; }}
                .logout:hover {{ background-color: #c82333; }}
                pre {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                #api-result {{ min-height: 100px; }}
            </style>
            <script>
                async function callAPI(endpoint) {{
                    const resultDiv = document.getElementById('api-result');
                    resultDiv.innerHTML = '<p>Loading...</p>';

                    try {{
                        const response = await fetch(`/api/call/${{endpoint}}`);
                        const data = await response.json();

                        if (response.ok) {{
                            resultDiv.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                        }} else {{
                            resultDiv.innerHTML = '<pre style="color: red;">Error: ' + JSON.stringify(data, null, 2) + '</pre>';
                        }}
                    }} catch (error) {{
                        resultDiv.innerHTML = '<pre style="color: red;">Error: ' + error.message + '</pre>';
                    }}
                }}
            </script>
        </head>
        <body>
            <div class="container">
                <h1>ダッシュボード</h1>

                <div class="section">
                    <h2>認証情報</h2>
                    <p><strong>アクセストークン:</strong> <code>{access_token[:20]}...{access_token[-20:]}</code></p>
                    <p><strong>トークンタイプ:</strong> {token_data.get('token_type', 'Bearer')}</p>
                    <p><strong>有効期限:</strong> {token_data.get('expires_in', 3600)}秒</p>
                    <a href="/logout" class="button logout">ログアウト</a>
                </div>

                <div class="section">
                    <h2>保護されたAPIを呼び出す</h2>
                    <p>以下のボタンをクリックして、アクセストークンを使ってAPIを呼び出します：</p>
                    <button class="button" onclick="callAPI('me')">GET /api/me (ユーザー情報)</button>
                    <button class="button" onclick="callAPI('posts')">GET /api/posts (投稿一覧)</button>
                    <button class="button" onclick="callAPI('profile')">GET /api/profile (プロフィール)</button>
                </div>

                <div class="section">
                    <h2>API レスポンス</h2>
                    <div id="api-result">
                        <p>上のボタンをクリックしてAPIを呼び出してください</p>
                    </div>
                </div>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/call/{endpoint}")
async def call_api(endpoint: str, session: Optional[str] = Cookie(None)):
    """
    保護されたAPIを呼び出す
    """
    session_id = get_session_id(session)
    access_token = get_access_token(session_id)

    if not access_token:
        return {"error": "Not authenticated"}, 401

    # APIを呼び出し
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{OAUTH_CONFIG['api_base']}/{endpoint}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if response.status_code != 200:
        return {"error": response.text, "status_code": response.status_code}

    return response.json()


@app.get("/logout")
async def logout(session: Optional[str] = Cookie(None)):
    """
    ログアウト
    """
    session_id = get_session_id(session)
    if session_id and session_id in sessions:
        del sessions[session_id]

    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("session")
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
