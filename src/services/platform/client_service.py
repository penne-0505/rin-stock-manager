from supabase import AsyncClient, acreate_client

from utils.config import settings
from utils.url_parser import get_param_value


class SupabaseClient:
    _supabase_client_instance: AsyncClient | None = None

    def __init__(self):
        self.SUPABASE_URL = settings.SUPABASE_URL
        self.SUPABASE_ANON_KEY = settings.SUPABASE_ANON_KEY

        if SupabaseClient._supabase_client_instance is None:
            try:
                if self.SUPABASE_URL and self.SUPABASE_ANON_KEY:
                    SupabaseClient._supabase_client_instance = acreate_client(
                        self.SUPABASE_URL, self.SUPABASE_ANON_KEY
                    )
                else:
                    raise ValueError(
                        "Supabase URL or Anon Key is not set in the environment variables."
                    )
            except Exception as e:
                raise RuntimeError(
                    "Failed to create Supabase client. Please check your configuration."
                ) from e

        self.supabase_client = SupabaseClient._supabase_client_instance

    async def initiate_oauth_login(self) -> str | None:
        """Google OAuth URL を取得する"""
        if not self.supabase_client:
            raise RuntimeError(
                "Supabase client is not initialized. Please check your configuration."
            )

        try:
            res = await self.supabase_client.auth.sign_in_with_oauth(
                {
                    "provider": "google",
                    "options": {"redirect_to": "http://localhost:8550/auth/callback"},
                }
            )
            return res.url
        except Exception as e:
            raise RuntimeError(
                "Failed to initiate OAuth login. Please check your configuration."
            ) from e

    async def exchange_code_and_get_user(
        self, url: str
    ) -> tuple[object | None, str | None] | None:
        """redirect URI に戻ったときの処理: トークンをセット→ユーザー情報取得"""
        if not self.supabase_client:
            raise RuntimeError(
                "Supabase client is not initialized. Please check your configuration."
            )

        code = get_param_value(url, "code")

        if not code:
            raise ValueError("Authorization code not found in the URL.")

        try:
            exchange_response = (
                await self.supabase_client.auth.exchange_code_for_session(
                    {"auth_code": code}
                )
            )

            if not exchange_response or not exchange_response.session:
                raise RuntimeError("Failed to exchange code for session.")

        except Exception as e:
            raise RuntimeError(
                "Failed to exchange code for session. Please check your configuration."
            ) from e

        try:
            user_response = await self.supabase_client.auth.get_user()
            if user_response and user_response.user:
                return user_response.user, None
            else:
                # ユーザー情報取得失敗
                return None
        except Exception as e:
            raise RuntimeError(
                "Failed to get user information. Please check your configuration."
            ) from e
