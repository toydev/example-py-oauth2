# OAuth 2.0 自前実装サンプル

FastAPI による OAuth 2.0 認可コードフローの完全な自前実装です。

## 構成

- **server.py**: 認可サーバー + リソースサーバー（ポート8000）
- **client.py**: OAuthクライアント（ポート8001）
- **requirements.txt**: 依存関係

## セットアップ

```bash
# 依存関係のインストール
pip install -r requirements.txt
```

## 実行方法

### 1. 認可サーバーを起動

```bash
python server.py
```

起動後、http://localhost:8000 でサーバー情報を確認できます。

### 2. クライアントアプリを起動（別のターミナル）

```bash
python client.py
```

### 3. ブラウザでアクセス

1. http://localhost:8001 にアクセス
2. 「ログイン」ボタンをクリック
3. 認可サーバーでログイン（demo-user / demo-password）
4. ダッシュボードで継続的にAPIを呼び出し

## OAuth 2.0 認可コードフロー

```
1. ユーザー
   ↓ ログインボタンクリック
2. クライアント (localhost:8001)
   ↓ 認可リクエスト（GETリダイレクト）
3. 認可サーバー (localhost:8000/authorize)
   ↓ ログイン・同意画面表示
4. ユーザー
   ↓ ログイン情報入力・許可
5. 認可サーバー
   ↓ 認可コード発行（リダイレクト）
6. クライアント (localhost:8001/callback)
   ↓ トークンリクエスト（POST）
7. 認可サーバー (localhost:8000/token)
   ↓ アクセストークン発行
8. クライアント
   ↓ アクセストークンでAPI呼び出し
9. リソースサーバー (localhost:8000/api/me)
   ↓ 保護されたリソースを返す
10. クライアント
    ↓ ユーザー情報を画面表示
```

## エンドポイント

### 認可サーバー（localhost:8000）

**OAuth 2.0 エンドポイント：**
- `GET /authorize`: 認可エンドポイント
- `POST /authorize/consent`: 同意処理
- `POST /token`: トークンエンドポイント

**保護されたAPI：**
- `GET /api/me`: ユーザー情報
- `GET /api/profile`: ユーザープロフィール（詳細情報）
- `GET /api/posts`: ユーザーの投稿一覧

### クライアント（localhost:8001）

- `GET /`: ホーム画面（未ログイン時）
- `GET /login`: 認可フロー開始
- `GET /callback`: 認可サーバーからのコールバック
- `GET /dashboard`: ダッシュボード（ログイン後）
- `GET /api/call/{endpoint}`: APIプロキシ（継続的なAPI呼び出し）
- `GET /logout`: ログアウト

## 継続的なAPI呼び出し

このサンプルでは、**OAuth認証後にアクセストークンを使って何度でもAPIを呼び出せる**実装になっています。

### 仕組み

1. **セッション管理**：
   - `itsdangerous` で署名付きCookieを使用
   - セッションIDとアクセストークンを紐付け
   - Cookie有効期限: 1時間

2. **ダッシュボード**：
   - ログイン後、`/dashboard` にリダイレクト
   - ボタンをクリックするだけでAPIを呼び出し
   - JavaScriptでFetch APIを使用

3. **APIプロキシ**：
   - クライアントの `/api/call/{endpoint}` がプロキシとして動作
   - セッションからアクセストークンを取得
   - サーバーの `/api/{endpoint}` にリクエスト転送

### 実際のフロー

```
ログイン → Cookie設定 → ダッシュボード
                             ↓
                        ボタンクリック
                             ↓
                    /api/call/posts
                             ↓
                    Cookieからトークン取得
                             ↓
                    /api/posts へリクエスト
                             ↓
                    レスポンスを表示
```

ページをリロードしても**セッションが維持される**ため、何度でもAPIを呼び出せます。

## デモ用クレデンシャル

### OAuth クライアント

- Client ID: `demo-client-id`
- Client Secret: `demo-client-secret`
- Redirect URI: `http://localhost:8001/callback`

### ユーザー

- Username: `demo-user`
- Password: `demo-password`
