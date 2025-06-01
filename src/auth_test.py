from decimal import Decimal
from uuid import UUID

import flet as ft
from flet import (
    Column,
    ElevatedButton,
    FloatingActionButton,
    Page,
    RouteChangeEvent,
    SnackBar,
    Text,
    app,
)

from constants.options import UnitType
from models.domains.inventory import Material
from models.dto.order import OrderSearchRequest
from services.business.inventory_service import InventoryService
from services.business.order_service import OrderService

# 最新の実装に合わせてインポートを修正
from services.platform.client_service import SupabaseClient

auth_service = SupabaseClient()


async def handle_login_button_click(pg: Page):
    """ログインボタンクリック時の処理"""
    await auth_service.init_client()

    if not auth_service.supabase_client:
        show_snackbar(pg, "Supabase clientが初期化されていません。")
        return

    oauth_url = await auth_service.initiate_oauth_login()
    if oauth_url:
        pg.launch_url(oauth_url)
    else:
        show_snackbar(pg, "OAuth URLの取得に失敗しました。")


async def handle_auth_callback(url: str, pg: Page):
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
        pg.controls.append(Text(f"ログイン成功！こんにちは `{user.email}` さん！"))

        # ページを更新するためのfloating buttonを作成
        pg.controls.append(
            FloatingActionButton(icon=ft.Icons.REFRESH, on_click=lambda _: pg.update())
        )

        # 最新の実装に合わせて OrderService を初期化
        order_service = OrderService(auth_service)

        # フィルタなしで全件取得するために OrderSearchRequest を使用
        search_request = OrderSearchRequest(
            page=1,
            limit=100,  # 適当な上限
            status_filter=None,  # 全ステータス
            date_from=None,
            date_to=None,
            customer_name=None,
            menu_item_name=None,
        )

        # 在庫のデモデータを追加するボタンを作成
        inventory_service = InventoryService(auth_service)
        temp_data = Material(
            name="temp_material",
            category_id=UUID("6bba9a48-6798-4d88-8e50-677dace1f33f"),
            unit_type=UnitType.PIECE,
            current_stock=Decimal("100.00"),
            alert_threshold=Decimal("20.00"),
            critical_threshold=Decimal("10.00"),
            notes="this is a temporary material for demo purposes",
        )
        pg.controls.append(
            ElevatedButton(
                "在庫デモデータを追加",
                on_click=lambda _: pg.run_task(
                    inventory_service.create_material, temp_data, user.id
                ),
            )
        )

        # TODO: このファイルに、DB操作をUI経由でテストするコードを追加する

        all_material = await inventory_service.material_repo.find()
        pg.controls.append(
            Text(f"全ての材料: {', '.join([m.name for m in all_material])}")
        )

        try:
            # get_order_by_filter の代わりに get_order_history を使用
            result = await order_service.get_order_history(search_request, user.id)
            orders = result.get("orders", [])

            if not orders:  # データが空の場合
                pg.controls.append(Text("あなたの注文データはありませんでした。"))
            else:
                for order in orders:
                    pg.controls.append(Text(f"注文ID: {order.id}"))
                    # 注文明細を取得
                    order_items = await order_service.get_order_details(
                        order.id, user.id
                    )
                    for item in order_items:
                        pg.controls.append(
                            Text(
                                f"メニューアイテムID: {item.menu_item_id}, 数量: {item.quantity}"
                            )
                        )
        except Exception as e:
            pg.add(Text(f"注文データの取得に失敗しました: {str(e)}"))
            raise e
    else:
        pg.controls.append(
            Text("ログインに失敗しました。ユーザー情報を取得できませんでした。")
        )
    pg.update()


def show_snackbar(pg: Page, message: str):
    """スナックバーを表示する"""
    snack_bar = SnackBar(Text(message))
    pg.controls.append(snack_bar)
    snack_bar.open = True
    pg.update()


def main(pg: Page):
    pg.title = "Supabase Auth Demo"
    pg.vertical_alignment = ft.MainAxisAlignment.CENTER
    pg.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    async def route_change(e: RouteChangeEvent):
        if e.route.startswith("/auth/callback"):
            url = e.route
            await handle_auth_callback(url, pg)
        else:
            pg.controls.clear()
            pg.controls.append(
                Column(
                    [
                        Text("Google アカウントでサインアップ / ログイン"),
                        ElevatedButton(
                            "Google でログイン",
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
                pass

    pg.on_route_change = route_change
    pg.go(pg.route)


if __name__ == "__main__":
    app(target=main, port=8550, view="web_browser")
