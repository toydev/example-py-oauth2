/**
 * 開発用データストレージ
 *
 * ESSENTIALS.mdで学んだOAuthの知識をベースに、
 * シンプルなインメモリストレージを実装
 */

export interface User {
  id: string;
  username: string;
  email: string;
  name: string;
}

export interface Post {
  id: string;
  userId: string;
  title: string;
  content: string;
  createdAt: string;
}

export interface AccessToken {
  token: string;
  userId: string;
  expiresAt: Date;
  scope: string;
}

// デモ用ユーザーデータ
export const users: Map<string, User> = new Map([
  ['user-1', {
    id: 'user-1',
    username: 'demo-user',
    email: 'demo@example.com',
    name: 'Demo User'
  }]
]);

// デモ用投稿データ
export const posts: Map<string, Post> = new Map([
  ['post-1', {
    id: 'post-1',
    userId: 'user-1',
    title: 'Hello MCP OAuth!',
    content: 'This is a demo post from our protected API.',
    createdAt: new Date().toISOString()
  }],
  ['post-2', {
    id: 'post-2',
    userId: 'user-1',
    title: 'OAuth 2.1 の本質',
    content: 'ESSENTIALS.mdで学んだ通り、パスワード保護とブラウザ露出問題から全てが導かれる。',
    createdAt: new Date().toISOString()
  }]
]);

// 開発用アクセストークン（後でOAuthサーバーと統合）
export const accessTokens: Map<string, AccessToken> = new Map([
  ['dev-token-12345', {
    token: 'dev-token-12345',
    userId: 'user-1',
    expiresAt: new Date(Date.now() + 3600 * 1000), // 1時間後
    scope: 'read write'
  }]
]);

// トークン検証
export function validateToken(token: string): AccessToken | null {
  const accessToken = accessTokens.get(token);

  if (!accessToken) {
    return null;
  }

  // 有効期限チェック
  if (accessToken.expiresAt < new Date()) {
    accessTokens.delete(token);
    return null;
  }

  return accessToken;
}

// ユーザー取得
export function getUser(userId: string): User | null {
  return users.get(userId) || null;
}

// 投稿一覧取得（ユーザーIDでフィルタ）
export function getPosts(userId: string): Post[] {
  return Array.from(posts.values()).filter(post => post.userId === userId);
}
