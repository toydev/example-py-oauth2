/**
 * MCP Tools
 *
 * 外部APIにアクセスするツール群
 * OAuthトークンで認証
 */

import { z } from 'zod';
import { callAPI } from '../client/apiClient.js';

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
