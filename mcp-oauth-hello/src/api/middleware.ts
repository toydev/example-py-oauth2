/**
 * 認証ミドルウェア
 *
 * Bearer トークンを検証し、リクエストにユーザー情報を追加
 * ESSENTIALS.mdのアクセストークン検証部分を実装
 */

import { Request, Response, NextFunction } from 'express';
import { validateToken } from './storage';

// Expressのリクエストに型を追加
declare global {
  namespace Express {
    interface Request {
      userId?: string;
      scope?: string;
    }
  }
}

/**
 * Bearer トークン検証ミドルウェア
 *
 * Authorization: Bearer {token} ヘッダーを検証
 */
export function requireAuth(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization;

  if (!authHeader) {
    return res.status(401).json({
      error: 'unauthorized',
      error_description: 'Missing Authorization header'
    });
  }

  // "Bearer {token}" 形式をパース
  const parts = authHeader.split(' ');
  if (parts.length !== 2 || parts[0] !== 'Bearer') {
    return res.status(401).json({
      error: 'invalid_token',
      error_description: 'Invalid Authorization header format. Expected: Bearer {token}'
    });
  }

  const token = parts[1];
  const accessToken = validateToken(token);

  if (!accessToken) {
    return res.status(401).json({
      error: 'invalid_token',
      error_description: 'Token is invalid or expired'
    });
  }

  // リクエストにユーザー情報を追加
  req.userId = accessToken.userId;
  req.scope = accessToken.scope;

  next();
}

/**
 * スコープチェックミドルウェア
 *
 * 特定のスコープを持っているかチェック
 */
export function requireScope(requiredScope: string) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.scope) {
      return res.status(403).json({
        error: 'insufficient_scope',
        error_description: 'No scope found'
      });
    }

    const scopes = req.scope.split(' ');
    if (!scopes.includes(requiredScope)) {
      return res.status(403).json({
        error: 'insufficient_scope',
        error_description: `Required scope: ${requiredScope}`
      });
    }

    next();
  };
}
