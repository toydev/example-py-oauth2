/**
 * MCP Server
 *
 * Model Context Protocol サーバー実装
 * ChatGPT Connectors から接続可能
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { Request, Response } from 'express';
import { tools } from './tools';

/**
 * MCPサーバーインスタンスを作成
 */
export function createMCPServer() {
  const server = new Server(
    {
      name: 'external-api-client',
      version: '1.0.0'
    },
    {
      capabilities: {
        tools: {}
      }
    }
  );

  // ツール一覧を返す
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: tools.map(tool => ({
        name: tool.name,
        description: tool.description,
        inputSchema: {
          type: 'object',
          properties: {},
          required: []
        },
        annotations: {
          readOnlyHint: true  // 読み取り専用ツールであることを明示
        }
      }))
    };
  });

  // ツール実行
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const tool = tools.find(t => t.name === request.params.name);

    if (!tool) {
      throw new Error(`Unknown tool: ${request.params.name}`);
    }

    try {
      return await tool.handler();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      return {
        content: [
          {
            type: 'text' as const,
            text: `Error: ${errorMessage}`
          }
        ],
        isError: true
      };
    }
  });

  return server;
}

/**
 * Express用MCPハンドラー
 */
export async function handleMCPRequest(req: Request, res: Response) {
  const server = createMCPServer();

  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
    enableJsonResponse: true
  });

  res.on('close', () => {
    transport.close();
  });

  await server.connect(transport);
  await transport.handleRequest(req, res, req.body);
}
