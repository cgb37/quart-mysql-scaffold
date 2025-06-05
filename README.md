# Quart MySQL Scaffold

A production-ready web application scaffold built with Quart, MySQL, and Docker. This project follows software design best practices and provides a solid foundation for building scalable web applications.

## Features

- **🚀 High Performance**: Built with Quart for async performance
- **🔐 Secure by Default**: JWT authentication, rate limiting, and security headers
- **📊 Database Ready**: MySQL integration with SQLAlchemy ORM
- **🐳 Docker Ready**: Containerized development and deployment
- **📝 Monitoring & Logging**: Structured logging and error tracking
- **👩‍💻 Developer Experience**: Hot reload, testing setup, and documentation

## Tech Stack

- **Backend**: Python 3.12, Quart (async Flask alternative)
- **Database**: MySQL 5.7 with SQLAlchemy ORM
- **Cache**: Redis for sessions and caching
- **Frontend**: Tailwind CSS for styling
- **Infrastructure**: Docker & Docker Compose
- **Authentication**: JWT tokens with refresh token support
- **Testing**: Pytest with async support

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js (for npm scripts)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd quart-mysql-scaffold
   ```

2. **Copy environment variables**
   ```bash
   cp .env.example .env
   ```

3. **Update environment variables**
   Edit the `.env` file with your specific configuration:
   ```bash
   # Generate secure secret keys
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

4. **Start the application**
   ```bash
   npm run start
   ```

5. **Access the application**
   - Web Application: http://localhost:5000
   - API Documentation: http://localhost:5000/docs
   - MySQL: localhost:3306
   - Redis: localhost:6379

## Available Scripts

```bash
# Development
npm run dev          # Start with logs visible
npm run start        # Start in background
npm run stop         # Stop all services
npm run restart      # Restart all services

# Logs
npm run logs         # View all logs
npm run logs:web     # View web service logs
npm run logs:db      # View database logs

# Database
npm run migrate      # Run database migrations
npm run seed         # Seed database with sample data

# Utilities
npm run shell:web    # Access web container shell
npm run shell:db     # Access MySQL shell
npm run test         # Run tests
npm run build        # Build containers
npm run rebuild      # Rebuild containers from scratch
npm run clean        # Clean up containers and volumes
```

## Project Structure

```
quart-mysql-scaffold/
├── app.py                      # Application entry point
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Multi-container setup
├── package.json               # NPM scripts
├── .env.example               # Environment variables template
├── src/
│   ├── config.py              # Application configuration
│   ├── extensions.py          # Flask extensions setup
│   ├── middleware.py          # Custom middleware
│   ├── routes/                # Route blueprints
│   │   ├── __init__.py
│   │   ├── api.py             # API endpoints
│   │   ├── auth.py            # Authentication routes
│   │   └── web.py             # Web page routes
│   └── services/              # Business logic services
│       ├── auth_service.py    # Authentication service
│       ├── database_service.py # Database operations
│       ├── error_handler.py   # Error handling
│       └── logging_service.py # Logging configuration
├── templates/                 # Jinja2 templates
│   ├── base.html             # Base template
│   ├── index.html            # Home page
│   └── auth/                 # Authentication templates
├── static/                   # Static files
├── tests/                    # Test files
├── docker/                   # Docker configuration files
│   ├── nginx/                # Nginx configuration
│   └── mysql/                # MySQL initialization
└── logs/                     # Application logs
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - User logout
- `GET /auth/me` - Get current user info
- `POST /auth/change-password` - Change password

### Users
- `GET /api/v1/users` - Get all users
- `POST /api/v1/users` - Create new user
- `GET /api/v1/users/{id}` - Get specific user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user
- `GET /api/v1/search/users` - Search users

### System
- `GET /health` - Health check
- `GET /api/v1/status` - API status

## Configuration

The application uses environment variables for configuration. Key settings include:

### Database
```bash
DB_HOST=db
DB_PORT=3306
DB_NAME=quart_db
DB_USER=quart_user
DB_PASSWORD=quart_password
```

### Security
```bash
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_EXPIRES=3600
```

### Features
```bash
RATELIMIT_ENABLED=true
SECURITY_HEADERS=true
LOG_LEVEL=INFO
```

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: Configurable rate limits per endpoint
- **Security Headers**: CORS, CSP, XSS protection
- **Password Hashing**: Bcrypt for secure password storage
- **Token Blacklisting**: Logout invalidates tokens
- **Input Validation**: Request validation and sanitization

## Development

### Adding New Features

1. **Create new routes** in `src/routes/`
2. **Add business logic** in `src/services/`
3. **Update configuration** in `src/config.py`
4. **Add tests** in `tests/`

### Database Migrations

```bash
# Create migration
docker-compose exec web alembic revision --autogenerate -m "Description"

# Run migrations
npm run migrate
```

### Testing

```bash
# Run all tests
npm run test

# Run specific test file
docker-compose exec web pytest tests/test_auth.py

# Run with coverage
docker-compose exec web pytest --cov=src tests/
```

## Deployment

### Production Deployment

1. **Update environment variables** for production
2. **Set QUART_ENV=production**
3. **Use production database** settings
4. **Configure reverse proxy** (Nginx included)
5. **Set up SSL certificates**

### Docker Production

```bash
# Build production image
docker build -t quart-app:latest .

# Run with production compose
docker-compose -f docker-compose.prod.yml up -d
```

## Monitoring

### Logs
- Application logs: `logs/app.log`
- Access logs via: `npm run logs`
- Structured JSON logging for production

### Health Checks
- Application: `GET /health`
- Database: Included in health check
- Redis: Included in health check

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- Documentation: http://localhost:5000/docs
- Issues: Create an issue on GitHub
- Email: support@quartapp.com

## Changelog

### v1.0.0
- Initial release
- Basic CRUD operations
- JWT authentication
- Docker setup
- Rate limiting
- Logging and monitoring