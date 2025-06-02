# Development Guide

This guide covers development workflows, coding standards, testing practices, and contribution guidelines for the Rin Stock Manager project.

## Development Workflow

### Branch Management

The project uses Git Flow with the following branches:

- **`main`**: Production-ready code
- **`dev`**: Development integration branch
- **`feature/*`**: New features
- **`bugfix/*`**: Bug fixes
- **`hotfix/*`**: Critical production fixes

### Feature Development

1. **Start from dev branch**:
   ```bash
   git checkout dev
   git pull origin dev
   ```

2. **Create feature branch**:
   ```bash
   git checkout -b feature/inventory-alerts
   ```

3. **Make changes and commit**:
   ```bash
   git add .
   git commit -m "feat: add inventory alert thresholds"
   ```

4. **Push and create PR**:
   ```bash
   git push origin feature/inventory-alerts
   # Create PR to dev branch
   ```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(inventory): add material stock alerts
fix(orders): resolve order number generation issue
docs: update API reference for filtering
refactor(repo): simplify query building logic
```

## Code Standards

### Python Style Guide

Follow **PEP 8** with these specific conventions:

#### Formatting
- **Line length**: 88 characters (Black default)
- **Indentation**: 4 spaces
- **Quotes**: Double quotes for strings
- **Imports**: Organized with isort

#### Naming Conventions
```python
# Classes: PascalCase
class MaterialRepository:

# Functions and variables: snake_case
def find_by_category_id():
async def get_user_materials():

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3
DEFAULT_PAGE_SIZE = 50

# Private methods: _leading_underscore
def _normalize_key():

# Type variables: PascalCase with suffix
M = TypeVar("M", bound=CoreBaseModel)
ID = TypeVar("ID")
```

#### Type Hints

Always use type hints:

```python
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

# Function signatures
async def find_materials(
    user_id: UUID,
    category_id: Optional[UUID] = None,
    limit: int = 100
) -> List[Material]:

# Class attributes
class Material:
    id: UUID
    name: str
    current_stock: Optional[Decimal] = None
```

#### Docstrings

Use Google-style docstrings:

```python
async def find_by_date_range(
    self, 
    date_from: datetime, 
    date_to: datetime, 
    user_id: UUID
) -> List[DailySummary]:
    """Retrieve summaries within a date range.
    
    Args:
        date_from: Start date (normalized to 00:00:00)
        date_to: End date (normalized to 23:59:59)
        user_id: User identifier for data isolation
        
    Returns:
        List of daily summaries sorted by date ascending
        
    Raises:
        ValueError: If date_from is after date_to
    """
```

### Repository Patterns

#### Standard Repository Structure

```python
from repositories.bases.crud_repo import CrudRepository
from models.inventory import Material

class MaterialRepository(CrudRepository[Material, UUID]):
    def __init__(self, client: SupabaseClient):
        super().__init__(client, Material)
    
    # Domain-specific methods
    async def find_by_category_id(
        self, 
        category_id: Optional[UUID], 
        user_id: UUID
    ) -> List[Material]:
        """Find materials by category with user isolation."""
        filters = {"user_id": (FilterOp.EQ, user_id)}
        if category_id is not None:
            filters["category_id"] = (FilterOp.EQ, category_id)
        return await self.find(filters=filters)
```

#### Error Handling

```python
from utils.errors import NotFoundError, ValidationError

async def get_material(self, material_id: UUID, user_id: UUID) -> Material:
    """Get material with proper error handling."""
    try:
        material = await self.get(material_id)
        if not material:
            raise NotFoundError(f"Material {material_id} not found")
        
        # Validate user access
        if material.user_id != user_id:
            raise ValidationError("Access denied")
            
        return material
    except Exception as e:
        logger.error(f"Error retrieving material {material_id}: {e}")
        raise
```

#### User Isolation

Always include user_id validation:

```python
async def find_user_materials(self, user_id: UUID) -> List[Material]:
    """All queries must include user_id for security."""
    return await self.find(filters={"user_id": (FilterOp.EQ, user_id)})
```

### Service Layer Patterns

#### Interface Definition

```python
from abc import ABC, abstractmethod

class InventoryServiceInterface(ABC):
    @abstractmethod
    async def get_low_stock_materials(self, user_id: UUID) -> List[Material]:
        """Get materials below alert threshold."""
        pass
    
    @abstractmethod
    async def adjust_stock(
        self, 
        material_id: UUID, 
        amount: Decimal, 
        reason: str, 
        user_id: UUID
    ) -> Material:
        """Adjust material stock with audit trail."""
        pass
```

#### Implementation

```python
class InventoryService(InventoryServiceInterface):
    def __init__(
        self, 
        material_repo: MaterialRepository,
        stock_transaction_repo: StockTransactionRepository
    ):
        self.material_repo = material_repo
        self.stock_transaction_repo = stock_transaction_repo
    
    async def adjust_stock(
        self, 
        material_id: UUID, 
        amount: Decimal, 
        reason: str, 
        user_id: UUID
    ) -> Material:
        """Implement with transaction logging."""
        # Update material stock
        material = await self.material_repo.update(
            material_id, 
            {"current_stock": amount}
        )
        
        # Log transaction
        transaction = StockTransaction(
            material_id=material_id,
            amount=amount,
            transaction_type="adjustment",
            reason=reason,
            user_id=user_id
        )
        await self.stock_transaction_repo.create(transaction)
        
        return material
```

## Testing

### Test Structure

```
tests/
├── conftest.py              # Pytest configuration
├── test_models/             # Model tests
├── test_repositories/       # Repository tests
├── test_services/           # Service tests
├── test_utils/              # Utility tests
└── fixtures/                # Test data
```

### Test Conventions

#### Test Naming

```python
class TestMaterialRepository:
    async def test_find_by_category_id_returns_filtered_materials(self):
        """Test should describe expected behavior."""
        pass
    
    async def test_find_by_category_id_with_none_returns_all_materials(self):
        """Test edge cases."""
        pass
    
    async def test_find_by_category_id_with_invalid_user_returns_empty(self):
        """Test security scenarios."""
        pass
```

#### Test Structure (AAA Pattern)

```python
async def test_create_material_success(self):
    """Test successful material creation."""
    # Arrange
    material_data = Material(
        name="Test Material",
        user_id=test_user_id,
        current_stock=Decimal("100.0")
    )
    
    # Act
    result = await material_repo.create(material_data)
    
    # Assert
    assert result is not None
    assert result.name == "Test Material"
    assert result.user_id == test_user_id
```

#### Fixtures

```python
# conftest.py
import pytest
from uuid import uuid4

@pytest.fixture
async def test_user_id():
    """Provide test user ID."""
    return uuid4()

@pytest.fixture
async def material_repo(supabase_client):
    """Provide material repository."""
    return MaterialRepository(supabase_client)

@pytest.fixture
async def sample_material(test_user_id):
    """Provide sample material data."""
    return Material(
        name="Test Material",
        user_id=test_user_id,
        current_stock=Decimal("50.0"),
        alert_threshold=Decimal("10.0")
    )
```

#### Mocking

```python
from unittest.mock import AsyncMock, patch

async def test_service_with_mocked_repository():
    """Test service logic with mocked dependencies."""
    # Arrange
    mock_repo = AsyncMock()
    mock_repo.find_below_alert_threshold.return_value = [sample_material]
    
    service = InventoryService(mock_repo)
    
    # Act
    low_stock = await service.get_low_stock_materials(user_id)
    
    # Assert
    assert len(low_stock) == 1
    mock_repo.find_below_alert_threshold.assert_called_once_with(user_id)
```

### Testing Commands

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_repositories/test_material_repo.py

# Run tests with coverage
poetry run pytest --cov=src --cov-report=html

# Run tests matching pattern
poetry run pytest -k "test_material"

# Run tests with verbose output
poetry run pytest -v

# Run tests and stop on first failure
poetry run pytest -x
```

## Development Tools

### Code Quality Tools

#### Black (Formatting)
```bash
# Format code
poetry run black src/ tests/

# Check formatting
poetry run black --check src/
```

#### isort (Import Sorting)
```bash
# Sort imports
poetry run isort src/ tests/

# Check import sorting
poetry run isort --check-only src/
```

#### Flake8 (Linting)
```bash
# Lint code
poetry run flake8 src/ tests/

# Lint with specific rules
poetry run flake8 --max-line-length=88 src/
```

#### mypy (Type Checking)
```bash
# Type check
poetry run mypy src/

# Type check with config
poetry run mypy --config-file mypy.ini src/
```

### Development Scripts

Create `scripts/dev.py`:

```python
#!/usr/bin/env python3
"""Development utility scripts."""

import asyncio
import subprocess
import sys
from pathlib import Path

def format_code():
    """Format code with black and isort."""
    subprocess.run(["poetry", "run", "black", "src/", "tests/"])
    subprocess.run(["poetry", "run", "isort", "src/", "tests/"])

def lint_code():
    """Lint code with flake8 and mypy."""
    result1 = subprocess.run(["poetry", "run", "flake8", "src/", "tests/"])
    result2 = subprocess.run(["poetry", "run", "mypy", "src/"])
    return result1.returncode == 0 and result2.returncode == 0

def run_tests():
    """Run tests with coverage."""
    subprocess.run([
        "poetry", "run", "pytest", 
        "--cov=src", 
        "--cov-report=html",
        "--cov-report=term-missing"
    ])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/dev.py [format|lint|test]")
        sys.exit(1)
    
    command = sys.argv[1]
    if command == "format":
        format_code()
    elif command == "lint":
        lint_code()
    elif command == "test":
        run_tests()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
```

## Debugging

### Logging Setup

```python
import logging
from utils.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Use in code
logger.info("Processing material update")
logger.warning("Stock below threshold")
logger.error("Database connection failed", exc_info=True)
```

### Debug Configuration

```python
# Development settings
if settings.debug:
    # Enable SQL logging
    logging.getLogger('supabase').setLevel(logging.DEBUG)
    
    # Enable detailed error traces
    import traceback
    traceback.print_exc()
```

### VS Code Debug Configuration

`.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        },
        {
            "name": "Python: Test File",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["${file}"],
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        }
    ]
}
```

## Performance Guidelines

### Database Optimization

```python
# Use batch operations
await repository.create_batch(items)

# Limit query results
await repository.find(limit=50, offset=0)

# Use specific filters
filters = {"status": (FilterOp.EQ, "active")}
await repository.find(filters=filters)

# Select only needed fields (when available)
await repository.find(select=["id", "name", "status"])
```

### Memory Management

```python
# Use generators for large datasets
async def process_materials():
    async for batch in material_repo.find_in_batches(batch_size=100):
        yield batch

# Clean up resources
async with AsyncContextManager() as resource:
    await process_data(resource)
```

## Documentation

### Code Documentation

- Use Google-style docstrings
- Document all public methods
- Include examples for complex functionality
- Keep documentation up to date

### API Documentation

- Update API reference when adding new methods
- Include usage examples
- Document error conditions
- Specify parameter types and return values

## Contributing

### Pull Request Process

1. **Fork the repository**
2. **Create feature branch from dev**
3. **Make changes following code standards**
4. **Add tests for new functionality**
5. **Update documentation**
6. **Run quality checks**:
   ```bash
   python scripts/dev.py format
   python scripts/dev.py lint
   python scripts/dev.py test
   ```
7. **Submit PR with description**

### PR Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass and coverage maintained
- [ ] Documentation updated
- [ ] No security vulnerabilities
- [ ] Breaking changes documented
- [ ] Performance impact considered

### Getting Help

- **Issues**: Create GitHub issue with details
- **Discussions**: Use GitHub discussions for questions
- **Documentation**: Check existing docs first
- **Code Review**: Tag maintainers for review

This development guide ensures consistent, high-quality code and efficient collaboration across the team.