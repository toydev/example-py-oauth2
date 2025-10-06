"""
OAuth 2.0 クライアントアプリケーション (Flask版)

Flask による自前実装
認可コードフローを使用してアクセストークンを取得し、
保護されたAPIに継続的にアクセスする
"""

from flask import Flask, request, session, render_template_string, redirect, jsonify
import requests
import secrets

app = Flask(__name__)
app.secret_key = "flask-custom-client-secret-key-change-in-production"

# OAuth 2.0設定
OAUTH_CONFIG = {
    "client_id": "demo-client-id",
    "client_secret": "demo-client-secret",
    "authorization_endpoint": "http://localhost:5000/authorize",
    "token_endpoint": "http://localhost:5000/token",
    "redirect_uri": "http://localhost:5001/callback",
    "api_base": "http://localhost:5000/api",
}


@app.route("/")
def home():
    """
    ホーム画面
    """
    access_token = session.get("access_token")

    if access_token:
        # ログイン済み - ダッシュボードにリダイレクト
        return redirect("/dashboard")

    # 未ログイン - ログイン画面を表示
    html = """
    <html>
        <head><title>OAuth 2.0 Client Demo (Flask)</title></head>
        <body>
            <h1>OAuth 2.0 クライアントデモ (Flask版)</h1>
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
    return render_template_string(html)


@app.route("/login")
def login():
    """
    認可フローの開始
    ユーザーを認可サーバーにリダイレクト
    """
    # 古いセッションデータをクリア
    session.clear()

    # CSRF対策用のstateパラメータを生成
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state

    # 認可リクエストのURLを構築
    auth_url = (
        f"{OAUTH_CONFIG['authorization_endpoint']}"
        f"?response_type=code"
        f"&client_id={OAUTH_CONFIG['client_id']}"
        f"&redirect_uri={OAUTH_CONFIG['redirect_uri']}"
        f"&state={state}"
        f"&scope=read"
    )

    return redirect(auth_url)


@app.route("/callback")
def callback():
    """
    認可サーバーからのコールバック
    認可コードを受け取り、アクセストークンに交換
    """
    code = request.args.get('code')
    state = request.args.get('state')

    # stateの検証（CSRF対策）
    if not state or state != session.get('oauth_state'):
        return "<h1>Error: Invalid state parameter</h1>", 400

    # トークンエンドポイントにリクエスト
    response = requests.post(
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
        return f"<h1>Error: {response.text}</h1>", 400

    token_data = response.json()
    access_token = token_data["access_token"]

    # セッションにアクセストークンを保存
    session['access_token'] = access_token
    session['token_data'] = token_data

    # ダッシュボードにリダイレクト
    return redirect("/dashboard")


@app.route("/dashboard")
def dashboard():
    """
    ダッシュボード画面
    ログイン後、継続的にAPIを呼び出せる
    """
    access_token = session.get("access_token")

    if not access_token:
        # 未ログイン - ホームにリダイレクト
        return redirect("/")

    # セッション情報を取得
    token_data = session.get("token_data", {})

    html = f"""
    <html>
        <head>
            <title>Dashboard - OAuth 2.0 Client (Flask)</title>
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
                <h1>ダッシュボード (Flask版)</h1>

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
    return render_template_string(html)


@app.route("/api/call/<endpoint>")
def call_api(endpoint):
    """
    保護されたAPIを呼び出す
    """
    access_token = session.get("access_token")

    if not access_token:
        return jsonify({"error": "Not authenticated"}), 401

    # APIを呼び出し
    response = requests.get(
        f"{OAUTH_CONFIG['api_base']}/{endpoint}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

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
