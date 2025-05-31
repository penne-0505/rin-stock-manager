# API Reference

This document provides detailed API reference for the Rin Stock Manager repositories and services.

## Repository Layer

All repositories inherit from `CrudRepository[M, ID]` and provide standard CRUD operations plus domain-specific methods.

### Base CRUD Operations

Every repository includes these standard methods:

```python
# Create
async def create(entity: M) -> M | None

# Read
async def get(key: ID | PKMap) -> M | None
async def list(*, limit: int = 100, offset: int = 0) -> list[M]
async def find(filters: Filter | None = None, order_by: OrderBy | None = None,
               *, limit: int = 100, offset: int = 0) -> list[M]
async def count(filters: Filter | None = None) -> int

# Update
async def update(key: ID | PKMap, patch: Mapping[str, Any]) -> M | None

# Delete
async def delete(key: ID | PKMap) -> None

# Utility
async def exists(key: ID | PKMap) -> bool
```

## Analytics Repositories

### DailySummaryRepository

Provides analytics and reporting for daily business summaries.

```python
from repositories.domains.analysis_repo import DailySummaryRepository
```

#### Methods

##### `find_by_date(target_date: datetime, user_id: UUID) -> DailySummary | None`

Retrieves daily summary for a specific date.

**Parameters:**
- `target_date`: Date to query (normalized to 00:00:00)
- `user_id`: User identifier for data isolation

**Returns:** Daily summary or None if not found

**Example:**
```python
from datetime import datetime
summary = await repo.find_by_date(datetime(2024, 1, 15), user_id)
```

##### `find_by_date_range(date_from: datetime, date_to: datetime, user_id: UUID) -> list[DailySummary]`

Retrieves summaries within a date range.

**Parameters:**
- `date_from`: Start date (normalized to 00:00:00)
- `date_to`: End date (normalized to 23:59:59)
- `user_id`: User identifier

**Returns:** List of summaries sorted by date ascending

**Example:**
```python
summaries = await repo.find_by_date_range(
    datetime(2024, 1, 1),
    datetime(2024, 1, 31),
    user_id
)
```

## Inventory Repositories

### MaterialRepository

Manages materials/ingredients with stock tracking.

```python
from repositories.domains.inventory_repo import MaterialRepository
```

#### Methods

##### `find_by_category_id(category_id: UUID | None, user_id: UUID) -> list[Material]`

Filters materials by category.

**Parameters:**
- `category_id`: Category filter (None returns all materials)
- `user_id`: User identifier

**Returns:** List of materials

##### `find_below_alert_threshold(user_id: UUID) -> list[Material]`

Finds materials requiring stock replenishment alerts.

**Returns:** Materials with stock below alert threshold

##### `find_below_critical_threshold(user_id: UUID) -> list[Material]`

Finds materials in critical stock situation.

**Returns:** Materials with stock below critical threshold

##### `find_by_ids(material_ids: list[UUID], user_id: UUID) -> list[Material]`

Batch retrieval of materials by IDs.

**Parameters:**
- `material_ids`: List of material IDs to retrieve
- `user_id`: User identifier

**Returns:** List of found materials

##### `update_stock_amount(material_id: UUID, new_amount: Decimal, user_id: UUID) -> Material | None`

Updates stock amount for a material.

**Parameters:**
- `material_id`: Material to update
- `new_amount`: New stock amount
- `user_id`: User identifier

**Returns:** Updated material or None

### MaterialCategoryRepository

Manages material categories.

##### `find_active_ordered(user_id: UUID) -> list[MaterialCategory]`

Returns active categories in display order.

### RecipeRepository

Manages recipe ingredients and relationships.

##### `find_by_menu_item_id(menu_item_id: UUID, user_id: UUID) -> list[Recipe]`

Gets recipes for a menu item.

##### `find_by_material_id(material_id: UUID, user_id: UUID) -> list[Recipe]`

Gets recipes using a specific material.

##### `find_by_menu_item_ids(menu_item_ids: list[UUID], user_id: UUID) -> list[Recipe]`

Batch retrieval of recipes for multiple menu items.

## Menu Repositories

### MenuItemRepository

Manages menu items with search and filtering capabilities.

```python
from repositories.domains.menu_repo import MenuItemRepository
```

#### Methods

##### `find_by_category_id(category_id: UUID | None, user_id: UUID) -> list[MenuItem]`

Filters menu items by category with display ordering.

##### `find_available_only(user_id: UUID) -> list[MenuItem]`

Returns only available menu items.

##### `search_by_name(keyword: str | list[str], user_id: UUID) -> list[MenuItem]`

Advanced search with multiple keywords.

**Parameters:**
- `keyword`: Single keyword or list of keywords for AND search
- `user_id`: User identifier

**Features:**
- Case-insensitive matching
- Multiple keyword AND logic
- Keyword normalization

**Example:**
```python
# Single keyword
items = await repo.search_by_name("pizza", user_id)

# Multiple keywords (AND logic)
items = await repo.search_by_name(["chicken", "spicy"], user_id)
```

##### `find_by_ids(menu_item_ids: list[UUID], user_id: UUID) -> list[MenuItem]`

Batch retrieval of menu items.

### MenuCategoryRepository

##### `find_active_ordered(user_id: UUID) -> list[MenuCategory]`

Returns active menu categories in display order.

## Order Repositories

### OrderRepository

Complete order lifecycle management with analytics.

```python
from repositories.domains.order_repo import OrderRepository
```

#### Methods

##### `find_active_draft_by_user(user_id: UUID) -> Order | None`

Gets the active draft order (shopping cart).

##### `find_by_status_list(status_list: list[OrderStatus], user_id: UUID) -> list[Order]`

Filters orders by multiple statuses.

**Example:**
```python
from constants.status import OrderStatus
active_orders = await repo.find_by_status_list([
    OrderStatus.DRAFT, 
    OrderStatus.ACTIVE
], user_id)
```

##### `search_with_pagination(filter: Filter, page: int, limit: int) -> tuple[list[Order], int]`

Paginated order search with total count.

**Returns:** Tuple of (orders, total_count)

##### `find_by_date_range(date_from: datetime, date_to: datetime, user_id: UUID) -> list[Order]`

Date range filtering with automatic normalization.

##### `find_completed_by_date(target_date: datetime, user_id: UUID) -> list[Order]`

Gets completed orders for a specific date.

##### `count_by_status_and_date(target_date: datetime, user_id: UUID) -> dict[OrderStatus, int]`

Analytics: order count by status for a date.

**Returns:** Dictionary mapping status to count

##### `generate_next_order_number(user_id: UUID) -> str`

Generates unique order number in format YYYYMMDD-XXX.

**Example result:** "20241215-001"

##### `find_orders_by_completion_time_range(start_time: datetime, end_time: datetime, user_id: UUID) -> list[Order]`

Analytics for order completion time analysis.

### OrderItemRepository

Order line item management.

##### `find_by_order_id(order_id: UUID) -> list[OrderItem]`

Gets all items for an order.

##### `find_existing_item(order_id: UUID, menu_item_id: UUID) -> OrderItem | None`

Checks for existing order item (duplicate detection).

##### `delete_by_order_id(order_id: UUID) -> bool`

Cascade deletion of order items.

##### `find_by_menu_item_and_date_range(menu_item_id: UUID, date_from: datetime, date_to: datetime, user_id: UUID) -> list[OrderItem]`

Sales analysis for specific menu item.

##### `get_menu_item_sales_summary(days: int, user_id: UUID) -> list[dict[str, Any]]`

Aggregated sales analytics for the last N days.

**Returns:** List of dictionaries with sales summary data

## Stock Repositories

### PurchaseRepository

Purchase/procurement tracking.

```python
from repositories.domains.stock_repo import PurchaseRepository
```

##### `find_recent(days: int, user_id: UUID) -> list[Purchase]`

Recent purchases within specified days.

##### `find_by_date_range(date_from: datetime, date_to: datetime, user_id: UUID) -> list[Purchase]`

Date range filtering with normalization.

### PurchaseItemRepository

Purchase line items.

##### `find_by_purchase_id(purchase_id: UUID) -> list[PurchaseItem]`

Items for a specific purchase.

##### `create_batch(purchase_items: list[PurchaseItem]) -> list[PurchaseItem]`

Batch creation for performance.

### StockAdjustmentRepository

Manual stock adjustments.

##### `find_by_material_id(material_id: UUID, user_id: UUID) -> list[StockAdjustment]`

Adjustment history for a material.

##### `find_recent(days: int, user_id: UUID) -> list[StockAdjustment]`

Recent adjustments.

### StockTransactionRepository

Complete stock movement audit trail.

##### `create_batch(transactions: list[StockTransaction]) -> list[StockTransaction]`

Batch transaction recording.

##### `find_by_reference(reference_type: str, reference_id: UUID, user_id: UUID) -> list[StockTransaction]`

Transactions by reference (order, purchase, etc.).

##### `find_by_material_and_date_range(material_id: UUID, date_from: datetime, date_to: datetime, user_id: UUID) -> list[StockTransaction]`

Material transaction history.

##### `find_consumption_transactions(date_from: datetime, date_to: datetime, user_id: UUID) -> list[StockTransaction]`

Consumption analysis (negative amounts only).

## Filter System

### Filter Operations

```python
from constants.types import FilterOp

# Available operations
FilterOp.EQ        # Equal
FilterOp.NEQ       # Not equal
FilterOp.GT        # Greater than
FilterOp.GTE       # Greater than or equal
FilterOp.LT        # Less than
FilterOp.LTE       # Less than or equal
FilterOp.LIKE      # Pattern matching
FilterOp.ILIKE     # Case-insensitive pattern matching
FilterOp.IN        # In list
FilterOp.IS        # Is null/not null
```

### Simple Filters (AND logic)

```python
filters = {
    "status": (FilterOp.EQ, "active"),
    "category_id": (FilterOp.IN, [uuid1, uuid2])
}
```

### OR Conditions

```python
from utils.filters import OrCondition

or_filter = OrCondition([
    {"status": (FilterOp.EQ, "active")},
    {"status": (FilterOp.EQ, "low_stock")}
])
```

### Complex Conditions

```python
from utils.filters import ComplexCondition, AndCondition, OrCondition

complex_filter = ComplexCondition([
    AndCondition({"supplier_id": (FilterOp.EQ, 1)}),
    OrCondition([
        {"status": (FilterOp.EQ, "active")},
        {"status": (FilterOp.EQ, "pending")}
    ])
], operator="and")
```

## Error Handling

All repository methods handle common error cases:

- **Empty results**: Return empty lists or None as appropriate
- **Invalid IDs**: Raise appropriate exceptions
- **User isolation**: Ensure data security through user_id validation
- **Type validation**: Pydantic validation on all inputs/outputs

## Usage Patterns

### Repository Initialization

```python
from services.platform.client_service import SupabaseClient
from repositories.domains.inventory_repo import MaterialRepository

client = SupabaseClient()
material_repo = MaterialRepository(client)
```

### Common Workflows

#### Stock Management
```python
# Check low stock
low_stock = await material_repo.find_below_alert_threshold(user_id)

# Update stock
await material_repo.update_stock_amount(material_id, new_amount, user_id)

# Record transaction
transaction = StockTransaction(...)
await stock_transaction_repo.create(transaction)
```

#### Order Processing
```python
# Get or create draft order
draft = await order_repo.find_active_draft_by_user(user_id)

# Add items
item = OrderItem(...)
await order_item_repo.create(item)

# Complete order
await order_repo.update(order_id, {"status": OrderStatus.COMPLETED})
```

#### Analytics
```python
# Daily summary
summary = await daily_summary_repo.find_by_date(date, user_id)

# Sales analysis
sales = await order_item_repo.get_menu_item_sales_summary(30, user_id)
```

## Business Service Layer

The business service layer provides high-level operations and workflows built on top of repositories.

### AnalyticsService

Provides comprehensive analytics and reporting capabilities.

```python
from services.business.analysis_service import AnalyticsService
```

#### Methods

##### `get_real_time_daily_stats(target_date: datetime, user_id: UUID) -> dict[str, Any]`

Returns real-time daily statistics including orders, revenue, and customer metrics.

**Example:**
```python
stats = await analytics.get_real_time_daily_stats(datetime.now(), user_id)
# Returns: {"total_orders": 45, "total_revenue": 1250.00, "avg_order_value": 27.78, ...}
```

##### `get_popular_items_ranking(days: int, user_id: UUID, limit: int = 10) -> list[dict[str, Any]]`

Returns ranking of most popular menu items by sales volume.

##### `calculate_average_preparation_time(days: int, user_id: UUID) -> float`

Calculates average order preparation time for performance analysis.

##### `get_material_consumption_analysis(days: int, user_id: UUID) -> list[dict[str, Any]]`

Analyzes material consumption patterns for inventory planning.

### InventoryService

Manages inventory operations including stock monitoring, purchasing, and material consumption.

```python
from services.business.inventory_service import InventoryService
```

#### Methods

##### `create_material(material_data: dict[str, Any], user_id: UUID) -> Material`

Creates a new material with validation and default settings.

**Example:**
```python
material = await inventory.create_material({
    "name": "Tomatoes",
    "unit": "kg",
    "current_stock": 50.0,
    "alert_threshold": 10.0,
    "critical_threshold": 5.0
}, user_id)
```

##### `get_stock_alerts_by_level(alert_level: str, user_id: UUID) -> list[Material]`

Returns materials requiring attention based on stock levels.

**Parameters:**
- `alert_level`: "critical" or "low"

##### `consume_materials_for_order(order_id: UUID, user_id: UUID) -> bool`

Automatically deducts materials from stock based on order recipes.

##### `record_purchase(purchase_data: dict[str, Any], items: list[dict[str, Any]], user_id: UUID) -> Purchase`

Records purchase and automatically updates material stock levels.

### MenuService

Handles menu management with real-time availability based on inventory.

```python
from services.business.menu_service import MenuService
```

#### Methods

##### `check_menu_availability(user_id: UUID) -> list[dict[str, Any]]`

Checks availability of all menu items based on current stock levels.

**Returns:** List with menu items and their availability status

##### `calculate_max_servings(menu_item_id: UUID, user_id: UUID) -> int`

Calculates maximum possible servings based on available ingredients.

##### `auto_update_menu_availability_by_stock(user_id: UUID) -> int`

Automatically updates menu item availability based on stock levels.

**Returns:** Number of items updated

### OrderService (CartService, OrderService, KitchenService)

Complete order workflow from cart management to kitchen operations.

```python
from services.business.order_service import CartService, OrderService, KitchenService
```

#### CartService Methods

##### `get_or_create_active_cart(user_id: UUID) -> Order`

Retrieves existing cart or creates new one.

##### `add_item_to_cart(user_id: UUID, menu_item_id: UUID, quantity: int) -> OrderItem`

Adds item to cart with stock validation.

##### `calculate_cart_total(cart_id: UUID) -> Decimal`

Calculates total amount for cart including all items.

#### OrderService Methods

##### `checkout_cart(cart_id: UUID, user_id: UUID) -> Order`

Converts cart to confirmed order and processes stock consumption.

##### `cancel_order(order_id: UUID, user_id: UUID) -> bool`

Cancels order and restores consumed materials to stock.

##### `get_order_history(user_id: UUID, page: int = 1, limit: int = 20, filters: dict = None) -> tuple[list[Order], int]`

Retrieves paginated order history with filtering options.

#### KitchenService Methods

##### `get_kitchen_queue(user_id: UUID) -> list[dict[str, Any]]`

Returns prioritized kitchen queue with preparation details.

##### `optimize_kitchen_queue(user_id: UUID) -> list[dict[str, Any]]`

Optimizes order sequence based on preparation time and priority.

##### `calculate_estimated_completion_time(order_id: UUID, user_id: UUID) -> datetime`

Predicts order completion time based on queue and preparation requirements.

## Service Integration Patterns

### Service Initialization

```python
from services.platform.client_service import SupabaseClient
from services.business.inventory_service import InventoryService
from repositories.domains.inventory_repo import MaterialRepository

client = SupabaseClient()
material_repo = MaterialRepository(client)
inventory_service = InventoryService(client)
```

### Common Workflows

#### Complete Order Processing
```python
# 1. Add items to cart
cart = await cart_service.get_or_create_active_cart(user_id)
item = await cart_service.add_item_to_cart(user_id, menu_item_id, quantity)

# 2. Checkout
order = await order_service.checkout_cart(cart.id, user_id)

# 3. Kitchen processing
queue = await kitchen_service.get_kitchen_queue(user_id)
completion_time = await kitchen_service.calculate_estimated_completion_time(order.id, user_id)
```

#### Inventory Management
```python
# Check alerts
critical_items = await inventory_service.get_stock_alerts_by_level("critical", user_id)

# Record purchase
purchase = await inventory_service.record_purchase(purchase_data, items, user_id)

# Update menu availability
updated = await menu_service.auto_update_menu_availability_by_stock(user_id)
```

#### Analytics Dashboard
```python
# Daily statistics
stats = await analytics_service.get_real_time_daily_stats(datetime.now(), user_id)

# Popular items
popular = await analytics_service.get_popular_items_ranking(30, user_id)

# Performance metrics
avg_prep_time = await analytics_service.calculate_average_preparation_time(7, user_id)
```