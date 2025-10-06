# Flask + Authlib 実装サンプル

Flask + Authlib による OAuth 2.0 認可コードフローの実装です。

**これが Authlib の本命！Flask との統合が完璧です。**

## 特徴

- **Flask + Authlib**: 最も成熟した組み合わせ
- **完璧な統合**: Authlib が Flask を第一優先でサポート
- **自動化**: トークン管理が自動化

## 実行方法

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. サーバー起動

```bash
python server.py
```

http://localhost:5000 で起動

### 3. クライアント起動（別ターミナル）

```bash
python client.py
```

http://localhost:5001 で起動

### 4. ブラウザでアクセス

1. http://localhost:5001 にアクセス
2. 「ログイン」をクリック
3. ログイン（demo-user / demo-password）
4. ダッシュボードで API 呼び出し

## 自前実装との比較

### サーバー側：トークンエンドポイント

**自前実装：**
```python
@app.route("/token", methods=['POST'])
def token():
    grant_type = request.form.get('grant_type')
    code = request.form.get('code')
    # ... 手動で全部処理（40行）
    return jsonify({...})
```

**Authlib 実装：**
```python
@app.route("/token", methods=['POST'])
def issue_token():
    return authorization.create_token_response()
    # ↑ これだけ（1行）
```

### サーバー側：トークン検証

**自前実装：**
```python
def require_oauth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        # ... 手動で検証（15行）
        return f(token_data, *args, **kwargs)
    return decorated_function
```

**Authlib 実装：**
```python
@app.route("/api/me")
@require_oauth()  # ← デコレータ1つ
def get_user_info():
    token = current_token  # ← 自動的に取得
    return jsonify({...})
```

### クライアント側：認可URL生成

**自前実装：**
```python
@app.route("/login")
def login():
    state = secrets.token_urlsafe(16)
    # 手動でURL構築
    auth_url = (
        f"{OAUTH_CONFIG['authorization_endpoint']}"
        f"?response_type=code"
        f"&client_id={OAUTH_CONFIG['client_id']}"
        f"&redirect_uri={OAUTH_CONFIG['redirect_uri']}"
        f"&state={state}"
        f"&scope=read"
    )
    return redirect(auth_url)
```

**Authlib 実装：**
```python
@app.route("/login")
def login():
    state = secrets.token_urlsafe(16)
    # Authlib が自動生成
    client = get_oauth_client()
    authorization_url, _ = client.create_authorization_url(
        OAUTH_CONFIG["authorization_endpoint"],
        state=state,
        scope="read",
    )
    return redirect(authorization_url)
```

### クライアント側：トークン取得

**自前実装：**
```python
@app.route("/callback")
def callback():
    # 手動でPOSTリクエスト
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
    token_data = response.json()
    # ...
```

**Authlib 実装：**
```python
@app.route("/callback")
def callback():
    # Authlib が自動処理
    client = get_oauth_client()
    token = client.fetch_token(
        url=OAUTH_CONFIG["token_endpoint"],
        authorization_response=request.url,
    )
    # token に全部入ってる
```

### クライアント側：API呼び出し

**自前実装：**
```python
@app.route("/api/call/<endpoint>")
def call_api(endpoint):
    access_token = session.get("access_token")
    # 手動でヘッダー付与
    response = requests.get(
        f"{OAUTH_CONFIG['api_base']}/{endpoint}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    return jsonify(response.json())
```

**Authlib 実装：**
```python
@app.route("/api/call/<endpoint>")
def call_api(endpoint):
    token = session.get("token")
    client = get_oauth_client(token=token)
    # Authlib が自動的にヘッダー付与
    response = client.get(f"{OAUTH_CONFIG['api_base']}/{endpoint}")
    return jsonify(response.json())
```

## Authlib の優位性

### Flask との統合が完璧

```python
# Flask 専用のインテグレーション
from authlib.integrations.flask_oauth2 import AuthorizationServer
from authlib.integrations.flask_oauth2 import ResourceProtector
from authlib.integrations.flask_oauth2 import current_token

# Flask のリクエストオブジェクトを直接理解
authorization = AuthorizationServer()
authorization.init_app(app, query_client=..., save_token=...)
```

### 自動化される処理

**サーバー側：**
- ✅ トークンエンドポイントの処理
- ✅ クライアント認証
- ✅ 認可コード検証
- ✅ トークン生成
- ✅ エラーレスポンス（RFC準拠）

**クライアント側：**
- ✅ 認可URLの生成
- ✅ トークン取得リクエスト
- ✅ Authorization ヘッダーの自動付与
- ✅ トークンリフレッシュ（refresh_token がある場合）

## FastAPI + Authlib との違い

| | Flask + Authlib | FastAPI + Authlib |
|---|---|---|
| **統合の完成度** | ★★★★★ | ★★☆☆☆ |
| **ドキュメント** | 豊富 | 少ない |
| **使いやすさ** | 簡単 | 複雑 |
| **本番採用** | 実績多数 | まだ少ない |

**結論：**
- Authlib を使うなら Flask が最適
- FastAPI は Authlib 統合が未熟
- 本番環境なら Flask + Authlib 推奨

## デモ用クレデンシャル

- Client ID: `demo-client-id`
- Client Secret: `demo-client-secret`
- Username: `demo-user`
- Password: `demo-password`
