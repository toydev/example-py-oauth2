/**
 * MCP Tools
 *
 * 外部APIにアクセスするツール群
 * OAuthトークンで認証
 */

import { z } from 'zod';
import { getToken } from './context.js';

const API_BASE = process.env.API_BASE || 'http://localhost:3000';

/**
 * 外部APIへのHTTPリクエスト
 */
async function callAPI(endpoint: string): Promise<any> {
  const token = getToken(); // コンテキストまたは環境変数から取得
  const url = `${API_BASE}${endpoint}`;

  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    const errorObj = error as { error: string; error_description?: string };
    throw new Error(`API Error: ${errorObj.error} - ${errorObj.error_description || ''}`);
  }

  return response.json();
}

/**
 * ツール定義
 */
export const tools = [
  {
    name: 'get_demo_info',
    description: 'Get demo account information (test data only)',
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
    name: 'get_demo_posts',
    description: 'Get sample posts (test data only)',
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
    name: 'get_demo_profile',
    description: 'Get sample profile with statistics (test data only)',
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
