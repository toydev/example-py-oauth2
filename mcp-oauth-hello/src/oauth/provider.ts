/**
 * OAuth 2.1 Provider実装
 *
 * MCP SDKのDemoInMemoryAuthProviderを参考にした実装
 * ESSENTIALS.mdで学んだOAuth 2.1の本質を反映
 */

import { OAuthServerProvider, AuthorizationParams } from '@modelcontextprotocol/sdk/server/auth/provider.js';
import { OAuthClientInformationFull, OAuthTokens } from '@modelcontextprotocol/sdk/shared/auth.js';
import { AuthInfo } from '@modelcontextprotocol/sdk/server/auth/types.js';
import { OAuthRegisteredClientsStore } from '@modelcontextprotocol/sdk/server/auth/clients.js';
import { Response } from 'express';
import crypto from 'crypto';
import { accessTokens } from '../api/storage';

interface AuthorizationCode {
  code: string;
  clientId: string;
  userId: string;
  expiresAt: Date;
  scope: string;
}

interface StoredToken {
  accessToken: string;
  refreshToken?: string;
  userId: string;
  clientId: string;
  expiresAt: Date;
  scope: string;
}

/**
 * OAuth Provider実装
 *
 * 認可コードフローとトークン管理を提供
 */
export class SimpleOAuthProvider implements OAuthServerProvider {
  clientsStore!: OAuthRegisteredClientsStore;
  private codes: Map<string, AuthorizationCode> = new Map();
  private tokens: Map<string, StoredToken> = new Map();

  /**
   * 認可エンドポイント
   *
   * ユーザー同意を取得し、認可コードを発行
   * ESSENTIALS.md: ブラウザでの認可フロー
   */
  async authorize(
    client: OAuthClientInformationFull,
    params: AuthorizationParams,
    res: Response
  ): Promise<void> {
    // 認可コード生成
    const code = crypto.randomBytes(32).toString('hex');

    // デモ用: 自動承認（本番環境では同意画面を表示）
    const userId = 'user-1';
    const scope = params.scope || 'read';

    // 認可コード保存（短命）
    this.codes.set(code, {
      code,
      clientId: client.client_id,
      userId,
      expiresAt: new Date(Date.now() + 5 * 60 * 1000), // 5分
      scope
    });

    // リダイレクトURIに認可コードを付けて返す
    const redirectUrl = new URL(params.redirect_uri);
    redirectUrl.searchParams.set('code', code);
    if (params.state) {
      redirectUrl.searchParams.set('state', params.state);
    }

    res.redirect(redirectUrl.toString());
  }

  /**
   * 認可コード検証（PKCE用）
   */
  async challengeForAuthorizationCode(
    client: OAuthClientInformationFull,
    authorizationCode: string
  ): Promise<string> {
    const code = this.codes.get(authorizationCode);

    if (!code || code.clientId !== client.client_id) {
      throw new Error('Invalid authorization code');
    }

    if (code.expiresAt < new Date()) {
      this.codes.delete(authorizationCode);
      throw new Error('Authorization code expired');
    }

    // デモ用: PKCEチャレンジを返す（本番環境では保存済みのチャレンジを返す）
    return '';
  }

  /**
   * 認可コード → アクセストークン交換
   *
   * ESSENTIALS.md: クライアントがトークンエンドポイントで認可コードを交換
   */
  async exchangeAuthorizationCode(
    client: OAuthClientInformationFull,
    authorizationCode: string,
    _codeVerifier?: string
  ): Promise<OAuthTokens> {
    const code = this.codes.get(authorizationCode);

    if (!code || code.clientId !== client.client_id) {
      throw new Error('Invalid authorization code');
    }

    if (code.expiresAt < new Date()) {
      this.codes.delete(authorizationCode);
      throw new Error('Authorization code expired');
    }

    // 認可コードは一度だけ使用可能
    this.codes.delete(authorizationCode);

    // アクセストークンとリフレッシュトークン生成
    const accessToken = crypto.randomBytes(32).toString('hex');
    const refreshToken = crypto.randomBytes(32).toString('hex');

    // トークン保存
    this.tokens.set(accessToken, {
      accessToken,
      refreshToken,
      userId: code.userId,
      clientId: code.clientId,
      expiresAt: new Date(Date.now() + 3600 * 1000), // 1時間
      scope: code.scope
    });

    return {
      access_token: accessToken,
      token_type: 'Bearer',
      expires_in: 3600,
      refresh_token: refreshToken,
      scope: code.scope
    };
  }

  /**
   * リフレッシュトークン → 新しいアクセストークン
   *
   * ESSENTIALS.md: アクセストークンの有効期限が切れた際の更新
   */
  async exchangeRefreshToken(
    client: OAuthClientInformationFull,
    refreshToken: string,
    _scopes?: string[],
    _resource?: URL
  ): Promise<OAuthTokens> {
    // 既存トークンを検索
    const existingToken = Array.from(this.tokens.values()).find(
      t => t.refreshToken === refreshToken && t.clientId === client.client_id
    );

    if (!existingToken) {
      throw new Error('Invalid refresh token');
    }

    // 新しいアクセストークン生成
    const accessToken = crypto.randomBytes(32).toString('hex');

    // 古いトークン削除
    this.tokens.delete(existingToken.accessToken);

    // 新しいトークン保存
    this.tokens.set(accessToken, {
      accessToken,
      refreshToken,
      userId: existingToken.userId,
      clientId: existingToken.clientId,
      expiresAt: new Date(Date.now() + 3600 * 1000),
      scope: existingToken.scope
    });

    return {
      access_token: accessToken,
      token_type: 'Bearer',
      expires_in: 3600,
      refresh_token: refreshToken,
      scope: existingToken.scope
    };
  }

  /**
   * アクセストークン検証
   *
   * ESSENTIALS.md: リソースサーバーでのトークン検証
   * APIストレージと共有してトークンを検証
   */
  async verifyAccessToken(token: string): Promise<AuthInfo> {
    // まずOAuthで発行されたトークンをチェック
    const oauthToken = this.tokens.get(token);
    if (oauthToken) {
      if (oauthToken.expiresAt < new Date()) {
        this.tokens.delete(token);
        throw new Error('Access token expired');
      }
      return {
        token,
        clientId: oauthToken.clientId,
        scopes: oauthToken.scope.split(' '),
        expiresAt: Math.floor(oauthToken.expiresAt.getTime() / 1000),
        extra: { sub: oauthToken.userId }
      };
    }

    // 次に開発用トークン（APIストレージ）をチェック
    const apiToken = accessTokens.get(token);
    if (apiToken) {
      if (apiToken.expiresAt < new Date()) {
        accessTokens.delete(token);
        throw new Error('Access token expired');
      }
      return {
        token,
        clientId: 'dev-client',
        scopes: apiToken.scope.split(' '),
        expiresAt: Math.floor(apiToken.expiresAt.getTime() / 1000),
        extra: { sub: apiToken.userId }
      };
    }

    throw new Error('Invalid access token');
  }
}
