# MCP OAuth Hello World

MCP (Model Context Protocol) + OAuth 2.1 Delegated Authorization の学習用実装

## 概要

```
ChatGPT Connectors → [MCPサーバー] → (OAuth) → [外部保護API]
                     ↑                           ↑
                   MCP + OAuth 2.1          ESSENTIALS.mdベース
                   DCR対応                  シンプルなAPI
```

## 構成

### 1つのExpressサーバー (port 3000)

- **MCP層**: ChatGPT ConnectorsからのMCP接続
  - Dynamic Client Registration (DCR)
  - OAuth 2.1認可フロー

- **外部API層**: OAuth保護されたシンプルなAPI
  - `/api/me` - ユーザー情報
  - `/api/posts` - 投稿一覧

## 技術スタック

- **MCP**: @modelcontextprotocol/sdk (公式TypeScript SDK)
- **OAuth 2.1**: node-oidc-provider (OpenID Certified)
- **Web**: Express + TypeScript
- **デプロイ**: ngrok (開発用)

## セットアップ

```bash
npm install
npm run dev
```

## 参考

- [ESSENTIALS.md](../ESSENTIALS.md) - OAuth 2.0の本質
- [MCP Specification](https://modelcontextprotocol.io/)
- [OAuth 2.1 Draft](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-11)
