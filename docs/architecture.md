# Architecture Guide

This document provides a comprehensive overview of the Rin Stock Manager architecture, design patterns, and implementation details.

## Overview

The Rin Stock Manager implements a layered module structure with separation of concerns. The system organizes code into distinct layers with defined responsibilities and dependencies.

## System Layers

```
┌─────────────────────────────────────────┐
│              UI Layer (Flet)            │  ← User Interface
├─────────────────────────────────────────┤
│           Service Layer                 │  ← Business Logic
├─────────────────────────────────────────┤
│         Repository Layer                │  ← Data Access
├─────────────────────────────────────────┤
│           Model Layer                   │  ← Data Models
├─────────────────────────────────────────┤
│     Infrastructure (Supabase)          │  ← Database
└─────────────────────────────────────────┘
```

### 1. Model Layer (`src/models/`)

Data models using Pydantic for validation and serialization.

**Base Model:**
```python
class CoreBaseModel(BaseModel, ABC):
    @classmethod
    @abstractmethod
    def __table_name__(cls) -> str: ...
```

**Key Features:**
- Pydantic validation and serialization
- Abstract table name mapping
- Type safety with Python typing
- Immutable data structures

**Domain Models:**
- **Analytics**: `DailySummary` - Daily business metrics
- **Inventory**: `Material`, `MaterialCategory`, `Recipe` - Stock management
- **Menu**: `MenuItem`, `MenuCategory` - Menu organization
- **Order**: `Order`, `OrderItem` - Order processing
- **Stock**: `Purchase`, `PurchaseItem`, `StockAdjustment`, `StockTransaction` - Stock operations

### 2. Repository Layer (`src/repositories/`)

The repository layer abstracts data access and provides a consistent interface for CRUD operations.

#### Base Repository (`src/repositories/bases/crud_repo.py`)

Generic repository with full CRUD operations:

```python
class CrudRepository(ABC, Generic[M, ID]):
    # CRUD operations
    async def create(self, entity: M) -> M | None
    async def get(self, key: ID | PKMap) -> M | None
    async def update(self, key: ID | PKMap, patch: Mapping[str, Any]) -> M | None
    async def delete(self, key: ID | PKMap) -> None
    async def exists(self, key: ID | PKMap) -> bool
    
    # Query operations
    async def list(self, *, limit: int = 100, offset: int = 0) -> list[M]
    async def find(self, filters: Filter | None = None, ...) -> list[M]
    async def count(self, filters: Filter | None = None) -> int
```

**Key Features:**
- Generic type support for models and IDs
- Composite primary key support
- Advanced filtering system
- Automatic Pydantic validation
- Pagination support

#### Domain Repositories (`src/repositories/domains/`)

Specialized repositories for each domain:

- **`analysis_repo.py`**: Analytics and reporting
- **`inventory_repo.py`**: Material and recipe management
- **`menu_repo.py`**: Menu item and category management
- **`order_repo.py`**: Order processing and tracking
- **`stock_repo.py`**: Purchase and stock transaction management

### 3. Filtering System

Advanced filtering system supporting complex queries:

#### Filter Types

**Simple Filters (AND logic):**
```python
filters = {
    "status": (FilterOp.EQ, "active"),
    "category": (FilterOp.EQ, "electronics")
}
```

**OR Conditions:**
```python
from utils.filters import OrCondition

or_filter = OrCondition([
    {"status": (FilterOp.EQ, "active")},
    {"status": (FilterOp.EQ, "low_stock")}
])
```

**Complex Conditions:**
```python
complex_filter = ComplexCondition([
    AndCondition({"supplier_id": (FilterOp.EQ, 1)}),
    OrCondition([
        {"status": (FilterOp.EQ, "active")},
        {"status": (FilterOp.EQ, "pending")}
    ])
], operator="and")
```

#### Filter Operations (`constants/types.py`)

```python
class FilterOp(Enum):
    EQ = "eq"           # Equal
    NEQ = "neq"         # Not equal
    GT = "gt"           # Greater than
    GTE = "gte"         # Greater than or equal
    LT = "lt"           # Less than
    LTE = "lte"         # Less than or equal
    LIKE = "like"       # Pattern matching
    ILIKE = "ilike"     # Case-insensitive pattern matching
    IN = "in_"          # In list
    IS = "is_"          # Is null/not null
```

### 4. Service Layer (`src/services/`)

The service layer contains business logic and orchestrates repository operations.

#### Platform Services (`src/services/platform/`)

Infrastructure services for external integrations:

- **`client_service.py`**: Supabase client management
- **`file_queue.py`**: Offline operation queuing
- **`reconnect_watcher.py`**: Connectivity monitoring

#### Business Services (`src/services/business/`)

Domain-specific business logic (fully implemented with comprehensive functionality):

- **`analysis_service.py`**: Analytics and reporting with real-time statistics, popular items ranking, performance metrics, and material consumption analysis
- **`inventory_service.py`**: Complete inventory management including material creation, stock monitoring, automatic consumption/restoration, and purchase recording
- **`menu_service.py`**: Menu management with real-time availability checking, search functionality, and stock-based updates
- **`order_service.py`**: Complete order workflow with three service classes:
  - **CartService**: Shopping cart management with validation
  - **OrderService**: Order lifecycle and history management
  - **KitchenService**: Kitchen operations and queue optimization

### 5. Offline Support Architecture

The system supports offline operations through a queuing mechanism:

#### FileQueue (`src/services/platform/file_queue.py`)

- Queues write operations when offline
- Automatic garbage collection of old operations
- Persistent storage using local files
- Thread-safe operations

#### ReconnectWatcher (`src/services/platform/reconnect_watcher.py`)

- Monitors network connectivity
- Triggers queue processing on reconnection
- Configurable retry strategies
- Event-driven architecture

**Offline Workflow:**
```
1. Operation requested → 2. Check connectivity
                      ↓
3. If online: Execute directly
   If offline: Queue operation
                      ↓
4. On reconnection → 5. Process queued operations
```

### 6. Configuration Management

Environment-based configuration using Pydantic Settings:

```python
class Settings(BaseSettings):
    supabase_url: str
    supabase_anon_key: str
    
    class Config:
        env_file = ".env"
```

**Features:**
- Type validation
- Environment variable support
- Default values
- Nested configuration objects

## Design Patterns

### 1. Repository Pattern

Provides data access operations with consistent interfaces.

**Implementation:**
- Generic CRUD operations
- Centralized query logic
- Consistent error handling
- Database abstraction layer

### 2. Generic Programming

Type-safe generic repositories and services:

```python
class CrudRepository(Generic[M, ID]):
    # M: Model type
    # ID: Primary key type
```

### 3. Dependency Injection

Services receive repository instances through constructor parameters:

```python
class InventoryService:
    def __init__(self, material_repo: MaterialRepository):
        self.material_repo = material_repo
```

### 4. Event-Driven Implementation

Offline support implements connectivity monitoring and queue processing through events.

## Data Flow

### Read Operations
```
UI → Service → Repository → Supabase → Model → Service → UI
```

### Write Operations (Online)
```
UI → Service → Repository → Supabase → Model → Service → UI
```

### Write Operations (Offline)
```
UI → Service → FileQueue → Local Storage
                    ↓
ReconnectWatcher → Queue Processing → Repository → Supabase
```

## Security Architecture

### User Isolation

All database operations include user-specific filtering:

```python
async def find_materials(self, user_id: str, filters: Filter = None):
    # Always include user_id in queries
    user_filter = {"user_id": (FilterOp.EQ, user_id)}
    # Combine with additional filters...
```

### Data Validation

- Pydantic models ensure data integrity
- Type validation at all layers
- Business rule validation in services

## Performance Considerations

### Query Optimization

- Efficient filtering at database level
- Pagination for large datasets
- Selective field querying
- Connection pooling

### Caching Strategy

- Model-level caching (planned)
- Query result caching (planned)
- Offline data persistence

### Scalability

- Stateless service design
- Horizontal scaling capability
- Async operations throughout

## Technology Decisions

### Database: Supabase (PostgreSQL)

**Reasons:**
- PostgreSQL reliability and performance
- Built-in authentication
- Real-time capabilities
- RESTful API
- Offline-first architecture support

### UI Framework: Flet

**Reasons:**
- Python-native development
- Cross-platform deployment
- Modern UI components
- Hot reload during development

### Validation: Pydantic

**Reasons:**
- Type safety
- Automatic validation
- JSON serialization
- Performance
- IDE support

## Future Enhancements

### Planned Features

1. **Real-time Updates**: WebSocket integration for live data
2. **Caching Layer**: Redis integration for performance
3. **Event Sourcing**: Audit trail and state reconstruction
4. **Microservices**: Service decomposition for scalability
5. **API Gateway**: External API access and rate limiting

### Migration Strategies

- Database schema versioning
- Backward compatibility maintenance
- Progressive feature rollout
- Data migration utilities

This architecture provides a solid foundation for a scalable, maintainable restaurant stock management system while maintaining flexibility for future enhancements.