"""
OAuth 2.0 認可サーバー + リソースサーバー (Flask版)

Flask による自前実装
"""

from flask import Flask, request, render_template_string, redirect, jsonify
import secrets
from typing import Optional
from datetime import datetime, timedelta
from functools import wraps

from storage import storage

app = Flask(__name__)


# ===== トークン検証デコレータ =====

def require_oauth(f):
    """Bearer トークンで保護"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({"error": "No authorization header"}), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != 'Bearer':
            return jsonify({"error": "Invalid authorization header"}), 401

        token = parts[1]
        token_data = storage.access_tokens.get(token)

        if not token_data:
            return jsonify({"error": "Invalid token"}), 401

        # 期限切れチェック
        if datetime.now() > token_data["expires_at"]:
            return jsonify({"error": "Token expired"}), 401

        # token_data を関数に渡す
        return f(token_data, *args, **kwargs)

    return decorated_function


# ===== 認可サーバーのエンドポイント =====

@app.route("/authorize")
def authorize():
    """
    認可エンドポイント
    クライアントからのリクエストを受け取り、ユーザーにログイン・同意画面を表示
    """
    response_type = request.args.get('response_type')
    client_id = request.args.get('client_id')
    redirect_uri = request.args.get('redirect_uri')
    state = request.args.get('state', '')
    scope = request.args.get('scope', '')

    # クライアントIDの検証
    if client_id not in storage.clients:
        return "Invalid client_id", 400

    # redirect_uriの検証
    if redirect_uri not in storage.clients[client_id]["redirect_uris"]:
        return "Invalid redirect_uri", 400

    # response_typeの検証（認可コードフローのみサポート）
    if response_type != "code":
        return "Unsupported response_type", 400

    # ログイン・同意画面を表示（簡易実装）
    html = f"""
    <html>
        <head><title>OAuth 2.0 Authorization (Flask)</title></head>
        <body>
            <h2>ログイン (Flask版)</h2>
            <form method="post" action="/authorize/consent">
                <input type="hidden" name="client_id" value="{client_id}">
                <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                <input type="hidden" name="response_type" value="{response_type}">
                <input type="hidden" name="state" value="{state}">
                <input type="hidden" name="scope" value="{scope}">

                <p>クライアント: Demo Client</p>
                <p>スコープ: {scope}</p>

                <label>ユーザー名: </label>
                <input type="text" name="username" value="demo-user" required>
                <br><br>

                <label>パスワード: </label>
                <input type="password" name="password" value="demo-password" required>
                <br><br>

                <button type="submit">許可する</button>
            </form>
        </body>
    </html>
    """

    return render_template_string(html)


@app.route("/authorize/consent", methods=['POST'])
def authorize_consent():
    """
    ユーザー認証 + 認可コード発行
    """
    client_id = request.form.get('client_id')
    redirect_uri = request.form.get('redirect_uri')
    response_type = request.form.get('response_type')
    username = request.form.get('username')
    password = request.form.get('password')
    state = request.form.get('state', '')
    scope = request.form.get('scope', '')

    # ユーザー認証
    user = storage.users.get(username)
    if not user or user["password"] != password:
        return "Invalid credentials", 401

    # 認可コード生成
    code = secrets.token_urlsafe(32)

    # 認可コードを保存
    storage.auth_codes[code] = {
        "code": code,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "username": username,
        "expires_at": datetime.now() + timedelta(minutes=10),
    }

    # クライアントにリダイレクト
    redirect_url = f"{redirect_uri}?code={code}"
    if state:
        redirect_url += f"&state={state}"

    return redirect(redirect_url, code=302)


@app.route("/token", methods=['POST'])
def token():
    """
    トークンエンドポイント
    認可コードをアクセストークンと交換
    """
    grant_type = request.form.get('grant_type')
    code = request.form.get('code')
    redirect_uri = request.form.get('redirect_uri')
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')

    # grant_type の検証
    if grant_type != "authorization_code":
        return jsonify({"error": "unsupported_grant_type"}), 400

    # クライアント認証
    client = storage.clients.get(client_id)
    if not client or client["client_secret"] != client_secret:
        return jsonify({"error": "invalid_client"}), 401

    # 認可コード検証
    auth_code_data = storage.auth_codes.get(code)
    if not auth_code_data:
        return jsonify({"error": "invalid_grant"}), 400

    # 期限切れチェック
    if datetime.now() > auth_code_data["expires_at"]:
        return jsonify({"error": "invalid_grant"}), 400

    # redirect_uri の検証
    if auth_code_data["redirect_uri"] != redirect_uri:
        return jsonify({"error": "invalid_grant"}), 400

    # クライアントID の検証
    if auth_code_data["client_id"] != client_id:
        return jsonify({"error": "invalid_grant"}), 400

    # アクセストークン生成
    access_token = secrets.token_urlsafe(32)

    storage.access_tokens[access_token] = {
        "access_token": access_token,
        "token_type": "Bearer",
        "scope": auth_code_data["scope"],
        "expires_at": datetime.now() + timedelta(hours=1),
        "username": auth_code_data["username"],
        "client_id": client_id,
    }

    # 認可コード削除（使い捨て）
    del storage.auth_codes[code]

    # トークンレスポンス
    return jsonify({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": auth_code_data["scope"],
    })


# ===== リソースサーバーのエンドポイント（保護されたAPI） =====

@app.route("/api/me")
@require_oauth
def get_user_info(token_data):
    """ユーザー情報取得API"""
    username = token_data["username"]
    user = storage.users.get(username)

    return jsonify({
        "username": username,
        "name": user["name"],
        "email": user["email"],
    })


@app.route("/api/profile")
@require_oauth
def get_user_profile(token_data):
    """
    ユーザープロフィール取得API
    Bearer トークンで保護された詳細情報
    """
    username = token_data["username"]
    user = storage.users.get(username)

    return jsonify({
        "username": username,
        "name": user["name"],
        "email": user["email"],
        "bio": user["bio"],
        "location": user["location"],
    })


@app.route("/api/posts")
@require_oauth
def get_user_posts(token_data):
    """
    ユーザーの投稿一覧取得API
    Bearer トークンで保護されたリソース
    """
    username = token_data["username"]
    posts = storage.posts.get(username, [])

    return jsonify({
        "username": username,
        "posts": posts,
    })


# ===== サーバー情報 =====

@app.route("/")
def root():
    """サーバー情報"""
    return jsonify({
        "name": "OAuth 2.0 Authorization Server (Flask)",
        "version": "1.0.0",
        "implementation": "Flask (custom)",
        "endpoints": {
            "authorization": "http://localhost:5000/authorize",
            "token": "http://localhost:5000/token",
            "userinfo": "http://localhost:5000/api/me",
        },
        "supported_grant_types": ["authorization_code"],
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
