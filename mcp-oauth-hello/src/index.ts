/**
 * MCP OAuth Hello World
 *
 * 1つのExpressサーバーで以下を統合:
 * - MCP Server (ChatGPT Connectorsからの接続)
 * - OAuth 2.1 Authorization Server (Dynamic Client Registration対応)
 * - Protected API (OAuth保護されたリソース)
 */

import express from 'express';
import apiRoutes from './api/routes';
import { handleMCPRequest } from './mcp/server';

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
      api: {
        me: '/api/me',
        posts: '/api/posts'
      }
    }
  });
});

// Protected API (ESSENTIALS.mdベース)
app.use('/api', apiRoutes);

// MCP Server (公式SDK)
app.post('/mcp', async (req, res) => {
  try {
    await handleMCPRequest(req, res);
  } catch (error) {
    console.error('MCP Error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// TODO: OAuth認可サーバーの実装

app.listen(PORT, () => {
  console.log(`🚀 MCP OAuth Hello World running on http://localhost:${PORT}`);
  console.log(`📖 Endpoints: http://localhost:${PORT}/`);
});
