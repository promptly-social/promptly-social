# Promptly Social Scribe - Backend API

A FastAPI-based backend service for the Promptly Social Scribe application, providing authentication and user management with Supabase integration.

## Features

- 🔐 **Authentication & Authorization**: Supabase Auth integration with JWT tokens
- 👤 **User Management**: Complete user lifecycle with profile management
- 🗄️ **Database**: PostgreSQL with SQLAlchemy ORM and async support
- 🧪 **Testing**: Comprehensive test suite with pytest
- 📊 **Monitoring**: Built-in health checks and logging
- 🔒 **Security**: CORS, security headers, and input validation
- 📋 **API Documentation**: Auto-generated OpenAPI/Swagger docs

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy
- **Authentication**: Supabase Auth
- **Testing**: pytest + pytest-asyncio
- **Validation**: Pydantic
- **Logging**: Loguru
- **Container**: Docker

## Project Structure

```bash
backend/
├── app/
│   ├── core/              # Core configuration and utilities
│   │   ├── config.py      # Application settings
│   │   ├── database.py    # Database connection and session management
│   │   └── security.py    # JWT and security utilities
│   ├── models/            # SQLAlchemy database models
│   │   └── user.py        # User and session models
│   ├── schemas/           # Pydantic request/response schemas
│   │   └── auth.py        # Authentication schemas
│   ├── routers/           # FastAPI route handlers
│   │   └── auth.py        # Authentication endpoints
│   ├── services/          # Business logic layer
│   │   └── auth.py        # Authentication service
│   ├── utils/             # Utility functions
│   │   └── supabase.py    # Supabase client wrapper
│   └── main.py            # FastAPI application setup
├── tests/                 # Test suite
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
└── env.example           # Environment variables template
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Supabase project

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**

   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

## Environment Configuration

Copy `env.example` to `.env` and configure the following:

### Required Variables

- `DATABASE_URL`: PostgreSQL connection string
- `DATABASE_URL_ASYNC`: Async PostgreSQL connection string
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Supabase anon key
- `SUPABASE_SERVICE_KEY`: Supabase service role key
- `JWT_SECRET_KEY`: Secret key for JWT signing

### Optional Variables

- `DEBUG`: Enable debug mode (default: False)
- `ENVIRONMENT`: Application environment (development/staging/production)
- `CORS_ORIGINS`: Allowed CORS origins
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)

## API Endpoints

### Authentication

- `POST /api/v1/auth/signup` - Register new user
- `POST /api/v1/auth/signin` - Sign in user
- `POST /api/v1/auth/signin/google` - Google OAuth sign in
- `POST /api/v1/auth/signout` - Sign out user
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/password/reset` - Request password reset

### System

- `GET /` - API information
- `GET /health` - Health check
- `GET /metrics` - Basic metrics
- `GET /docs` - API documentation (development only)

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

## Docker Deployment

### Build and run with Docker

```bash
# Build image
docker build -t promptly-backend .

# Run container
docker run -p 8000:8000 --env-file .env promptly-backend
```

### Docker Compose (recommended)

```yaml
version: "3.8"
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - postgres

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: promptly_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Session Management**: User session tracking with revocation
- **Password Security**: Bcrypt hashing with configurable rounds
- **CORS Protection**: Configurable cross-origin resource sharing
- **Security Headers**: X-Frame-Options, CSP, etc.
- **Input Validation**: Pydantic schema validation
- **Audit Logging**: Comprehensive request/response logging

## Logging

The application uses structured logging with Loguru:

- **Development**: Pretty console output
- **Production**: JSON format for log aggregation
- **Audit Logs**: All requests/responses logged for compliance
- **Error Tracking**: Detailed error logging with context

## Monitoring & Health Checks

- **Health Endpoint**: `/health` for load balancer checks
- **Metrics Endpoint**: `/metrics` for monitoring integration
- **Database Health**: Connection pool monitoring
- **Application Status**: Runtime information

## Database Migrations

The application uses SQLAlchemy with Alembic for migrations:

```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Run migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Development

### Code Style

- **Formatting**: Black code formatter
- **Linting**: Flake8 and pylint
- **Type Hints**: Full type annotation coverage
- **Docstrings**: Google-style documentation

### Pre-commit Hooks

Install pre-commit hooks for code quality:

```bash
pip install pre-commit
pre-commit install
```

## Production Deployment

### Environment Setup

1. Use environment-specific `.env` files
2. Enable production logging (JSON format)
3. Set up database connection pooling
4. Configure reverse proxy (nginx)
5. Set up SSL/TLS certificates

### Performance Optimization

- **Connection Pooling**: Configured for high concurrency
- **Async Operations**: Full async/await support
- **Caching**: Ready for Redis integration
- **Load Balancing**: Multiple worker processes

### Monitoring

Integrate with your monitoring stack:

- **Application Metrics**: Custom metrics endpoint
- **Health Checks**: Kubernetes-compatible health checks
- **Error Tracking**: Sentry integration ready
- **Log Aggregation**: Structured JSON logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- Check the API documentation at `/docs`
- Review the test suite for usage examples
- Open an issue for bug reports or feature requests
