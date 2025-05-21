from supabase import AsyncClient, create_client

from utils.config import settings
from utils.utils import get_param_value


class SupabaseClient:
    _supabase_client_instance: AsyncClient | None = None

    def __init__(self):
        self.SUPABASE_URL = settings.SUPABASE_URL
        self.SUPABASE_ANON_KEY = settings.SUPABASE_ANON_KEY

        if SupabaseClient._supabase_client_instance is None:
            try:
                if self.SUPABASE_URL and self.SUPABASE_ANON_KEY:
                    SupabaseClient._supabase_client_instance = create_client(
                        self.SUPABASE_URL, self.SUPABASE_ANON_KEY
                    )
                else:
                    # Supabase URL または Anon Key が設定されていない場合
                    pass
            except Exception:
                # Supabase クライアントの初期化中にエラーが発生した場合
                pass

        self.supabase_client = SupabaseClient._supabase_client_instance

    async def initiate_oauth_login(self) -> str | None:
        """Google OAuth URL を取得する"""
        if not self.supabase_client:
            # Supabase クライアントが初期化されていない場合
            return None
        try:
            res = self.supabase_client.auth.sign_in_with_oauth(
                {
                    "provider": "google",
                    "options": {"redirect_to": "http://localhost:8550/auth/callback"},
                }
            )
            return res.url
        except Exception:
            # OAuth URL 取得中のエラー
            return None

    async def exchange_code_and_get_user(
        self, url: str
    ) -> tuple[object | None, str | None] | None:
        """redirect URI に戻ったときの処理: トークンをセット→ユーザー情報取得"""
        if not self.supabase_client:
            # Supabase クライアントが初期化されていない場合
            return None

        code = get_param_value(url, "code")

        if not code:
            # URL に code パラメータがない場合
            return None

        try:
            exchange_response = self.supabase_client.auth.exchange_code_for_session(
                {"auth_code": code}
            )

            if not exchange_response or not exchange_response.session:
                # トークン交換失敗
                return None

        except Exception:
            # トークン交換中のエラー
            return None

        try:
            user_response = self.supabase_client.auth.get_user()
            if user_response and user_response.user:
                return user_response.user, None
            else:
                # ユーザー情報取得失敗
                return None
        except Exception:
            # ユーザー情報取得中のエラー
            return None
