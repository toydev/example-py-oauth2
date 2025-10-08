# MCP OAuth Hello World

MCP (Model Context Protocol) + OAuth 2.1 Delegated Authorization の学習用実装

## 概要

MCPサーバーを2つの方法で提供：

```
1. HTTP版 (ChatGPT Connectors用)
   ChatGPT Connectors → [MCP Server/HTTP] → (OAuth) → [外部保護API]

2. stdio版 (Claude Desktop/Claude Code用)
   Claude Desktop → [MCP Server/stdio] → (OAuth) → [外部保護API]
```

## 現在の実装状況

- ✅ **外部保護API**: Bearer トークン認証（`/api/me`, `/api/posts`, `/api/profile`）
- ✅ **MCP Server**: HTTP版（ChatGPT Connectors用）
- ✅ **MCP Server**: stdio版（Claude Desktop/Claude Code用）
- ✅ **ChatGPT Connectors**: 接続確認済み（安全性チェック通過）
- ⏳ **OAuth 2.1認可サーバー**: 未実装（開発用トークン使用中）

## ファイル構成

```
src/
  http.ts              # HTTP版エントリポイント（ChatGPT Connectors用）
  stdio.ts             # stdio版エントリポイント（Claude Desktop/Claude Code用）
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

# ngrokで公開
ngrok http 3000

# ChatGPT Connectorsに登録
# URL: https://xxxx.ngrok-free.app
# 認証: なし
```

### stdio版（Claude Desktop/Claude Code用）

```bash
# MCP設定ファイルに追加
# ~/.claude/mcp.json または Claude Code設定

{
  "mcpServers": {
    "external-api-client": {
      "command": "node",
      "args": ["/path/to/mcp-oauth-hello/dist/stdio.js"]
    }
  }
}

# または開発時は
{
  "mcpServers": {
    "external-api-client": {
      "command": "npm",
      "args": ["run", "mcp"],
      "cwd": "/path/to/mcp-oauth-hello"
    }
  }
}
```

## MCPツール

すべて読み取り専用（`readOnlyHint: true`）：

- **get_demo_info**: デモユーザー情報取得
- **get_demo_posts**: サンプル投稿一覧取得
- **get_demo_profile**: サンプルプロフィール取得

## 技術スタック

- **MCP**: @modelcontextprotocol/sdk (公式TypeScript SDK)
- **OAuth 2.1**: node-oidc-provider (OpenID Certified) - 未実装
- **Web**: Express + TypeScript
- **デプロイ**: ngrok (開発用)

## 重要な知見

### ChatGPT Connectorsの安全性チェック

ChatGPTはAIでツール説明を解析して安全性を判断：

- ❌ "user information", "external API" → 危険と判断
- ✅ "demo", "sample", "(test data only)" → 安全と判断

### readOnlyHintアノテーション

読み取り専用ツールは`readOnlyHint: true`を設定することで、Claude/ChatGPTが適切に認識します。

## 次のステップ

1. ⏳ Claude Desktop/Claude Codeでの動作確認
2. ⏳ OAuth 2.1認可サーバー実装（オプション）
3. ⏳ Dynamic Client Registration (DCR)実装

## 参考

- [ESSENTIALS.md](../ESSENTIALS.md) - OAuth 2.0の本質
- [MCP Specification](https://modelcontextprotocol.io/)
- [OAuth 2.1 Draft](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-11)
