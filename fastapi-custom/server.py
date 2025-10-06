"""
OAuth 2.0 認可サーバー + リソースサーバー

MCP の OAuth 実装を見据えたシンプルな実装例
"""

from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
from typing import Optional
from datetime import datetime, timedelta

from storage import storage

app = FastAPI(title="OAuth 2.0 Server")
security = HTTPBearer()


# ===== 認可サーバーのエンドポイント =====

@app.get("/authorize")
async def authorize(
    response_type: str,
    client_id: str,
    redirect_uri: str,
    state: Optional[str] = None,
    scope: Optional[str] = None,
):
    """
    認可エンドポイント
    クライアントからのリクエストを受け取り、ユーザーにログイン・同意画面を表示
    """
    # クライアントIDの検証
    if client_id not in storage.clients:
        raise HTTPException(status_code=400, detail="Invalid client_id")

    # redirect_uriの検証
    if redirect_uri not in storage.clients[client_id]["redirect_uris"]:
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")

    # response_typeの検証（認可コードフローのみサポート）
    if response_type != "code":
        raise HTTPException(status_code=400, detail="Unsupported response_type")

    # ログイン・同意画面を表示（簡易実装）
    html_content = f"""
    <html>
        <head><title>OAuth 2.0 Authorization</title></head>
        <body>
            <h2>ログイン</h2>
            <form method="post" action="/authorize/consent">
                <input type="hidden" name="client_id" value="{client_id}">
                <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                <input type="hidden" name="state" value="{state or ''}">
                <input type="hidden" name="scope" value="{scope or ''}">
                <div>
                    <label>Username: <input type="text" name="username" value="demo-user"></label>
                </div>
                <div>
                    <label>Password: <input type="password" name="password" value="demo-password"></label>
                </div>
                <div style="margin-top: 20px;">
                    <p>クライアント「{client_id}」が以下の権限を要求しています：</p>
                    <p><strong>{scope or 'read'}</strong></p>
                </div>
                <button type="submit">許可する</button>
            </form>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/authorize/consent")
async def authorize_consent(
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    state: str = Form(""),
    scope: str = Form(""),
):
    """
    ユーザーの同意処理
    ログイン情報を検証し、認可コードを発行してクライアントにリダイレクト
    """
    # ユーザー認証
    user = storage.users.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 認可コードを生成
    auth_code = secrets.token_urlsafe(32)
    storage.auth_codes[auth_code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "username": username,
        "scope": scope,
        "expires_at": datetime.now() + timedelta(minutes=10),
    }

    # クライアントにリダイレクト
    redirect_url = f"{redirect_uri}?code={auth_code}"
    if state:
        redirect_url += f"&state={state}"

    return RedirectResponse(url=redirect_url, status_code=302)


@app.post("/token")
async def token(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None),
    client_secret: Optional[str] = Form(None),
):
    """
    トークンエンドポイント
    認可コードをアクセストークンに交換
    """
    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="Unsupported grant_type")

    # クライアント認証
    client = storage.clients.get(client_id)
    if not client or client["client_secret"] != client_secret:
        raise HTTPException(status_code=401, detail="Invalid client credentials")

    # 認可コードの検証
    auth_code_data = storage.auth_codes.get(code)
    if not auth_code_data:
        raise HTTPException(status_code=400, detail="Invalid authorization code")

    # 有効期限チェック
    if datetime.now() > auth_code_data["expires_at"]:
        del storage.auth_codes[code]
        raise HTTPException(status_code=400, detail="Authorization code expired")

    # クライアントIDとredirect_uriの一致を確認
    if (auth_code_data["client_id"] != client_id or
        auth_code_data["redirect_uri"] != redirect_uri):
        raise HTTPException(status_code=400, detail="Invalid request")

    # アクセストークンを生成
    access_token = secrets.token_urlsafe(32)
    storage.access_tokens[access_token] = {
        "username": auth_code_data["username"],
        "client_id": client_id,
        "scope": auth_code_data["scope"],
        "expires_at": datetime.now() + timedelta(hours=1),
    }

    # 認可コードを削除（使い捨て）
    del storage.auth_codes[code]

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": auth_code_data["scope"],
    }


# ===== リソースサーバーのエンドポイント =====

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    アクセストークンを検証する依存関数
    """
    token = credentials.credentials
    token_data = storage.access_tokens.get(token)

    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid access token")

    # 有効期限チェック
    if datetime.now() > token_data["expires_at"]:
        del storage.access_tokens[token]
        raise HTTPException(status_code=401, detail="Access token expired")

    return token_data


@app.get("/api/me")
async def get_user_info(token_data: dict = Depends(verify_token)):
    """
    保護されたAPIエンドポイント
    アクセストークンで認証されたユーザー情報を返す
    """
    username = token_data["username"]
    user = storage.users.get(username)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "username": username,
        "name": user["name"],
        "email": user["email"],
    }


@app.get("/api/profile")
async def get_user_profile(token_data: dict = Depends(verify_token)):
    """
    ユーザープロフィール取得
    """
    username = token_data["username"]
    user = storage.users.get(username)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "username": username,
        "name": user["name"],
        "email": user["email"],
        "bio": user.get("bio", ""),
        "location": user.get("location", ""),
    }


@app.get("/api/posts")
async def get_user_posts(token_data: dict = Depends(verify_token)):
    """
    ユーザーの投稿一覧を取得
    """
    username = token_data["username"]
    posts = storage.posts.get(username, [])

    return {
        "username": username,
        "posts": posts,
        "total": len(posts),
    }


@app.get("/")
async def root():
    """
    ルートエンドポイント（サーバー情報）
    """
    return {
        "message": "OAuth 2.0 Authorization Server",
        "endpoints": {
            "authorize": "/authorize",
            "token": "/token",
            "user_info": "/api/me",
            "user_profile": "/api/profile",
            "user_posts": "/api/posts",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
