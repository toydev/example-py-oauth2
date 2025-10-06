"""
OAuth 2.0 Grants と Validators

Authlib の Grant と Validator を実装
"""

from authlib.oauth2.rfc6749 import grants
from authlib.oauth2.rfc6750 import BearerTokenValidator
from datetime import datetime, timedelta
from models import AuthorizationCode
from storage import storage


class AuthorizationCodeGrant(grants.AuthorizationCodeGrant):
    """認可コードグラント（Authlib）"""

    TOKEN_ENDPOINT_AUTH_METHODS = ['client_secret_post', 'client_secret_basic']

    def save_authorization_code(self, code, request):
        """認可コードを保存"""
        auth_code = AuthorizationCode(
            code=code,
            client_id=request.client_id,
            redirect_uri=request.redirect_uri,
            scope=request.scope,
            username=request.user["username"],
            expires_at=datetime.now() + timedelta(minutes=10),
        )
        storage.auth_codes[code] = auth_code

    def query_authorization_code(self, code, client):
        """認可コードを取得"""
        auth_code = storage.auth_codes.get(code)
        if not auth_code:
            return None

        # 期限切れチェック
        if datetime.now() > auth_code.expires_at:
            return None

        # クライアントIDチェック
        if auth_code.client_id != client.client_id:
            return None

        return auth_code

    def delete_authorization_code(self, authorization_code):
        """認可コードを削除（使い捨て）"""
        code = authorization_code.code
        if code in storage.auth_codes:
            del storage.auth_codes[code]

    def authenticate_user(self, authorization_code):
        """ユーザー情報を取得"""
        username = authorization_code.username
        user = storage.users.get(username)
        if user:
            return {"username": username}
        return None


class MyBearerTokenValidator(BearerTokenValidator):
    """Bearer トークンの検証（Authlib）"""

    def authenticate_token(self, token_string):
        """トークンを検証"""
        token = storage.access_tokens.get(token_string)

        if not token:
            return None

        # 期限切れチェック
        if token.is_expired():
            return None

        return token

    def request_invalid(self, request):
        return False

    def token_revoked(self, token):
        return False
