/**
 * 保護されたAPIルート
 *
 * ESSENTIALS.mdで学んだ通り、アクセストークンで保護されたリソース
 */

import { Router } from 'express';
import { createRequireAuth, requireScope } from './middleware';
import { getUser, getPosts } from './storage';
import { SimpleOAuthProvider } from '../oauth/provider';

export function createApiRoutes(oauthProvider: SimpleOAuthProvider) {
  const router = Router();
  const requireAuth = createRequireAuth(oauthProvider);

/**
 * GET /api/me
 *
 * 現在のユーザー情報を取得
 */
router.get('/me', requireAuth, (req, res) => {
  const user = getUser(req.userId!);

  if (!user) {
    return res.status(404).json({
      error: 'user_not_found',
      error_description: 'User not found'
    });
  }

  res.json({
    id: user.id,
    username: user.username,
    email: user.email,
    name: user.name
  });
});

/**
 * GET /api/posts
 *
 * 現在のユーザーの投稿一覧を取得
 */
router.get('/posts', requireAuth, requireScope('read'), (req, res) => {
  const posts = getPosts(req.userId!);

  res.json({
    posts: posts.map(post => ({
      id: post.id,
      title: post.title,
      content: post.content,
      createdAt: post.createdAt
    }))
  });
});

/**
 * GET /api/profile
 *
 * ユーザープロフィール詳細（追加デモ用）
 */
router.get('/profile', requireAuth, (req, res) => {
  const user = getUser(req.userId!);

  if (!user) {
    return res.status(404).json({
      error: 'user_not_found'
    });
  }

  const posts = getPosts(req.userId!);

  res.json({
    user: {
      id: user.id,
      username: user.username,
      email: user.email,
      name: user.name
    },
    stats: {
      totalPosts: posts.length
    }
  });
});

  return router;
}
