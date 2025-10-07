/**
 * MCP Tools
 *
 * 外部APIにアクセスするツール群
 * 開発用トークンで認証（後でOAuth認可サーバーと統合）
 */

import { z } from 'zod';

// 開発用トークン（後でOAuthトークンに置き換え）
const DEV_TOKEN = 'dev-token-12345';
const API_BASE = process.env.API_BASE || 'http://localhost:3000';

/**
 * 外部APIへのHTTPリクエスト
 */
async function callAPI(endpoint: string): Promise<any> {
  const url = `${API_BASE}${endpoint}`;

  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${DEV_TOKEN}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`API Error: ${error.error} - ${error.error_description}`);
  }

  return response.json();
}

/**
 * ツール定義
 */
export const tools = [
  {
    name: 'get_user_info',
    description: 'Get current user information from the external API',
    inputSchema: z.object({}),
    handler: async () => {
      const data = await callAPI('/api/me');
      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify(data, null, 2)
          }
        ]
      };
    }
  },
  {
    name: 'get_posts',
    description: 'Get user posts from the external API',
    inputSchema: z.object({}),
    handler: async () => {
      const data = await callAPI('/api/posts');
      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify(data, null, 2)
          }
        ]
      };
    }
  },
  {
    name: 'get_profile',
    description: 'Get user profile with statistics from the external API',
    inputSchema: z.object({}),
    handler: async () => {
      const data = await callAPI('/api/profile');
      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify(data, null, 2)
          }
        ]
      };
    }
  }
];
