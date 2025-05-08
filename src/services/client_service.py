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
                    pass
            except Exception:
                pass

        self.supabase_client = SupabaseClient._supabase_client_instance

    async def initiate_oauth_login(self) -> str | None:
        if not self.supabase_client:
            return None
        try:
            res = await self.supabase_client.auth.sign_in_with_oauth(
                {
                    "provider": "google",
                    "options": {"redirect_to": "http://localhost:8550/auth/callback"},
                }
            )
            return res.url
        except Exception:
            return None

    async def exchange_code_and_get_user(
        self, url: str
    ) -> tuple[object | None, str | None] | None:
        if not self.supabase_client:
            return None

        code = get_param_value(url, "code")

        if not code:
            return None

        try:
            exchange_response = (
                await self.supabase_client.auth.exchange_code_for_session(
                    {"auth_code": code}
                )
            )
            if not exchange_response or not exchange_response.session:
                return None

        except Exception:
            return None

        try:
            user_response = await self.supabase_client.auth.get_user()
            if user_response and user_response.user:
                return user_response.user, None
            else:
                return None
        except Exception:
            return None

    async def get_inventory_data(self) -> list | None:
        if not self.supabase_client:
            return None
        try:
            resp = (
                await self.supabase_client.table("inventory_items")
                .select("*")
                .execute()
            )
            return resp.data
        except Exception:
            return None
