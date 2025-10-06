# OAuth 2.0 実装サンプル

OAuth 2.0 認可コードフローの3つの実装

## 構成

```
/
  ESSENTIALS.md        OAuth 2.0 の設計思想と本質

  flask-custom/        Flask 自前実装
  flask-authlib/       Flask + Authlib
  fastapi-custom/      FastAPI 自前実装
```

## 実行方法

### サーバー起動

```bash
# いずれか1つを選択
cd flask-custom && python server.py
cd flask-authlib && python server.py
cd fastapi-custom && python server.py
```

### クライアント起動（別ターミナル）

```bash
# サーバーと同じディレクトリのクライアントを起動
cd flask-custom && python client.py
cd flask-authlib && python client.py
cd fastapi-custom && python client.py
```

ブラウザで http://localhost:5001 にアクセス

## デモ用クレデンシャル

すべての実装で共通：

- **Client ID**: `demo-client-id`
- **Client Secret**: `demo-client-secret`
- **Username**: `demo-user`
- **Password**: `demo-password`

## ポート番号

すべての実装で統一：

- **サーバー**: 5000
- **クライアント**: 5001

## 実装の特徴

| 実装 | 特徴 |
|---|---|
| **flask-custom** | シンプルな自前実装、内部動作が明確 |
| **flask-authlib** | Authlib 使用、RFC 準拠、本番向け |
| **fastapi-custom** | async/await 対応、型ヒント、MCP 統合向け |

## 参考

詳細は [ESSENTIALS.md](./ESSENTIALS.md) を参照
