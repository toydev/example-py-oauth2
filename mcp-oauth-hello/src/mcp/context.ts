/**
 * MCP Request Context
 *
 * AsyncLocalStorageを使ってリクエストスコープでトークンを管理
 */

import { AsyncLocalStorage } from 'async_hooks';

interface RequestContext {
  token: string;
}

export const requestContext = new AsyncLocalStorage<RequestContext>();

/**
 * トークンを取得
 *
 * HTTP版: リクエストコンテキストから取得
 * stdio版: 環境変数から取得
 */
export function getToken(): string {
  // HTTP版: リクエストコンテキストからトークン取得
  const context = requestContext.getStore();
  if (context?.token) {
    return context.token;
  }

  // stdio版: 環境変数からトークン取得
  const envToken = process.env.API_TOKEN || process.env.EXTERNAL_API_TOKEN;
  if (envToken) {
    return envToken;
  }

  throw new Error(
    'No API token available. ' +
    'For stdio: Set API_TOKEN environment variable. ' +
    'For HTTP: Ensure Authorization header is present.'
  );
}
