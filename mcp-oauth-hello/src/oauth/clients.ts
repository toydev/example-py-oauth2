/**
 * OAuthクライアント登録ストア
 *
 * Dynamic Client Registration (RFC 7591) のサポート
 */

import { OAuthRegisteredClientsStore } from '@modelcontextprotocol/sdk/server/auth/clients.js';
import { OAuthClientInformationFull } from '@modelcontextprotocol/sdk/shared/auth.js';
import crypto from 'crypto';

/**
 * インメモリクライアントストア
 *
 * 本番環境ではデータベースを使用
 */
export class InMemoryClientsStore implements OAuthRegisteredClientsStore {
  private clients: Map<string, OAuthClientInformationFull> = new Map();

  /**
   * クライアント取得
   */
  async getClient(clientId: string): Promise<OAuthClientInformationFull | undefined> {
    return this.clients.get(clientId);
  }

  /**
   * クライアント登録
   *
   * Dynamic Client Registration: クライアントが自動で登録できる
   */
  async registerClient(
    clientMetadata: OAuthClientInformationFull
  ): Promise<OAuthClientInformationFull> {
    const clientId = crypto.randomBytes(16).toString('hex');
    const clientSecret = crypto.randomBytes(32).toString('hex');

    const client: OAuthClientInformationFull = {
      ...clientMetadata,
      client_id: clientId,
      client_secret: clientSecret,
      client_id_issued_at: Math.floor(Date.now() / 1000),
      client_secret_expires_at: 0 // 無期限
    };

    this.clients.set(clientId, client);
    return client;
  }
}
