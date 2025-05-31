# Rin Stock Manager

Restaurant inventory management system - A Python application providing efficient inventory tracking, order management, and analytics capabilities.

## 🚀 Key Features

- **📦 Inventory Management**: Track materials, categories, and recipes
- **🛒 Order Processing**: Handle orders with draft, active, and completed states
- **📊 Analytics**: Daily summaries and business insights
- **🍽️ Menu Management**: Organize menu items and categories
- **💾 Offline Support**: Queue operations when offline, sync when reconnected
- **🔒 Data Security**: User-isolated data with proper authentication

## 🛠️ Technology Stack

- **Backend**: Supabase (PostgreSQL) for data persistence
- **Frontend**: Flet framework for desktop UI
- **Architecture**: Clean Architecture with Repository/Service pattern
- **Language**: Python 3.12+
- **Dependencies**: Poetry for dependency management

## ⚡ Quick Start

### Prerequisites

- Python 3.12 or higher
- Poetry package manager
- Supabase account and project

### Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd rin-stock-manager

# 2. Install dependencies
poetry install
poetry shell

# 3. Configure environment
cp .env.example .env
# Edit .env with your Supabase credentials

# 4. Run tests
pytest
```

For detailed setup instructions, see the [Setup Guide](./setup.md).

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Setup Guide](./setup.md) | Installation and configuration instructions |
| [Architecture Guide](./architecture.md) | System design details |
| [API Reference](./api-reference.md) | Repository/Service API documentation |
| [Development Guide](./development.md) | Development workflow and contribution guidelines |

## 🏗️ Project Status

### ✅ Completed
- Repository layer with full CRUD operations
- Advanced filtering system with AND/OR logic
- All domain repositories (inventory, menu, order, stock, analytics)
- Business service layer with comprehensive functionality
- Model definitions and validation
- Configuration management

### 🚧 In Progress
- UI development with Flet
- Offline functionality integration
- Comprehensive test suite

### 📋 Planned
- Business service API documentation
- Deployment guides
- Performance optimization

## 🏛️ Architecture Overview

The system follows Clean Architecture principles ensuring clear separation of concerns:

```
┌─────────────────────────────────────────┐
│              UI Layer (Flet)            │  ← Presentation
├─────────────────────────────────────────┤
│           Service Layer                 │  ← Business Logic
├─────────────────────────────────────────┤
│         Repository Layer                │  ← Data Access
├─────────────────────────────────────────┤
│           Model Layer                   │  ← Domain Models
├─────────────────────────────────────────┤
│     Infrastructure (Supabase)          │  ← External Services
└─────────────────────────────────────────┘
```

### Key Components

- **Repository Pattern**: Generic CRUD operations with advanced filtering
- **Business Services**: Complete business logic layer with analytics and workflow management
- **Filtering System**: Support for complex AND/OR queries
- **Offline Support**: FileQueue + ReconnectWatcher for connectivity issues
- **Configuration**: Pydantic-based environment settings

## 🔧 Development

### Basic Commands

```bash
# Environment setup
poetry install && poetry shell

# Testing
pytest                     # Run all tests
pytest --cov=src          # Run with coverage
pytest -v                 # Verbose output

# Code quality (planned)
black src/ tests/          # Code formatting
isort src/ tests/          # Import sorting
flake8 src/ tests/         # Linting
mypy src/                  # Type checking
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

See the [Development Guide](./development.md) for detailed instructions.

## 📄 License

[License information to be added]

## 🆘 Support

For questions or issues, please create an issue in the repository.