/**
 * MCP OAuth Hello World - HTTP Server
 *
 * ChatGPT Connectors用のHTTPサーバー
 * - MCP Server (HTTP transport)
 * - OAuth 2.1 Authorization Server (Dynamic Client Registration対応)
 * - Protected API (OAuth保護されたリソース)
 */

import express from 'express';
import apiRoutes from './api/routes';
import { handleMCPRequest } from './mcp/server';
import { mcpAuthRouter, getOAuthProtectedResourceMetadataUrl } from '@modelcontextprotocol/sdk/server/auth/router.js';
import { requireBearerAuth } from '@modelcontextprotocol/sdk/server/auth/middleware/bearerAuth.js';
import { SimpleOAuthProvider } from './oauth/provider';
import { InMemoryClientsStore } from './oauth/clients';
import { requestContext } from './mcp/context';

const app = express();
const PORT = process.env.PORT || 3000;
const BASE_URL = `http://localhost:${PORT}`;

// OAuth Provider初期化
const clientsStore = new InMemoryClientsStore();
const oauthProvider = new SimpleOAuthProvider();
oauthProvider.clientsStore = clientsStore;

// Middleware
app.use(express.json());

// OAuth 2.1 認可サーバー (MCP SDK標準機能)
// /.well-known/oauth-authorization-server にメタデータを公開
// /oauth/authorize, /oauth/token, /oauth/register などのエンドポイントを提供
app.use(mcpAuthRouter({
  provider: oauthProvider,
  issuerUrl: new URL(BASE_URL),
  scopesSupported: ['read', 'write']
}));

// Health check
app.get('/', (req, res) => {
  res.json({
    name: 'MCP OAuth Hello World',
    version: '1.0.0',
    endpoints: {
      mcp: '/mcp',
      oauth: {
        metadata: '/.well-known/oauth-authorization-server',
        authorize: '/oauth/authorize',
        token: '/oauth/token',
        register: '/oauth/register'
      },
      api: {
        me: '/api/me',
        posts: '/api/posts',
        profile: '/api/profile'
      }
    }
  });
});

// Protected API (ESSENTIALS.mdベース)
app.use('/api', apiRoutes);

// MCP Server (OAuth保護)
// ESSENTIALS.md: MCPサーバー自体もOAuthで保護されたリソース
const mcpUrl = new URL('/mcp', BASE_URL);
const resourceMetadataUrl = getOAuthProtectedResourceMetadataUrl(mcpUrl);

app.post('/mcp',
  requireBearerAuth({
    verifier: oauthProvider,
    resourceMetadataUrl
  }),
  async (req, res) => {
    try {
      // トークンを取得してコンテキストに設定
      const token = req.headers.authorization?.replace('Bearer ', '');

      if (!token) {
        res.status(401).json({ error: 'No token provided' });
        return;
      }

      // トークンをコンテキストに設定してリクエスト処理
      await requestContext.run({ token }, async () => {
        await handleMCPRequest(req, res);
      });
    } catch (error) {
      console.error('MCP Error:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  }
);

app.listen(PORT, () => {
  console.log(`🚀 MCP OAuth Hello World running on http://localhost:${PORT}`);
  console.log(`📖 Endpoints: http://localhost:${PORT}/`);
});
