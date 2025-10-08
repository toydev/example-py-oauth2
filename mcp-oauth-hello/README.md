# MCP OAuth Hello World

MCP (Model Context Protocol) + OAuth 2.1 Delegated Authorization の実装例

## 概要

OAuth 2.1で保護されたMCPサーバーを2つの方法で提供：

```
1. HTTP版 (ChatGPT Connectors用)
   ChatGPT → [OAuth Flow] → [MCP Server/HTTP + Protected API]

2. stdio版 (Claude Desktop/Claude Code用)
   Claude Desktop/Code → [MCP Server/stdio] → [OAuth Token] → [Protected API]
```

**特徴:**
- MCPサーバー自体がOAuth 2.1で保護されたリソース
- 認可サーバー、リソースサーバー、MCPサーバーを統合
- ESSENTIALS.mdで学んだOAuth 2.1の本質を反映した実装

## 実装状況

- ✅ **OAuth 2.1認可サーバー**: Authorization Code Grant + PKCE
- ✅ **MCP Server (HTTP版)**: ChatGPT Connectors用（OAuth保護）
- ✅ **MCP Server (stdio版)**: Claude Desktop/Claude Code用
- ✅ **OAuth Client**: stdio版MCPツールからのブラウザ認可フロー
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
  client/
    apiClient.ts       # OAuthクライアント（完全なOAuthフロー実装）
    tokenStorage.ts    # トークン永続化（ファイルシステム）
    callbackServer.ts  # OAuthコールバックサーバー（認可コード受信）
    browser.ts         # ブラウザ起動ユーティリティ
    oauthClient.ts     # OAuthClientProvider実装
  mcp/
    server.ts          # MCP共通ロジック
    tools.ts           # ツール定義（3つの読み取り専用ツール）
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

### stdio版（Claude Desktop/Claude Code用）

**重要**: stdio版では、MCPツールが保護されたAPIにアクセスする際に、自動的にOAuthフローを開始します。

#### セットアップ手順

1. **HTTP版サーバーを起動**（別ターミナル）
   ```bash
   cd mcp-oauth-hello
   npm run http
   ```

2. **MCP設定を追加**

   プロジェクトルートの`.mcp.json.example`を参照：
   ```json
   {
     "mcpServers": {
       "external-api-client": {
         "type": "stdio",
         "command": "npx",
         "args": ["tsx", "mcp-oauth-hello/src/stdio.ts"],
         "env": {}
       }
     }
   }
   ```

3. **Claude Codeで使用**
   ```bash
   # プロジェクトルートに.mcp.jsonを配置
   cp .mcp.json.example .mcp.json

   # Claude Codeを再起動
   ```

#### OAuthフロー（初回のみ）

1. Claude Codeで `get_demo_info` などのツールを呼び出す
2. トークンがない場合、自動的にブラウザが開く
3. ブラウザで認可を承認
4. トークンが `~/.mcp-oauth-hello/tokens.json` に保存される
5. 以降は保存されたトークンを使用（認可不要）

トークンをクリアして再認可する場合：
```bash
rm -rf ~/.mcp-oauth-hello
```

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
