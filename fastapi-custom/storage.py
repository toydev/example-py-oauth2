"""
OAuth 2.0 ストレージ（インメモリ実装）

本番環境ではDBを使用すること
"""


class Storage:
    """インメモリストレージ"""

    def __init__(self):
        # クライアント情報
        self.clients = {
            "demo-client-id": {
                "client_secret": "demo-client-secret",
                "redirect_uris": ["http://localhost:5001/callback"],
            }
        }
        # 認可コード（有効期限10分）
        self.auth_codes = {}
        # アクセストークン（有効期限1時間）
        self.access_tokens = {}
        # ユーザー情報（簡易的なユーザーDB）
        self.users = {
            "demo-user": {
                "password": "demo-password",
                "name": "Demo User",
                "email": "demo@example.com",
                "bio": "OAuth 2.0 デモユーザーです",
                "location": "Tokyo, Japan",
            }
        }
        # サンプルデータ（投稿）
        self.posts = {
            "demo-user": [
                {
                    "id": 1,
                    "title": "OAuth 2.0 入門",
                    "content": "OAuth 2.0 認可コードフローについて学びました。",
                    "created_at": "2025-10-01T10:00:00Z",
                },
                {
                    "id": 2,
                    "title": "FastAPI で OAuth サーバー構築",
                    "content": "FastAPI を使って認可サーバーを実装しました。",
                    "created_at": "2025-10-02T15:30:00Z",
                },
                {
                    "id": 3,
                    "title": "アクセストークンの管理",
                    "content": "トークンの有効期限管理について理解が深まりました。",
                    "created_at": "2025-10-03T09:15:00Z",
                },
            ]
        }


# グローバルストレージインスタンス
storage = Storage()
