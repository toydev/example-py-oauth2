"""
OAuth 2.0 クライアントアプリケーション (Flask + Authlib版)

Authlib を使用した実装
認可コードフローを使用してアクセストークンを取得し、
保護されたAPIに継続的にアクセスする
"""

from flask import Flask, request, session, render_template_string, redirect, jsonify
from authlib.integrations.requests_client import OAuth2Session
import secrets

app = Flask(__name__)
app.secret_key = "flask-authlib-secret-key-change-in-production"

# OAuth 2.0設定
OAUTH_CONFIG = {
    "client_id": "demo-client-id",
    "client_secret": "demo-client-secret",
    "authorization_endpoint": "http://localhost:5000/authorize",
    "token_endpoint": "http://localhost:5000/token",
    "redirect_uri": "http://localhost:5001/callback",
    "api_base": "http://localhost:5000/api",
}


def get_oauth_client(token=None):
    """OAuth2Session インスタンスを作成"""
    return OAuth2Session(
        client_id=OAUTH_CONFIG["client_id"],
        client_secret=OAUTH_CONFIG["client_secret"],
        redirect_uri=OAUTH_CONFIG["redirect_uri"],
        token=token,
    )


@app.route("/")
def home():
    """
    ホーム画面
    """
    token = session.get("token")

    if token:
        # ログイン済み - ダッシュボードにリダイレクト
        return redirect("/dashboard")

    # 未ログイン - ログイン画面を表示
    html = """
    <html>
        <head><title>OAuth 2.0 Client Demo (Flask + Authlib)</title></head>
        <body>
            <h1>OAuth 2.0 クライアントデモ (Flask + Authlib版)</h1>
            <p>このアプリは OAuth 2.0 認可コードフローのデモです（Authlib使用）</p>
            <h2>ステップ：</h2>
            <ol>
                <li><a href="/login">ログイン</a> をクリック</li>
                <li>認可サーバーでログイン・同意</li>
                <li>コールバックでアクセストークン取得（Authlib が自動処理）</li>
                <li>ダッシュボードで継続的にAPIを呼び出し（Authlib が自動でヘッダー付与）</li>
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
    return render_template_string(html)


@app.route("/login")
def login():
    """
    認可フローの開始（Authlib 使用）
    ユーザーを認可サーバーにリダイレクト
    """
    # 古いセッションデータをクリア
    session.clear()

    # CSRF対策用のstateパラメータを生成
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state

    # Authlib で認可リクエストのURLを構築
    client = get_oauth_client()
    authorization_url, _ = client.create_authorization_url(
        OAUTH_CONFIG["authorization_endpoint"],
        state=state,
        scope="read",
    )

    return redirect(authorization_url)


@app.route("/callback")
def callback():
    """
    認可サーバーからのコールバック（Authlib 使用）
    認可コードを受け取り、アクセストークンに交換
    """
    state = request.args.get('state')
    saved_state = session.get('oauth_state')

    print(f"[CALLBACK] Received state: {state}")
    print(f"[CALLBACK] Saved state: {saved_state}")
    print(f"[CALLBACK] Session: {dict(session)}")

    # stateの検証（CSRF対策）
    if not state or state != saved_state:
        return f"""<h1>Error: Invalid state parameter</h1>
        <p>Received: {state}</p>
        <p>Saved: {saved_state}</p>
        <p><a href="/logout">ログアウトしてリトライ</a></p>""", 400

    # Authlib でトークンエンドポイントにリクエスト
    client = get_oauth_client()
    try:
        token = client.fetch_token(
            url=OAUTH_CONFIG["token_endpoint"],
            authorization_response=request.url,
        )
        print(f"[CALLBACK] Token received: {token}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"<h1>Error fetching token: {str(e)}</h1>", 400

    # セッションにトークンデータを保存
    try:
        session['token'] = token
        print(f"[CALLBACK] Token saved to session")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"<h1>Error saving token: {str(e)}</h1>", 400

    # ダッシュボードにリダイレクト
    return redirect("/dashboard")


@app.route("/dashboard")
def dashboard():
    """
    ダッシュボード画面
    ログイン後、継続的にAPIを呼び出せる
    """
    token = session.get("token")

    if not token:
        # 未ログイン - ホームにリダイレクト
        return redirect("/")

    access_token = token.get("access_token", "")

    html = f"""
    <html>
        <head>
            <title>Dashboard - OAuth 2.0 Client (Flask + Authlib)</title>
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
                <h1>ダッシュボード (Flask + Authlib版)</h1>

                <div class="section">
                    <h2>認証情報</h2>
                    <p><strong>アクセストークン:</strong> <code>{access_token[:20]}...{access_token[-20:]}</code></p>
                    <p><strong>トークンタイプ:</strong> {token.get('token_type', 'Bearer')}</p>
                    <p><strong>有効期限:</strong> {token.get('expires_in', 3600)}秒</p>
                    <a href="/logout" class="button logout">ログアウト</a>
                </div>

                <div class="section">
                    <h2>保護されたAPIを呼び出す</h2>
                    <p>以下のボタンをクリックして、アクセストークンを使ってAPIを呼び出します：</p>
                    <p><small>※ Authlib が自動的に Authorization ヘッダーを付与します</small></p>
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
    return render_template_string(html)


@app.route("/api/call/<endpoint>")
def call_api(endpoint):
    """
    保護されたAPIを呼び出す（Authlib が自動でヘッダー付与）
    """
    token = session.get("token")

    if not token:
        return jsonify({"error": "Not authenticated"}), 401

    # Authlib の OAuth2Session を使ってAPIを呼び出し
    client = get_oauth_client(token=token)

    # Authlib が自動的に Authorization ヘッダーを付与
    response = client.get(f"{OAUTH_CONFIG['api_base']}/{endpoint}")

    if response.status_code != 200:
        return jsonify({"error": response.text, "status_code": response.status_code})

    return jsonify(response.json())


@app.route("/logout")
def logout():
    """
    ログアウト
    """
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
