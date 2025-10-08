/**
 * OAuth Client Provider
 *
 * MCP SDKのOAuthClientProviderを実装
 * ユーザーによるブラウザでの認可フローをサポート
 */

import { OAuthClientProvider } from '@modelcontextprotocol/sdk/client/auth.js';
import { OAuthClientMetadata, OAuthClientInformation, OAuthTokens, OAuthClientInformationFull } from '@modelcontextprotocol/sdk/shared/auth.js';
import {
  saveTokens,
  loadTokens,
  saveClientInformation,
  loadClientInformation,
  saveCodeVerifier,
  loadCodeVerifier,
  clearCredentials
} from './tokenStorage.js';
import { startCallbackServer, stopCallbackServer } from './callbackServer.js';
import { openBrowser } from './browser.js';

const REDIRECT_PORT = 8080;
const REDIRECT_URL = `http://localhost:${REDIRECT_PORT}/callback`;

export class FileBasedOAuthClient implements OAuthClientProvider {
  get redirectUrl(): string {
    return REDIRECT_URL;
  }

  get clientMetadata(): OAuthClientMetadata {
    return {
      redirect_uris: [REDIRECT_URL],
      token_endpoint_auth_method: 'client_secret_post'
    };
  }

  async clientInformation(): Promise<OAuthClientInformation | undefined> {
    return await loadClientInformation();
  }

  async saveClientInformation(clientInformation: OAuthClientInformationFull): Promise<void> {
    await saveClientInformation(clientInformation);
  }

  async tokens(): Promise<OAuthTokens | undefined> {
    return await loadTokens();
  }

  async saveTokens(tokens: OAuthTokens): Promise<void> {
    await saveTokens(tokens);
    // トークン取得後、コールバックサーバーを停止
    stopCallbackServer();
  }

  async redirectToAuthorization(authorizationUrl: URL): Promise<void> {
    console.error('\n🔐 Authorization required!');
    console.error('📖 Opening browser to:', authorizationUrl.toString());
    console.error('⏳ Waiting for authorization...\n');

    // ブラウザを開く
    await openBrowser(authorizationUrl.toString());
  }

  async saveCodeVerifier(codeVerifier: string): Promise<void> {
    await saveCodeVerifier(codeVerifier);
  }

  async codeVerifier(): Promise<string> {
    return await loadCodeVerifier();
  }

  async invalidateCredentials(scope: 'all' | 'client' | 'tokens' | 'verifier'): Promise<void> {
    await clearCredentials(scope);
  }
}

/**
 * OAuth認可フローを開始
 *
 * コールバックサーバーを起動してから認可を開始
 */
export async function initializeOAuthFlow(): Promise<void> {
  console.error('🚀 Starting OAuth callback server...');
  await startCallbackServer(REDIRECT_PORT);
}
