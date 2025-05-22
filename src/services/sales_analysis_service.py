from datetime import datetime


class SalesReport:
    # 仮のDTO。notMVPなので詳細は後で決める。
    pass


class SalesAnalysisService:
    # このgroup_byがあいまいなので、実装時には詰める
    def get_sales_report(
        self, start_date: datetime, end_date: datetime, group_by: str | None = None
    ) -> SalesReport:
        """指定期間の売上レポート（日次・週次・月次、商品別など）"""

    def get_top_selling_items(
        self, start_date: datetime, end_date: datetime, limit: int = 10
    ) -> list:
        """売上上位の商品を取得する"""

    # ここも同様甘いので、実装時に詰める
    def get_sales_trends(
        self,
        period: str = "daily",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """売上推移（グラフ等に使う、時間帯別/曜日別など）"""
