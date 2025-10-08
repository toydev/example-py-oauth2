# MCP OAuth Hello World

MCP (Model Context Protocol) + OAuth 2.1 Delegated Authorization の実装例

## 概要

OAuth 2.1で保護されたMCPサーバーを2つの方法で提供：

```
1. HTTP版 (Claude Code用 - OAuth認証あり)
   Claude Code → [OAuth Flow via Browser] → [MCP Server/HTTP + Protected API]

2. stdio版 (Claude Desktop/Claude Code用 - 開発用トークン)
   Claude Desktop/Code → [MCP Server/stdio] → [API_TOKEN] → [Protected API]
```

**特徴:**
- HTTP版：MCPサーバー自体がOAuth 2.1で保護されたリソース（ブラウザ認証フロー）
- stdio版：開発用トークンで簡易アクセス
- 認可サーバー、リソースサーバー、MCPサーバーを統合
- ESSENTIALS.mdで学んだOAuth 2.1の本質を反映した実装

## 実装状況

- ✅ **OAuth 2.1認可サーバー**: Authorization Code Grant + PKCE
- ✅ **MCP Server (HTTP版)**: Claude Code用（OAuth保護、ブラウザ認証フロー）
- ✅ **MCP Server (stdio版)**: Claude Desktop/Claude Code用（開発用トークン）
- ✅ **保護されたAPI**: Bearer トークン認証（`/api/me`, `/api/posts`, `/api/profile`）
- ✅ **Dynamic Client Registration**: RFC 7591準拠
- ✅ **OAuthメタデータ**: RFC 8414準拠（/.well-known/oauth-authorization-server）

## アーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│              MCP OAuth Hello World                  │
│                                                     │
│  ┌──────────────────┐  ┌─────────────────────────┐ │
│  │ OAuth 2.1 AS     │  │ MCP Server + RS         │ │
│  │                  │  │                         │ │
│  │ /oauth/authorize │  │ /mcp (OAuth protected)  │ │
│  │ /oauth/token     │  │ /api/* (OAuth protected)│ │
│  │ /oauth/register  │  │                         │ │
│  └──────────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────┘
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

### HTTP版（ChatGPT Connectors用）

```bash
# サーバー起動
npm run http

# 別ターミナルでngrokで公開
ngrok http 3000
```

エンドポイント一覧（http://localhost:3000/）:
```json
{
  "mcp": "/mcp",
  "oauth": {
    "metadata": "/.well-known/oauth-authorization-server",
    "authorize": "/oauth/authorize",
    "token": "/oauth/token",
    "register": "/oauth/register"
  },
  "api": {
    "me": "/api/me",
    "posts": "/api/posts",
    "profile": "/api/profile"
  }
}
```

### HTTP版（Claude Code用 - OAuth認証あり）

**HTTP版はMCPサーバー自体がOAuth保護されており、ブラウザでの認証フローが必要です。**

#### セットアップ手順

1. **HTTPサーバーを起動**
   ```bash
   npm run http
   ```

2. **MCP設定を追加**（`.mcp.json`）
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

3. **Claude Codeを再起動**

#### OAuthフロー

Claude CodeがHTTP版MCPサーバーに接続する際、MCP SDKの標準OAuth機能によってブラウザで認証フローが開始されます。

### stdio版（Claude Desktop/Claude Code用 - 開発用トークン）

**stdio版は開発用トークンで簡易アクセスします（OAuth認証なし）。**

#### セットアップ手順

1. **HTTPサーバーを起動**（別ターミナル - APIサーバーとして）
   ```bash
   npm run http
   ```

2. **MCP設定を追加**（`.mcp.json`）
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

3. **Claude Codeを再起動**

## MCPツール

すべて読み取り専用（`readOnlyHint: true`）：

| ツール名 | 説明 | パラメータ |
|---------|------|-----------|
| `get_demo_info` | デモユーザー情報取得 | なし |
| `get_demo_posts` | サンプル投稿一覧取得 | なし |
| `get_demo_profile` | サンプルプロフィール取得 | なし |

## OAuth 2.1フロー

### 開発用トークン

開発・テスト用に事前発行されたトークン：

```bash
# Bearer トークン: dev-token-12345
curl -H "Authorization: Bearer dev-token-12345" \
  http://localhost:3000/api/me
```

### Authorization Code Grant（実装済み）

1. **クライアント登録** (Dynamic Client Registration)
```bash
curl -X POST http://localhost:3000/oauth/register \
  -H "Content-Type: application/json" \
  -d '{"redirect_uris":["https://example.com/callback"]}'
```

2. **認可リクエスト**
```
GET /oauth/authorize?
  response_type=code&
  client_id={client_id}&
  redirect_uri={redirect_uri}&
  scope=read write&
  state={random_state}&
  code_challenge={pkce_challenge}&
  code_challenge_method=S256
```

3. **トークン取得**
```bash
curl -X POST http://localhost:3000/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code&code={code}&client_id={client_id}&client_secret={client_secret}&code_verifier={pkce_verifier}"
```

4. **リソースアクセス**
```bash
curl -H "Authorization: Bearer {access_token}" \
  http://localhost:3000/mcp
```

## 技術スタック

- **MCP SDK**: @modelcontextprotocol/sdk v1.0.4
  - MCPサーバー実装（HTTP + stdio）
  - OAuth 2.1認可サーバー（`mcpAuthRouter`）
  - Bearer認証ミドルウェア（`requireBearerAuth`）
- **Web**: Express + TypeScript
- **開発**: tsx (TypeScript実行)
- **デプロイ**: ngrok（開発用）

## 重要な知見

### ESSENTIALS.mdの本質を反映

OAuth 2.1の2つの根本課題を解決：
1. **パスワード保護問題** → Delegated Authorization
2. **ブラウザ露出問題** → Authorization Code Grant + PKCE

### MCPエンドポイントのOAuth保護

MCPサーバー自体を保護されたリソースとして扱う：

```typescript
app.post('/mcp',
  requireBearerAuth({
    verifier: oauthProvider,
    resourceMetadataUrl
  }),
  async (req, res) => {
    await handleMCPRequest(req, res);
  }
);
```

### ChatGPT Connectorsの安全性チェック

ChatGPTはツール説明を解析して安全性を判断：

- ❌ "user information", "external API" → 危険と判断
- ✅ "demo", "sample", "(test data only)" → 安全と判断

### readOnlyHintアノテーション

読み取り専用ツールは`readOnlyHint: true`を設定：

```typescript
{
  name: "get_demo_info",
  description: "Get demo account information (test data only)",
  annotations: {
    readOnlyHint: true
  }
}
```

## テスト

```bash
# OAuthメタデータ確認
curl http://localhost:3000/.well-known/oauth-authorization-server

# 認証なしアクセス（拒否される）
curl -X POST http://localhost:3000/mcp

# Bearer トークン付きアクセス（成功）
curl -X POST http://localhost:3000/mcp \
  -H "Authorization: Bearer dev-token-12345" \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'

# 保護されたAPI
curl -H "Authorization: Bearer dev-token-12345" \
  http://localhost:3000/api/profile
```

## 参考

- [ESSENTIALS.md](../ESSENTIALS.md) - OAuth 2.0の本質を学んだドキュメント
- [MCP Specification](https://modelcontextprotocol.io/)
- [OAuth 2.1 Draft](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-11)
- [RFC 7591 - Dynamic Client Registration](https://datatracker.ietf.org/doc/html/rfc7591)
- [RFC 8414 - OAuth 2.0 Authorization Server Metadata](https://datatracker.ietf.org/doc/html/rfc8414)

## ライセンス

MIT
