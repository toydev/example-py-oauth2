#!/usr/bin/env node
/**
 * MCP OAuth Hello World - stdio Server
 *
 * Claude Desktop/Claude Code 用のエントリポイント
 * 標準入出力でMCPプロトコル通信
 */

import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { createMCPServer } from './mcp/server.js';

async function main() {
  const server = createMCPServer();
  const transport = new StdioServerTransport();

  await server.connect(transport);

  // stderrに出力（stdioはstdin/stdoutを使うため）
  console.error('MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
