from models.order import Order, OrderItem
from repositories.abstruct.crud_repo import CrudRepository
from services.app_services.client_service import SupabaseClient

"""
思考整理

order_itemsは、買い物カートのようなもので、オーダー、購入予定の商品(のID)と紐づけられている
    -> orderはなにかしらのorder_itemsを持たなければならない (カートに商品がないと、オーダーはできない)
    -> オーダーの作成時には、order_itemsは必須
    つまり'OrderRepository'単体では、オーダーの作成はできない (サービスクラスに相当する操作 (複数のテーブルを横断的に操作))
    よって、OrderRepositoryは、抽象CRUDのインターフェースを狭める程度の実装にとどまる？
    オーダー作成や削除、更新、取得などは、サービスクラスで行う必要がある。<- 冗長な気がする (というよりボイラープレート的？)

"""


class OrderRepository(CrudRepository[Order]):
    def __init__(self, client: SupabaseClient) -> None:
        super().__init__(client, Order.__table_name__())


class OrderItemRepository(CrudRepository[OrderItem]):
    def __init__(self, client: SupabaseClient) -> None:
        super().__init__(client, OrderItem.__table_name__())
