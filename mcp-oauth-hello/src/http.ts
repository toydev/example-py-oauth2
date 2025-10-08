/**
 * MCP OAuth Hello World - HTTP Server
 *
 * ChatGPT Connectors用のHTTPサーバー
 * - MCP Server (HTTP transport)
 * - OAuth 2.1 Authorization Server (Dynamic Client Registration対応)
 * - Protected API (OAuth保護されたリソース)
 */

import express from 'express';
import { createApiRoutes } from './api/routes';
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

// ngrok などのプロキシ経由でアクセスされる場合に対応
app.set('trust proxy', true);

// /.well-known/oauth-authorization-server を動的に上書き
// IMPORTANT: mcpAuthRouter より前に定義する必要がある
app.get('/.well-known/oauth-authorization-server', (req, res) => {
  const protocol = req.get('x-forwarded-proto') || req.protocol;
  const host = req.get('x-forwarded-host') || req.get('host');
  const baseUrl = `${protocol}://${host}`;
  res.json({
    issuer: baseUrl + '/',
    authorization_endpoint: `${baseUrl}/authorize`,
    response_types_supported: ['code'],
    code_challenge_methods_supported: ['S256'],
    token_endpoint: `${baseUrl}/token`,
    token_endpoint_auth_methods_supported: ['client_secret_post'],
    grant_types_supported: ['authorization_code', 'refresh_token'],
    scopes_supported: ['read', 'write'],
    registration_endpoint: `${baseUrl}/register`
  });
});

// OAuth 2.1 認可サーバー
// mcpAuthRouter を使用してエンドポイント提供
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
app.use('/api', createApiRoutes(oauthProvider));

// MCP Server (OAuth保護)
// ESSENTIALS.md: MCPサーバー自体もOAuthで保護されたリソース
const mcpUrl = new URL('/mcp', BASE_URL);
const resourceMetadataUrl = getOAuthProtectedResourceMetadataUrl(mcpUrl);

// OAuth Protected Resource Metadata for /mcp (RFC 9728)
app.get('/.well-known/oauth-protected-resource/mcp', (req, res) => {
  const protocol = req.get('x-forwarded-proto') || req.protocol;
  const host = req.get('x-forwarded-host') || req.get('host');
  const baseUrl = `${protocol}://${host}`;
  res.json({
    resource: `${baseUrl}/mcp`,
    authorization_servers: [baseUrl + '/'],
    scopes_supported: ['read', 'write']
  });
});

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
