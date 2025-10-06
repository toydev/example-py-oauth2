/**
 * MCP OAuth Hello World
 *
 * 1つのExpressサーバーで以下を統合:
 * - MCP Server (ChatGPT Connectorsからの接続)
 * - OAuth 2.1 Authorization Server (Dynamic Client Registration対応)
 * - Protected API (OAuth保護されたリソース)
 */

import express from 'express';

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());

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
        posts: '/api/posts'
      }
    }
  });
});

// TODO: OAuth認可サーバーの実装
// TODO: MCP Serverの実装
// TODO: 保護されたAPIの実装

app.listen(PORT, () => {
  console.log(`🚀 MCP OAuth Hello World running on http://localhost:${PORT}`);
  console.log(`📖 Endpoints: http://localhost:${PORT}/`);
});
