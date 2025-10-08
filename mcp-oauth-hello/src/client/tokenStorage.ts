/**
 * OAuth トークンストレージ
 *
 * ファイルシステムにトークンを永続化
 */

import fs from 'fs/promises';
import path from 'path';
import os from 'os';
import { OAuthTokens, OAuthClientInformationFull } from '@modelcontextprotocol/sdk/shared/auth.js';

const STORAGE_DIR = path.join(os.homedir(), '.mcp-oauth-hello');
const TOKENS_FILE = path.join(STORAGE_DIR, 'tokens.json');
const CLIENT_FILE = path.join(STORAGE_DIR, 'client.json');
const VERIFIER_FILE = path.join(STORAGE_DIR, 'verifier.txt');

/**
 * ストレージディレクトリを初期化
 */
async function ensureStorageDir() {
  try {
    await fs.mkdir(STORAGE_DIR, { recursive: true });
  } catch (error) {
    // ディレクトリが既に存在する場合は無視
  }
}

/**
 * OAuthトークンを保存
 */
export async function saveTokens(tokens: OAuthTokens): Promise<void> {
  await ensureStorageDir();
  await fs.writeFile(TOKENS_FILE, JSON.stringify(tokens, null, 2), 'utf-8');
  console.error('✅ Tokens saved to', TOKENS_FILE);
}

/**
 * OAuthトークンを読み込み
 */
export async function loadTokens(): Promise<OAuthTokens | undefined> {
  try {
    const data = await fs.readFile(TOKENS_FILE, 'utf-8');
    return JSON.parse(data);
  } catch (error) {
    return undefined;
  }
}

/**
 * クライアント情報を保存
 */
export async function saveClientInformation(client: OAuthClientInformationFull): Promise<void> {
  await ensureStorageDir();
  await fs.writeFile(CLIENT_FILE, JSON.stringify(client, null, 2), 'utf-8');
  console.error('✅ Client information saved to', CLIENT_FILE);
}

/**
 * クライアント情報を読み込み
 */
export async function loadClientInformation(): Promise<OAuthClientInformationFull | undefined> {
  try {
    const data = await fs.readFile(CLIENT_FILE, 'utf-8');
    return JSON.parse(data);
  } catch (error) {
    return undefined;
  }
}

/**
 * PKCEコードベリファイアを保存
 */
export async function saveCodeVerifier(verifier: string): Promise<void> {
  await ensureStorageDir();
  await fs.writeFile(VERIFIER_FILE, verifier, 'utf-8');
}

/**
 * PKCEコードベリファイアを読み込み
 */
export async function loadCodeVerifier(): Promise<string> {
  try {
    return await fs.readFile(VERIFIER_FILE, 'utf-8');
  } catch (error) {
    throw new Error('Code verifier not found');
  }
}

/**
 * 認証情報を削除
 */
export async function clearCredentials(scope: 'all' | 'client' | 'tokens' | 'verifier'): Promise<void> {
  try {
    switch (scope) {
      case 'all':
        await fs.rm(STORAGE_DIR, { recursive: true, force: true });
        console.error('🗑️  All credentials cleared');
        break;
      case 'client':
        await fs.unlink(CLIENT_FILE);
        console.error('🗑️  Client credentials cleared');
        break;
      case 'tokens':
        await fs.unlink(TOKENS_FILE);
        console.error('🗑️  Tokens cleared');
        break;
      case 'verifier':
        await fs.unlink(VERIFIER_FILE);
        console.error('🗑️  Code verifier cleared');
        break;
    }
  } catch (error) {
    // ファイルが存在しない場合は無視
  }
}
