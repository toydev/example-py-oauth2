# Flask 自前実装サンプル

Flask による OAuth 2.0 認可コードフローの完全な自前実装です。

## 特徴

- **Flask**: Python の定番 Web フレームワーク
- **自前実装**: OAuth ライブラリを使わず、仕様に従って実装
- **シンプル**: 学習・理解に最適

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

## FastAPI 版との違い

| | Flask | FastAPI |
|---|---|---|
| **構文** | デコレータベース | async/await |
| **型ヒント** | なし | 必須 |
| **自動ドキュメント** | なし | あり（Swagger） |
| **セッション管理** | Flask.session（組み込み）| Cookie（手動）|
| **ポート** | 5000/5001 | 8000/8001 |

**コード例：**

```python
# Flask
@app.route("/api/me")
@require_oauth
def get_user_info(token_data):
    return jsonify({...})

# FastAPI
@app.get("/api/me")
async def get_user_info(token_data: dict = Depends(require_oauth)):
    return {...}
```

## デモ用クレデンシャル

- Client ID: `demo-client-id`
- Client Secret: `demo-client-secret`
- Username: `demo-user`
- Password: `demo-password`
