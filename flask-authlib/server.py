"""
OAuth 2.0 認可サーバー + リソースサーバー (Flask + Authlib版)

Authlib を使用した実装（モジュール分割版）
"""

from flask import Flask, request, render_template_string, jsonify, redirect
from authlib.integrations.flask_oauth2 import AuthorizationServer, ResourceProtector
from authlib.integrations.flask_oauth2 import current_token
import secrets
from datetime import datetime, timedelta

from models import Token, AuthorizationCode
from storage import storage
from grants import AuthorizationCodeGrant, MyBearerTokenValidator

app = Flask(__name__)
app.secret_key = "flask-authlib-server-secret-key-change-in-production"


# ===== Authlib の設定 =====

def query_client(client_id):
    """クライアント情報を取得（Authlib が呼び出す）"""
    return storage.clients.get(client_id)


def save_token(token, request):
    """トークンを保存（Authlib が呼び出す）"""
    # request.user は authenticate_user の戻り値
    user = request.user
    access_token_str = token["access_token"]

    token_obj = Token(
        access_token=access_token_str,
        token_type=token["token_type"],
        scope=token.get("scope", ""),
        expires_at=datetime.now() + timedelta(seconds=token["expires_in"]),
        client_id=request.client_id,
        username=user["username"],
    )
    storage.access_tokens[access_token_str] = token_obj


# AuthorizationServer のインスタンス作成
authorization = AuthorizationServer()
authorization.init_app(app, query_client=query_client, save_token=save_token)
authorization.register_grant(AuthorizationCodeGrant)

# ResourceProtector のインスタンス作成
require_oauth = ResourceProtector()
require_oauth.register_token_validator(MyBearerTokenValidator())


# ===== 認可サーバーのエンドポイント =====

@app.route("/authorize", methods=['GET', 'POST'])
def authorize_route():
    """
    認可エンドポイント
    GETでログイン画面、POSTで認可コード発行
    """
    if request.method == 'GET':
        # ログイン・同意画面を表示
        response_type = request.args.get('response_type')
        client_id = request.args.get('client_id')
        redirect_uri = request.args.get('redirect_uri')
        state = request.args.get('state', '')
        scope = request.args.get('scope', '')

        # クライアントIDの検証
        client = storage.clients.get(client_id)
        if not client:
            return "Invalid client_id", 400

        # redirect_uriの検証
        if redirect_uri not in client.redirect_uris:
            return "Invalid redirect_uri", 400

        html = f"""
        <html>
            <head><title>OAuth 2.0 Authorization (Flask + Authlib)</title></head>
            <body>
                <h2>ログイン (Flask + Authlib版)</h2>
                <form method="post" action="/authorize">
                    <input type="hidden" name="response_type" value="{response_type}">
                    <input type="hidden" name="client_id" value="{client_id}">
                    <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                    <input type="hidden" name="state" value="{state}">
                    <input type="hidden" name="scope" value="{scope}">

                    <p>クライアント: {client.client_name}</p>
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

    # POST - ユーザー認証 + 認可コード発行
    username = request.form.get('username')
    password = request.form.get('password')

    # ユーザー認証
    user = storage.users.get(username)
    if not user or user["password"] != password:
        return "Invalid credentials", 401

    # 認可コード生成
    code = secrets.token_urlsafe(32)

    # 認可コードを保存
    auth_code = AuthorizationCode(
        code=code,
        client_id=request.form.get('client_id'),
        redirect_uri=request.form.get('redirect_uri'),
        scope=request.form.get('scope', ''),
        username=username,
        expires_at=datetime.now() + timedelta(minutes=10),
    )
    storage.auth_codes[code] = auth_code

    # クライアントにリダイレクト
    redirect_uri = request.form.get('redirect_uri')
    state = request.form.get('state', '')

    redirect_url = f"{redirect_uri}?code={code}"
    if state:
        redirect_url += f"&state={state}"

    return redirect(redirect_url, code=302)


@app.route("/token", methods=['POST'])
def issue_token():
    """
    トークンエンドポイント（Authlib が処理）
    認可コードをアクセストークンと交換
    """
    return authorization.create_token_response()


# ===== リソースサーバーのエンドポイント（保護されたAPI） =====

@app.route("/api/me")
@require_oauth()
def get_user_info():
    """ユーザー情報取得API（Authlib が自動でトークン検証）"""
    token = current_token
    username = token.username
    user = storage.users.get(username)

    return jsonify({
        "username": username,
        "name": user["name"],
        "email": user["email"],
    })


@app.route("/api/profile")
@require_oauth()
def get_user_profile():
    """
    ユーザープロフィール取得API
    Bearer トークンで保護された詳細情報
    """
    token = current_token
    username = token.username
    user = storage.users.get(username)

    return jsonify({
        "username": username,
        "name": user["name"],
        "email": user["email"],
        "bio": user["bio"],
        "location": user["location"],
    })


@app.route("/api/posts")
@require_oauth()
def get_user_posts():
    """
    ユーザーの投稿一覧取得API
    Bearer トークンで保護されたリソース
    """
    token = current_token
    username = token.username
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
        "name": "OAuth 2.0 Authorization Server (Flask + Authlib)",
        "version": "1.0.0",
        "implementation": "Authlib",
        "endpoints": {
            "authorization": "http://localhost:5000/authorize",
            "token": "http://localhost:5000/token",
            "userinfo": "http://localhost:5000/api/me",
        },
        "supported_grant_types": ["authorization_code"],
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
