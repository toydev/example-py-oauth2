"""
OAuth 2.0 モデルクラス (Authlib Mixin 実装)

Authlib が要求する ClientMixin, AuthorizationCodeMixin, TokenMixin を実装
"""

from authlib.oauth2.rfc6749 import ClientMixin, AuthorizationCodeMixin, TokenMixin
from datetime import datetime


class Client(ClientMixin):
    """クライアント（Authlib が要求）"""

    def __init__(self, client_id, client_secret, client_name, redirect_uris, grant_types, response_types, scope, token_endpoint_auth_method):
        self.client_id = client_id
        self.client_secret = client_secret
        self.client_name = client_name
        self.redirect_uris = redirect_uris
        self.grant_types = grant_types
        self.response_types = response_types
        self.scope = scope
        self.token_endpoint_auth_method = token_endpoint_auth_method

    def get_client_id(self):
        return self.client_id

    def get_default_redirect_uri(self):
        return self.redirect_uris[0]

    def get_allowed_scope(self, scope):
        if not scope:
            return ''
        return scope

    def check_redirect_uri(self, redirect_uri):
        return redirect_uri in self.redirect_uris

    def check_client_secret(self, client_secret):
        return self.client_secret == client_secret

    def check_response_type(self, response_type):
        return response_type in self.response_types

    def check_grant_type(self, grant_type):
        return grant_type in self.grant_types

    def check_endpoint_auth_method(self, method, endpoint):
        if endpoint == 'token':
            return self.token_endpoint_auth_method == method
        return True


class AuthorizationCode(AuthorizationCodeMixin):
    """認可コード（Authlib が要求）"""

    def __init__(self, code, client_id, redirect_uri, scope, username, expires_at):
        self.code = code
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.username = username
        self.expires_at = expires_at

    def get_redirect_uri(self):
        return self.redirect_uri

    def get_scope(self):
        return self.scope


class Token(TokenMixin):
    """トークン（Authlib が要求）"""

    def __init__(self, access_token, token_type, scope, expires_at, client_id, username):
        self.access_token = access_token
        self.token_type = token_type
        self.scope = scope
        self.expires_at = expires_at
        self.client_id = client_id
        self.username = username

    def check_client(self, client):
        """トークンが指定されたクライアントに発行されたか確認"""
        return self.client_id == client.get_client_id()

    def get_client(self):
        """トークンに関連付けられたクライアントを返す"""
        from storage import storage
        return storage.clients.get(self.client_id)

    def get_user(self):
        """トークンに関連付けられたユーザーを返す"""
        from storage import storage
        user = storage.users.get(self.username)
        if user:
            return {"username": self.username}
        return None

    def get_scope(self):
        """トークンのスコープを返す"""
        return self.scope

    def get_expires_in(self):
        """トークンの有効期限（秒）を返す"""
        return int((self.expires_at - datetime.now()).total_seconds())

    def is_expired(self):
        """トークンが期限切れか確認"""
        return datetime.now() > self.expires_at

    def is_revoked(self):
        """トークンが無効化されているか確認"""
        return False
