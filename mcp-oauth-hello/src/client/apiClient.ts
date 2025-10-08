/**
 * OAuth API Client
 *
 * OAuthトークンを使った外部API呼び出し
 * トークンがない場合は認可フローを開始
 */

import crypto from 'crypto';
import { loadTokens, saveTokens, loadClientInformation, saveClientInformation, saveCodeVerifier, loadCodeVerifier } from './tokenStorage.js';
import { initializeOAuthFlow } from './oauthClient.js';
import { waitForAuthorizationCode } from './callbackServer.js';
import { openBrowser } from './browser.js';

const API_BASE = process.env.API_BASE || 'http://localhost:3000';
const REDIRECT_URI = 'http://localhost:8080/callback';

// OAuth認可フロー実行中フラグ
let authFlowInProgress = false;

/**
 * OAuthメタデータを取得
 */
async function getOAuthMetadata(): Promise<any> {
  const url = `${API_BASE}/.well-known/oauth-authorization-server`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch OAuth metadata');
  }
  return response.json();
}

/**
 * Dynamic Client Registration
 */
async function registerClient(metadata: any): Promise<any> {
  const response = await fetch(metadata.registration_endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      redirect_uris: [REDIRECT_URI],
      token_endpoint_auth_method: 'client_secret_post'
    })
  });

  if (!response.ok) {
    throw new Error('Failed to register client');
  }

  return response.json();
}

/**
 * PKCEチャレンジを生成
 */
function generatePKCE(): { verifier: string; challenge: string } {
  const verifier = crypto.randomBytes(32).toString('base64url');
  const challenge = crypto
    .createHash('sha256')
    .update(verifier)
    .digest('base64url');

  return { verifier, challenge };
}

/**
 * 認可コードをトークンに交換
 */
async function exchangeCodeForToken(
  metadata: any,
  clientInfo: any,
  code: string,
  codeVerifier: string
): Promise<any> {
  const params = new URLSearchParams({
    grant_type: 'authorization_code',
    code,
    client_id: clientInfo.client_id,
    client_secret: clientInfo.client_secret,
    redirect_uri: REDIRECT_URI,
    code_verifier: codeVerifier
  });

  const response = await fetch(metadata.token_endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: params.toString()
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(`Token exchange failed: ${error.error || response.statusText}`);
  }

  return response.json();
}

/**
 * アクセストークンを取得
 *
 * トークンがなければOAuthフローを開始
 */
async function getAccessToken(): Promise<string> {
  // 既存のトークンをチェック
  const tokens = await loadTokens();
  if (tokens?.access_token) {
    // トークンの有効期限チェック（簡易実装）
    return tokens.access_token;
  }

  // 既にOAuthフロー実行中の場合は待機
  if (authFlowInProgress) {
    console.error('⏳ Waiting for OAuth flow to complete...');
    // 既に実行中のフローの完了を待つ
    await new Promise(resolve => setTimeout(resolve, 2000));
    const newTokens = await loadTokens();
    if (newTokens?.access_token) {
      return newTokens.access_token;
    }
    throw new Error('OAuth flow failed');
  }

  // OAuthフローを開始
  authFlowInProgress = true;
  try {
    console.error('\n🔐 No access token found. Starting OAuth flow...');

    // 1. OAuthメタデータを取得
    console.error('📋 Fetching OAuth metadata...');
    const metadata = await getOAuthMetadata();

    // 2. クライアント情報を取得または登録
    let clientInfo = await loadClientInformation();
    if (!clientInfo) {
      console.error('📝 Registering OAuth client...');
      clientInfo = await registerClient(metadata);
      await saveClientInformation(clientInfo);
      console.error('✅ Client registered:', clientInfo.client_id);
    }

    // 3. コールバックサーバーを起動
    await initializeOAuthFlow();

    // 4. PKCEチャレンジを生成
    const pkce = generatePKCE();
    await saveCodeVerifier(pkce.verifier);

    // 5. 認可URLを構築
    const authUrl = new URL(metadata.authorization_endpoint);
    authUrl.searchParams.set('response_type', 'code');
    authUrl.searchParams.set('client_id', clientInfo.client_id);
    authUrl.searchParams.set('redirect_uri', REDIRECT_URI);
    authUrl.searchParams.set('scope', 'read write');
    authUrl.searchParams.set('state', crypto.randomBytes(16).toString('hex'));
    authUrl.searchParams.set('code_challenge', pkce.challenge);
    authUrl.searchParams.set('code_challenge_method', 'S256');

    // 6. ブラウザで認可ページを開く
    console.error('📖 Opening browser for authorization...');
    console.error('🔗 Authorization URL:', authUrl.toString());
    await openBrowser(authUrl.toString());

    // 7. 認可コードを待機
    console.error('⏳ Waiting for authorization...');
    const code = await waitForAuthorizationCode();
    console.error('✅ Authorization code received!');

    // 8. 認可コードをアクセストークンに交換
    console.error('🔄 Exchanging code for token...');
    const codeVerifier = await loadCodeVerifier();
    const tokenResponse = await exchangeCodeForToken(metadata, clientInfo, code, codeVerifier);

    // 9. トークンを保存
    await saveTokens(tokenResponse);
    console.error('✅ Access token obtained and saved!');

    return tokenResponse.access_token;
  } finally {
    authFlowInProgress = false;
  }
}

/**
 * 外部APIへのHTTPリクエスト
 */
export async function callAPI(endpoint: string): Promise<any> {
  const token = await getAccessToken();
  const url = `${API_BASE}${endpoint}`;

  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(`API Error: ${error.error} - ${error.error_description || ''}`);
  }

  return response.json();
}
