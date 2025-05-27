# Rin Stock Manager

A Python-based restaurant stock management system designed for efficient inventory tracking, order management, and analytics. Built with modern architecture patterns and offline-first capabilities.

## Features

- **Inventory Management**: Track materials, categories, and recipes
- **Order Processing**: Handle orders with draft, active, and completed states
- **Stock Control**: Manage purchases, adjustments, and transactions
- **Analytics**: Daily summaries and business insights
- **Menu Management**: Organize menu items and categories
- **Offline Support**: Queue operations when offline, sync when reconnected
- **Data Security**: User-isolated data with proper authentication

## Technology Stack

- **Backend**: Supabase (PostgreSQL) for data persistence
- **Frontend**: Flet framework for desktop UI
- **Architecture**: Clean Architecture with Repository/Service pattern
- **Language**: Python 3.12+
- **Dependencies**: Poetry for dependency management

## Quick Start

### Prerequisites

- Python 3.12 or higher
- Poetry package manager
- Supabase account and project

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd rin-stock-manager
```

2. Install dependencies:
```bash
poetry install
poetry shell
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

4. Run tests:
```bash
pytest
```

## Architecture

The project follows Clean Architecture principles with clear separation of concerns:

- **Models**: Pydantic models with database table mapping
- **Repositories**: Data access layer with CRUD operations
- **Services**: Business logic layer (in development)
- **Utils**: Configuration, error handling, and utilities

### Key Components

- **Repository Pattern**: Generic CRUD operations with advanced filtering
- **Filtering System**: Support for complex AND/OR queries
- **Offline Support**: FileQueue + ReconnectWatcher for connectivity issues
- **Configuration**: Environment-based settings with Pydantic

## Documentation

- [Architecture Guide](./architecture.md) - Detailed system design
- [API Reference](./api-reference.md) - Repository and service documentation
- [Setup Guide](./setup.md) - Installation and configuration
- [Development Guide](./development.md) - Contributing and development workflow

## Project Status

### Completed ✅
- Repository layer with full CRUD operations
- Advanced filtering system with OR/AND logic
- All domain repositories (inventory, menu, order, stock, analytics)
- Model definitions and validation
- Configuration management

### In Progress 🚧
- Business service layer
- UI development with Flet
- Offline functionality integration

### Planned 📋
- Comprehensive test suite
- API documentation
- Deployment guides

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

[License information to be added]

## Support

For questions or issues, please create an issue in the repository.