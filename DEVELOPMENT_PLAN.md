# Development Plan: Azure-Ready Quart Application

## Overview

This plan outlines the transformation of the current Quart MySQL scaffold to be Azure Web App for Linux ready, removing Redis and Nginx dependencies, implementing dual authentication strategies, and restructuring the codebase following Azure best practices.

## Goals

- ✅ Remove Redis dependency completely
- ✅ Remove Nginx (Azure handles load balancing)
- ✅ Implement Quart-Auth for local development
- ✅ Implement Quart-SAML for Azure production
- ✅ Restructure project following modular best practices
- ✅ Ensure Azure Web App for Linux compatibility

## Phase 1: Dependency Removal & Core Restructuring

### 1.1 Remove Redis Dependencies

**Files to Modify:**
- `src/config.py` - Remove Redis configuration
- `src/extensions.py` - Remove Redis initialization
- `src/services/auth_service.py` - Replace Redis token storage with database
- `requirements.txt` - Remove Redis packages
- `docker-compose.yml` - Remove Redis service
- Health check endpoints

**Tasks:**
- [ ] Replace Redis session storage with SQLAlchemy-based sessions
- [ ] Implement database-based token blacklist
- [ ] Remove rate limiting or implement memory-based alternative
- [ ] Update health checks to remove Redis dependency

### 1.2 Remove Nginx Dependencies

**Files to Remove/Modify:**
- `docker/nginx/` directory
- `docker-compose.yml` - Remove Nginx service
- Update port configurations

**Tasks:**
- [ ] Remove Nginx configuration files
- [ ] Update Docker Compose to expose Quart directly
- [ ] Configure Quart for direct external access
- [ ] Update CORS settings for direct access

### 1.3 Project Restructuring

**New Project Structure:**
```
quart-mysql-scaffold/
├── app.py                          # Application entry point
├── requirements/                   # Split requirements by environment
│   ├── base.txt                   # Base dependencies
│   ├── development.txt            # Development dependencies
│   └── production.txt             # Production dependencies
├── azure-requirements.txt          # Azure-specific requirements
├── startup.sh                     # Azure startup script
├── .env.example                   # Environment variables template
├── .env.development               # Development environment
├── .env.production                # Production environment template
├── docker-compose.yml             # Local development only
├── Dockerfile                     # Containerization
├── package.json                   # NPM scripts
├── azure.yaml                     # Azure Developer CLI configuration
├── src/
│   ├── __init__.py
│   ├── config/                    # Configuration management
│   │   ├── __init__.py
│   │   ├── base.py               # Base configuration
│   │   ├── development.py        # Development config
│   │   ├── production.py         # Production config
│   │   └── azure.py              # Azure-specific config
│   ├── core/                     # Core application components
│   │   ├── __init__.py
│   │   ├── extensions.py         # Extension initialization
│   │   ├── middleware.py         # Custom middleware
│   │   ├── security.py           # Security utilities
│   │   └── database.py           # Database configuration
│   ├── modules/                  # Feature modules
│   │   ├── __init__.py
│   │   ├── auth/                 # Authentication module
│   │   │   ├── __init__.py
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   └── endpoints.py
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user.py
│   │   │   │   ├── session.py
│   │   │   │   └── token_blacklist.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth_routes.py
│   │   │   │   └── saml_routes.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth_service.py
│   │   │   │   ├── local_auth.py
│   │   │   │   ├── saml_service.py
│   │   │   │   └── session_service.py
│   │   │   └── schemas/
│   │   │       ├── __init__.py
│   │   │       ├── auth_schemas.py
│   │   │       └── user_schemas.py
│   │   ├── users/                # User management module
│   │   │   ├── __init__.py
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   └── endpoints.py
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   └── user_profile.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   └── user_routes.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   └── user_service.py
│   │   │   └── schemas/
│   │   │       ├── __init__.py
│   │   │       └── user_schemas.py
│   │   └── health/               # Health check module
│   │       ├── __init__.py
│   │       ├── api/
│   │       │   ├── __init__.py
│   │       │   └── endpoints.py
│   │       ├── routes/
│   │       │   ├── __init__.py
│   │       │   └── health_routes.py
│   │       └── services/
│   │           ├── __init__.py
│   │           └── health_service.py
│   ├── shared/                   # Shared utilities
│   │   ├── __init__.py
│   │   ├── exceptions.py         # Custom exceptions
│   │   ├── validators.py         # Input validation
│   │   ├── decorators.py         # Custom decorators
│   │   ├── constants.py          # Application constants
│   │   └── utils.py              # Utility functions
│   └── utils/                    # Legacy utilities (to be migrated)
│       ├── __init__.py
│       └── decorators.py
├── infra/                        # Azure infrastructure (Bicep)
│   ├── main.bicep               # Main infrastructure template
│   ├── main.parameters.json     # Parameters file
│   ├── modules/
│   │   ├── web-app.bicep        # Azure Web App configuration
│   │   ├── database.bicep       # Azure Database for MySQL
│   │   ├── key-vault.bicep      # Azure Key Vault
│   │   └── app-insights.bicep   # Application Insights
│   └── README.md                # Infrastructure documentation
├── templates/                    # Jinja2 templates
│   ├── base.html
│   ├── index.html
│   └── auth/
│       ├── login.html
│       └── saml_redirect.html
├── static/                       # Static files
├── tests/                        # Test files
│   ├── __init__.py
│   ├── conftest.py              # Pytest configuration
│   ├── unit/                    # Unit tests
│   │   ├── __init__.py
│   │   ├── test_auth/
│   │   │   ├── __init__.py
│   │   │   ├── test_local_auth.py
│   │   │   ├── test_saml_auth.py
│   │   │   └── test_auth_service.py
│   │   └── test_users/
│   │       ├── __init__.py
│   │       └── test_user_service.py
│   ├── integration/             # Integration tests
│   │   ├── __init__.py
│   │   ├── test_api.py
│   │   └── test_auth_flow.py
│   └── fixtures/                # Test fixtures
│       ├── __init__.py
│       └── auth_fixtures.py
├── migrations/                   # Database migrations
│   └── versions/
├── docs/                        # Documentation
│   ├── deployment.md
│   ├── authentication.md
│   └── api.md
└── scripts/                     # Utility scripts
    ├── generate_secrets.py
    ├── setup_azure.py
    └── migrate_data.py
```

## Phase 2: Authentication Implementation

### 2.1 Local Development Authentication (Quart-Auth)

**New Dependencies:**
```txt
# requirements/development.txt
quart-auth==0.7.0
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
```

**Implementation:**
- JWT-based authentication for API endpoints
- Session-based authentication for web interface
- Password hashing with bcrypt
- Token refresh mechanism
- Role-based access control

### 2.2 Azure Production Authentication (Quart-SAML)

**New Dependencies:**
```txt
# requirements/production.txt
quart-saml==0.2.0
xmlsec==1.3.13
lxml==4.9.3
```

**Implementation:**
- SAML 2.0 integration with Azure AD
- Automatic user provisioning
- Role mapping from SAML attributes
- Single Sign-On (SSO) support
- Multi-tenant support

### 2.3 Authentication Factory Pattern

**Key Files:**
- `src/core/auth_factory.py` - Authentication factory
- `src/modules/auth/services/auth_interface.py` - Authentication interface
- `src/modules/auth/services/local_auth.py` - Local authentication implementation
- `src/modules/auth/services/saml_service.py` - SAML authentication implementation

## Phase 3: Azure Integration

### 3.1 Azure Web App Configuration

**Azure-specific Files:**
```bash
# azure-requirements.txt
quart==0.20.0
hypercorn==0.16.0
gunicorn==21.2.0
SQLAlchemy==2.0.23
aiomysql==0.2.0
azure-identity==1.15.0
azure-keyvault-secrets==4.7.0
azure-monitor-opentelemetry==1.2.0
quart-saml==0.2.0
```

**startup.sh:**
```bash
#!/bin/bash
# Azure Web App startup script
python -m hypercorn app:app --bind 0.0.0.0:8000 --workers 4
```

### 3.2 Azure Services Integration

**Required Azure Resources:**
- Azure Web App for Linux (Python 3.12)
- Azure Database for MySQL Flexible Server
- Azure Key Vault (for secrets management)
- Azure Application Insights (for monitoring)
- Azure Active Directory (for SAML authentication)

### 3.3 Infrastructure as Code (Bicep)

**Bicep Templates:**
- Main infrastructure template with all resources
- Modular templates for each service
- Managed Identity configuration
- RBAC assignments
- Network security groups

## Phase 4: Configuration Management

### 4.1 Environment-Specific Configuration

**Configuration Strategy:**
- Base configuration class with common settings
- Environment-specific inheritance
- Azure Key Vault integration for production secrets
- Pydantic settings validation

### 4.2 Feature Flags

**Implementation:**
- Authentication method selection (local vs SAML)
- Feature toggles for debugging
- A/B testing capabilities
- Configuration hot-reloading

## Phase 5: Security & Compliance

### 5.1 Security Headers

**Implementation:**
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options
- X-Content-Type-Options
- Referrer Policy

### 5.2 Azure Security Integration

**Features:**
- Managed Identity for Azure resource access
- Key Vault for secret management
- Application Insights for security monitoring
- Azure AD integration for identity management

## Phase 6: Testing Strategy

### 6.1 Test Structure

**Test Categories:**
- Unit tests for each module
- Integration tests for API endpoints
- Authentication flow tests
- Azure deployment tests
- Performance tests

### 6.2 Test Environment

**Setup:**
- Docker-based test environment
- Mock Azure services for local testing
- CI/CD pipeline integration
- Test data management

## Phase 7: Deployment & DevOps

### 7.1 Azure DevOps Pipeline

**Pipeline Stages:**
1. Build and test
2. Security scanning
3. Infrastructure provisioning
4. Application deployment
5. Health checks
6. Rollback procedures

### 7.2 Monitoring & Observability

**Implementation:**
- Application Insights integration
- Custom metrics and dashboards
- Alerting rules
- Log aggregation
- Performance monitoring

## Implementation Timeline

### Week 1-2: Core Restructuring
- [ ] Remove Redis and Nginx dependencies
- [ ] Implement new project structure
- [ ] Update configuration management
- [ ] Create base authentication interface

### Week 3-4: Authentication Implementation
- [ ] Implement Quart-Auth for local development
- [ ] Implement Quart-SAML for production
- [ ] Create authentication factory pattern
- [ ] Update all authentication flows

### Week 5-6: Azure Integration
- [ ] Create Bicep infrastructure templates
- [ ] Implement Azure-specific configurations
- [ ] Set up managed identity
- [ ] Configure Key Vault integration

### Week 7-8: Testing & Deployment
- [ ] Implement comprehensive test suite
- [ ] Set up CI/CD pipeline
- [ ] Deploy to Azure staging environment
- [ ] Performance testing and optimization

## Risk Mitigation

### Authentication Complexity
- **Risk**: Different auth systems for dev/prod
- **Mitigation**: Common interface, comprehensive testing

### Azure Vendor Lock-in
- **Risk**: Tight coupling to Azure services
- **Mitigation**: Abstract Azure services behind interfaces

### Performance Impact
- **Risk**: SAML overhead in production
- **Mitigation**: Implement caching, session optimization

### Configuration Management
- **Risk**: Complex environment-specific configs
- **Mitigation**: Centralized config validation, clear documentation

## Success Criteria

- [ ] Application runs locally with Quart-Auth
- [ ] Application deploys successfully to Azure Web App
- [ ] SAML authentication works with Azure AD
- [ ] No Redis or Nginx dependencies
- [ ] Comprehensive test coverage (>90%)
- [ ] Performance meets baseline requirements
- [ ] Security compliance validated
- [ ] Documentation complete and accurate

## Resources & Dependencies

### Required Tools
- Azure CLI
- Azure Developer CLI (azd)
- Docker & Docker Compose
- Python 3.12
- Node.js (for scripts)

### Azure Services
- Azure Web App for Linux
- Azure Database for MySQL
- Azure Key Vault
- Azure Application Insights
- Azure Active Directory

### External Libraries
- Quart-Auth (development)
- Quart-SAML (production)
- SQLAlchemy
- Pydantic
- Azure SDK for Python

This development plan provides a comprehensive roadmap for transforming your Quart application into an Azure-ready, production-grade web application while maintaining development flexibility and following security best practices.
