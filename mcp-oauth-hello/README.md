# MCP OAuth Hello World

MCP (Model Context Protocol) + OAuth 2.1 Delegated Authorization の実装例

## 概要

認可サーバー、リソースサーバー、MCPサーバーを単一ポートで提供するサンプル実装。

**提供内容:**
- **認可サーバー**: OAuth 2.1（PKCE対応）
- **リソースサーバー**: 保護されたAPI（`/api/me`, `/api/posts`, `/api/profile`）
- **MCPサーバー**: 2つの接続方式（HTTP/stdio）

**設計:**
- 単一ポート（`:3000`）で全サーバーを統合
- 理由：ngrok無料版（1ポートのみ）でChatGPT Connectorsから試せるように

**MCP接続方式:**

```
1. HTTP版
   MCPクライアント → [ブラウザ認証] → [MCPサーバー/HTTP]
   （localhost または ngrok経由）

2. stdio版
   MCPクライアント → [環境変数トークン] → [MCPサーバー/stdio]
   （localhost のみ）
```

**特徴:**
- HTTP版：OAuth 2.1ブラウザ認証（外部公開可能）
- stdio版：事前定義トークン（ローカル専用）

## アーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│              MCP OAuth Hello World                  │
│                                                     │
│  ┌──────────────────┐  ┌─────────────────────────┐  │
│  │ OAuth 2.1 AS     │  │ MCP Server + RS         │  │
│  │                  │  │                         │  │
│  │ /oauth/authorize │  │ /mcp (OAuth protected)  │  │
│  │ /oauth/token     │  │ /api/* (OAuth protected)│  │
│  │ /oauth/register  │  │                         │  │
│  └──────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## トークン管理

### 2種類のトークン

| 種別 | 発行方法 | 用途 | 有効期限 |
|------|---------|------|---------|
| **事前定義トークン** | サーバー起動時に生成<br>`dev-token-12345` | stdio版、curlテスト | 1時間 |
| **OAuthトークン** | ブラウザ認証フロー<br>（PKCE） | HTTP版 | 1時間 |

両方同時に有効。

**stdio版で事前定義トークンを使う理由:**
- stdio版はツール呼び出しごとにプロセス起動→終了（メモリ揮発）
- OAuthトークンを永続化するにはファイル保存が必要
- 複雑化を避け、環境変数で渡すシンプルな方式を採用

**トークン検証:**
- 認可サーバー（OAuth Provider）で一元管理
- リソースサーバーは`verifyAccessToken()`を呼び出してトークン検証
- OAuthトークンと事前定義トークンの両方に対応

```bash
# 事前定義トークンでAPIアクセス
curl -H "Authorization: Bearer dev-token-12345" \
  http://localhost:3000/api/me
```

## ファイル構成

```
src/
  http.ts              # HTTP版エントリポイント（OAuth + MCP + API統合）
  stdio.ts             # stdio版エントリポイント（Claude Desktop/Code用）
  oauth/
    provider.ts        # OAuth 2.1 Provider（認可コード・トークン管理）
    clients.ts         # Dynamic Client Registration
  mcp/
    server.ts          # MCP共通ロジック
    tools.ts           # ツール定義（3つの読み取り専用ツール）
    context.ts         # リクエストコンテキスト（トークン管理）
  api/
    routes.ts          # 保護API実装
    middleware.ts      # Bearer認証
    storage.ts         # データストレージ
```

## セットアップ

```bash
npm install
```

## 使い方

### HTTP版

```bash
npm run http
```

**.mcp.json:**
```json
{
  "mcpServers": {
    "external-api-client": {
      "type": "http",
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

Claude Code再起動後、ブラウザで自動的にOAuth認証が開始されます。

**外部公開（ngrok）:**
```bash
ngrok http 3000
# → https://xxxx.ngrok.io/mcp
```

### stdio版

```bash
npm run http  # 別ターミナルでAPIサーバーとして起動
```

**.mcp.json:**
```json
{
  "mcpServers": {
    "external-api-client": {
      "type": "stdio",
      "command": "npx",
      "args": ["tsx", "src/stdio.ts"],
      "env": {
        "API_TOKEN": "dev-token-12345"
      }
    }
  }
}
```

Claude Code再起動で利用可能。

## MCPツール

すべて読み取り専用（`readOnlyHint: true`）：

| ツール名 | 説明 | パラメータ |
|---------|------|-----------|
| `get_demo_info` | デモユーザー情報取得 | なし |
| `get_demo_posts` | サンプル投稿一覧取得 | なし |
| `get_demo_profile` | サンプルプロフィール取得 | なし |

## OAuth 2.1実装

### PKCE

OAuth 2.1必須セキュリティ機能。認可コード傍受攻撃を防止：

1. 認可時：`code_challenge`送信
2. トークン交換時：`code_verifier`送信
3. 検証：`SHA256(code_verifier) == code_challenge`

### フロー

1. クライアント登録（Dynamic Client Registration / RFC 7591）
2. 認可リクエスト（`code_challenge`含む）
3. ユーザー認証・同意
4. 認可コード発行
5. トークン交換（`code_verifier`で検証）
6. アクセストークン発行

## 技術スタック

- MCP SDK v1.0.4（MCPサーバー、OAuth 2.1認可サーバー）
- Express + TypeScript
- tsx（TypeScript実行）
- ngrok（外部公開）

## 設計ポイント

### OAuth 2.1の本質

2つの根本課題を解決：
1. パスワード保護問題 → Delegated Authorization
2. ブラウザ露出問題 → Authorization Code Grant + PKCE

### MCPサーバーの保護

MCPエンドポイント自体をOAuth保護されたリソースとして実装。

### ツール安全性

- `readOnlyHint: true`で読み取り専用を明示
- ツール説明に`(test data only)`を含めて安全性を示す

## 参考

- [ESSENTIALS.md](../ESSENTIALS.md) - OAuth 2.0の本質を学んだドキュメント
- [MCP Specification](https://modelcontextprotocol.io/)
- [OAuth 2.1 Draft](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-11)
- [RFC 7591 - Dynamic Client Registration](https://datatracker.ietf.org/doc/html/rfc7591)
- [RFC 8414 - OAuth 2.0 Authorization Server Metadata](https://datatracker.ietf.org/doc/html/rfc8414)

## ライセンス

MIT
