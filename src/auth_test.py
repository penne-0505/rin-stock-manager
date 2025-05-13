import flet as ft
from flet import Column, ElevatedButton, Page, RouteChangeEvent, SnackBar, Text, app

from repositories.concrete.inventory_item_repo import InventoryItemRepository
from repositories.concrete.order_repo import OrderItemRepository, OrderRepository

# services.auth_service からのインポートを変更
from services.app_services.client_service import SupabaseClient
from services.domain_services.order_service import OrderService

# AuthService のインスタンスを作成
auth_service = SupabaseClient()


async def handle_login_button_click(pg: Page):
    """ログインボタンクリック時の処理"""
    if not auth_service.supabase_client:
        show_snackbar(pg, "Supabase clientが初期化されていません。")
        return

    oauth_url = await auth_service.initiate_oauth_login()
    if oauth_url:
        pg.launch_url(oauth_url)
    else:
        show_snackbar(pg, "OAuth URLの取得に失敗しました。")


async def handle_auth_callback(url: str, pg: Page):
    """認証コールバック処理"""
    if not auth_service.supabase_client:
        show_snackbar(pg, "Supabase clientが初期化されていません。")
        return

    try:
        user, error_message = await auth_service.exchange_code_and_get_user(url)
    except Exception:
        pass

    if error_message:
        show_snackbar(pg, error_message)
        return

    pg.controls.clear()
    if user and hasattr(user, "email"):
        pg.controls.append(Text(f"ログイン成功！こんにちは {user.email}"))

        inventory_repo = InventoryItemRepository(auth_service.supabase_client)
        order_repo = OrderRepository(auth_service.supabase_client)
        order_item_repo = OrderItemRepository(auth_service.supabase_client)

        order_service = OrderService(
            order_repo=order_repo,
            order_item_repo=order_item_repo,
            inv_item_repo=inventory_repo,
        )

        orders = await order_service.get_order_by_filter()  # フィルタ無しで、全件取得
        if orders is None:  # データ取得失敗の場合
            pg.controls.append(Text("注文データの取得に失敗しました。"))
        elif not orders:  # データが空の場合
            pg.controls.append(Text("あなたの注文データはありませんでした。"))
        else:
            for order in orders:
                pg.controls.append(Text(f"注文ID: {order.id}"))
                for item in order.items:
                    pg.controls.append(
                        Text(
                            f"アイテムID: {item.inventory_item_id}, 数量: {item.quantity}"
                        )
                    )
    else:
        pg.controls.append(
            Text("ログインに失敗しました。ユーザー情報を取得できませんでした。")
        )
    pg.update()


def show_snackbar(pg: Page, message: str):
    """スナックバーを表示する"""
    snack_bar = SnackBar(Text(message))
    pg.controls.append(snack_bar)  # snack_bar を pg.controls に追加してから open する
    snack_bar.open = True
    pg.update()


def main(pg: Page):
    pg.title = "Supabase Auth Demo"
    pg.vertical_alignment = ft.MainAxisAlignment.CENTER
    pg.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    async def route_change(e: RouteChangeEvent):
        if e.route.startswith("/auth/callback"):
            url = e.route
            await handle_auth_callback(
                url, pg
            )  # handle_callback を handle_auth_callback に変更
        else:
            pg.controls.clear()
            pg.controls.append(
                Column(
                    [
                        Text("Google アカウントでサインアップ / ログイン"),
                        ElevatedButton(
                            "Google でログイン",
                            # login 関数呼び出しを handle_login_button_click に変更
                            on_click=lambda _: pg.run_task(
                                handle_login_button_click, pg
                            ),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                )
            )
            try:
                pg.update()
            except Exception:
                # ページアップデート中のエラー
                pass

    pg.on_route_change = route_change
    pg.go(pg.route)


if __name__ == "__main__":
    app(target=main, port=8550, view="web_browser")
