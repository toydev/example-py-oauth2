# OAuth 2.0/2.1 実装サンプル

OAuth 2.0/2.1 認可コードフローの実装例

## 構成

```
/
  ESSENTIALS.md        OAuth 2.0 の設計思想と本質

  flask-custom/        Flask 自前実装
  flask-authlib/       Flask + Authlib
  fastapi-custom/      FastAPI 自前実装
  mcp-oauth-hello/     MCP + OAuth 2.1（PKCE対応）
```

## 実行方法

### Python実装（flask-custom/flask-authlib/fastapi-custom）

**サーバー起動:**
```bash
# いずれか1つを選択
cd flask-custom && python server.py
cd flask-authlib && python server.py
cd fastapi-custom && python server.py
```

**クライアント起動（別ターミナル）:**
```bash
# サーバーと同じディレクトリのクライアントを起動
cd flask-custom && python client.py
cd flask-authlib && python client.py
cd fastapi-custom && python client.py
```

ブラウザで http://localhost:5001 にアクセス

### MCP実装（mcp-oauth-hello）

**サーバー起動:**
```bash
cd mcp-oauth-hello && npm run http
```

詳細は [mcp-oauth-hello/README.md](./mcp-oauth-hello/README.md) を参照

## デモ用クレデンシャル（Python実装）

すべてのPython実装で共通：

- **Client ID**: `demo-client-id`
- **Client Secret**: `demo-client-secret`
- **Username**: `demo-user`
- **Password**: `demo-password`

## ポート番号

| 実装 | ポート |
|---|---|
| Python実装（サーバー） | 5000 |
| Python実装（クライアント） | 5001 |
| MCP実装 | 3000 |

## 実装の特徴

| 実装 | 特徴 |
|---|---|
| **flask-custom** | シンプルな自前実装、内部動作が明確 |
| **flask-authlib** | Authlib 使用、RFC 準拠、本番向け |
| **fastapi-custom** | async/await 対応、型ヒント、MCP 統合向け |
| **mcp-oauth-hello** | MCP SDK、OAuth 2.1（PKCE必須）、HTTP/stdio両対応、単一ポート設計 |

## 参考

詳細は [ESSENTIALS.md](./ESSENTIALS.md) を参照
