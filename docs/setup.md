# Setup and Installation Guide

This guide walks you through setting up the Rin Stock Manager development environment and preparing for deployment.

## Prerequisites

### System Requirements

- **Python**: 3.12 or higher
- **Poetry**: For dependency management
- **Git**: For version control
- **Supabase Account**: For database and authentication

### Platform Support

- **Primary**: Linux, macOS
- **Secondary**: Windows (with WSL recommended)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd rin-stock-manager
```

### 2. Install Poetry

If you don't have Poetry installed:

```bash
# Using curl
curl -sSL https://install.python-poetry.org | python3 -

# Using pip
pip install poetry

# Verify installation
poetry --version
```

### 3. Install Dependencies

```bash
# Install all dependencies
poetry install

# Activate virtual environment
poetry shell
```

### 4. Environment Configuration

#### Create Environment File

```bash
cp .env.example .env
```

#### Configure Environment Variables

Edit `.env` with your settings:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# Optional: Development Settings
DEBUG=true
LOG_LEVEL=INFO
```

### 5. Supabase Setup

#### Create Supabase Project

1. Go to [Supabase](https://supabase.com)
2. Create a new project
3. Note your project URL and anon key

#### Database Schema

The application expects specific database tables. Create them using SQL:

```sql
-- Users table (if not using Supabase Auth)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Materials table
CREATE TABLE materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR NOT NULL,
    category_id UUID REFERENCES material_categories(id),
    current_stock DECIMAL(10,2) DEFAULT 0,
    alert_threshold DECIMAL(10,2),
    critical_threshold DECIMAL(10,2),
    unit VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Material Categories
CREATE TABLE material_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR NOT NULL,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Menu Items
CREATE TABLE menu_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR NOT NULL,
    description TEXT,
    price DECIMAL(10,2),
    category_id UUID REFERENCES menu_categories(id),
    is_available BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Menu Categories
CREATE TABLE menu_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR NOT NULL,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Orders
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    order_number VARCHAR UNIQUE NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'draft',
    total_amount DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Order Items
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id),
    menu_item_id UUID NOT NULL REFERENCES menu_items(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Recipes
CREATE TABLE recipes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    menu_item_id UUID NOT NULL REFERENCES menu_items(id),
    material_id UUID NOT NULL REFERENCES materials(id),
    required_amount DECIMAL(10,3) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Purchases
CREATE TABLE purchases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    supplier_name VARCHAR,
    total_amount DECIMAL(10,2),
    purchase_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Purchase Items
CREATE TABLE purchase_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_id UUID NOT NULL REFERENCES purchases(id),
    material_id UUID NOT NULL REFERENCES materials(id),
    quantity DECIMAL(10,3) NOT NULL,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Stock Adjustments
CREATE TABLE stock_adjustments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    material_id UUID NOT NULL REFERENCES materials(id),
    adjustment_type VARCHAR NOT NULL,
    amount DECIMAL(10,3) NOT NULL,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Stock Transactions
CREATE TABLE stock_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    material_id UUID NOT NULL REFERENCES materials(id),
    transaction_type VARCHAR NOT NULL,
    amount DECIMAL(10,3) NOT NULL,
    reference_type VARCHAR,
    reference_id UUID,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Daily Summaries
CREATE TABLE daily_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    summary_date DATE NOT NULL,
    total_orders INTEGER DEFAULT 0,
    total_revenue DECIMAL(10,2) DEFAULT 0,
    total_items_sold INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, summary_date)
);
```

#### Row Level Security (RLS)

Enable RLS and create policies:

```sql
-- Enable RLS on all tables
ALTER TABLE materials ENABLE ROW LEVEL SECURITY;
ALTER TABLE material_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE menu_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE menu_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE recipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchases ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE stock_adjustments ENABLE ROW LEVEL SECURITY;
ALTER TABLE stock_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_summaries ENABLE ROW LEVEL SECURITY;

-- Create policies (example for materials table)
CREATE POLICY "Users can view own materials" 
ON materials FOR SELECT 
USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can create own materials" 
ON materials FOR INSERT 
WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own materials" 
ON materials FOR UPDATE 
USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete own materials" 
ON materials FOR DELETE 
USING (auth.uid()::text = user_id::text);

-- Repeat similar policies for all tables
```

### 6. Verify Installation

```bash
# Run tests
poetry run pytest

# Check dependencies
poetry show

# Verify Python version
python --version
```

## Development Setup

### IDE Configuration

#### VS Code

Recommended extensions:
- Python
- Pylance
- Python Docstring Generator
- Ruff (for linting)

#### Settings

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"]
}
```

### Git Hooks

Set up pre-commit hooks:

```bash
# Install pre-commit
poetry add --group dev pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3.12
  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
        args: ["--profile", "black"]
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
EOF

# Install hooks
pre-commit install
```

## Testing Setup

### Test Configuration

The project uses pytest with async support:

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src

# Run specific test file
poetry run pytest tests/test_repositories.py

# Run with verbose output
poetry run pytest -v
```

### Test Environment

Create a test environment file `.env.test`:

```env
SUPABASE_URL=your_test_supabase_url
SUPABASE_ANON_KEY=your_test_supabase_key
```

## Deployment Preparation

### Production Environment

1. **Environment Variables**:
   ```env
   SUPABASE_URL=production_url
   SUPABASE_ANON_KEY=production_key
   DEBUG=false
   LOG_LEVEL=WARNING
   ```

2. **Dependencies**:
   ```bash
   # Install production dependencies only
   poetry install --only=main
   ```

3. **Build Application**:
   ```bash
   # Build for distribution
   poetry build
   ```

### Docker Setup (Optional)

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only=main

# Copy application
COPY src/ ./src/

# Set environment
ENV PYTHONPATH=/app/src

# Run application
CMD ["python", "-m", "src.main"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
    volumes:
      - ./data:/app/data
    ports:
      - "8000:8000"
```

## Troubleshooting

### Common Issues

#### Poetry Installation
```bash
# If Poetry command not found
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
which poetry
```

#### Python Version
```bash
# Check current Python version
python --version

# Install specific Python version (using pyenv)
pyenv install 3.12.0
pyenv global 3.12.0
```

#### Supabase Connection
```bash
# Test connection
python -c "
from utils.config import settings
print(f'URL: {settings.supabase_url}')
print(f'Key: {settings.supabase_anon_key[:10]}...')
"
```

#### Dependencies
```bash
# Clear cache and reinstall
poetry cache clear --all pypi
poetry install --no-cache
```

### Environment Issues

#### Virtual Environment
```bash
# Check active environment
poetry env info

# Remove and recreate
poetry env remove python
poetry install
```

#### Path Issues
```bash
# Add to shell profile (.bashrc, .zshrc)
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Database Issues

#### Connection Problems
- Verify Supabase URL and key
- Check project status in Supabase dashboard
- Ensure RLS policies are correctly configured

#### Migration Issues
- Check table creation scripts
- Verify foreign key relationships
- Ensure UUID extensions are enabled

## Next Steps

1. **Read [Development Guide](./development.md)** for contribution guidelines
2. **Check [Architecture Guide](./architecture.md)** for system design
3. **Review [API Reference](./api-reference.md)** for implementation details
4. **Run tests** to verify everything works
5. **Start developing** your features

## Support

If you encounter issues:

1. Check this troubleshooting section
2. Review the logs for error details
3. Verify environment configuration
4. Create an issue with detailed information