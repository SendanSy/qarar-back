# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your actual values

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Running the Application
```bash
# Development server
DJANGO_ENV=development python manage.py runserver

# Production server
DJANGO_ENV=production gunicorn core.wsgi:application

# The API will be available at http://127.0.0.1:8000/
# Swagger UI: http://127.0.0.1:8000/swagger/
# ReDoc: http://127.0.0.1:8000/redoc/
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
coverage run -m pytest
coverage report
coverage html

# Run specific test file
pytest apps/content/tests.py
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8
```

### Management Commands
```bash
# Create sample posts
python manage.py create_sample_posts

# Seed database with initial data
python manage.py seed_data

# Process hashtags for existing posts
python manage.py process_hashtags

# Process hashtags with options
python manage.py process_hashtags --force --status=published
python manage.py process_hashtags --dry-run  # Preview changes only
```

## Architecture Overview (Updated)

This is a Django REST Framework-based news platform backend for the "Qarar" platform, designed to handle governmental decisions and announcements in Arabic/English with enhanced architecture patterns.

### Core Architecture Patterns

1. **Clean Architecture**: Implements Domain-Driven Design with service layers
2. **Multi-Environment Settings**: Environment-specific configurations (development/staging/production)
3. **Base Model Classes**: Comprehensive inheritance hierarchy for common functionality
4. **Service Layer Pattern**: Business logic encapsulated in service classes
5. **Enhanced Security**: Production-ready security configurations
6. **Bilingual Support**: Full Arabic/English content support with validation

### Enhanced Security Features

- **Environment-based CORS**: Configurable allowed origins per environment
- **Security Headers**: Comprehensive security middleware
- **Input Validation**: Custom validators for Arabic text, files, and business rules
- **Audit Trail**: Built-in user tracking for all model changes
- **Soft Delete**: Safe deletion with recovery capability

### Core Base Classes

Located in `apps/core/models.py`:

- **`BaseModel`**: UUID, timestamps, soft delete
- **`ContentBaseModel`**: Full content functionality (SEO, publishing, tracking, audit)
- **`CategoryBaseModel`**: For taxonomies and classifications
- **Mixins**: `TimestampMixin`, `PublishableMixin`, `ViewTrackingMixin`, `AuditMixin`, etc.

### Service Layer Architecture

Located in `apps/core/services.py` and app-specific service files:

- **`CRUDService`**: Base CRUD operations
- **`PublishableService`**: Publishing workflow management
- **`ViewTrackingService`**: View analytics
- **`SearchService`**: Search functionality base
- **Domain Services**: `PostService`, `CategoryService`, `HashTagService`

### Enhanced Database Design

- **UUID Primary Keys**: Better security and distributed systems support
- **Database Constraints**: Unique constraints with soft delete conditions
- **Optimized Indexes**: Composite indexes for common query patterns
- **Through Models**: Audit trails for many-to-many relationships
- **Check Constraints**: Data integrity at database level

### API Response Standardization

- **Consistent Response Format**: Standardized success/error responses
- **Custom Exception Handler**: Unified error handling across the API
- **Business Logic Exceptions**: Domain-specific error types
- **Validation Improvements**: Enhanced field validation with custom validators

### Key Apps and Responsibilities

- **`apps/core/`**: Base classes, services, exceptions, validators
- **`apps/content/`**: Content management with enhanced models and services
- **`apps/users/`**: User management and authentication
- **`apps/producers/`**: Organizations and subsidiaries
- **`apps/geographics/`**: Geographic classification system

### Enhanced Content Classification

1. **PostType**: Enhanced with colors, icons, and post counts
2. **Categories/SubCategories**: Hierarchical with proper constraints and counts
3. **HashTags**: Automatic extraction from content with Arabic/English support, trending detection, and popularity tracking
4. **Through Models**: `PostCategory`, `PostSubCategory`, `PostHashTag` with timestamps
5. **Bookmarks**: Full bookmark system with collections and soft delete support

### Environment Configuration

Settings split into multiple files in `core/settings/`:
- **`base.py`**: Common settings
- **`development.py`**: Development-specific settings
- **`staging.py`**: Staging environment settings
- **`production.py`**: Production security and performance settings

### File Structure Patterns

```
apps/
├── core/
│   ├── models.py           # Base model classes and mixins
│   ├── services.py         # Base service classes
│   ├── exceptions.py       # Custom exceptions and error handling
│   ├── validators.py       # Custom field validators
├── content/
│   ├── models/
│   │   ├── post.py        # Enhanced Post model with constraints
│   │   ├── classification.py  # Categories, hashtags with validation
│   │   └── bookmark.py    # Bookmark system
│   ├── services.py        # Content-specific business logic
│   └── migrations/
core/
├── settings/
│   ├── __init__.py        # Environment detection
│   ├── base.py           # Common settings
│   ├── development.py    # Development settings
│   ├── staging.py        # Staging settings
│   └── production.py     # Production settings
```

### Custom Validators

Located in `apps/core/validators.py`:
- **`ArabicTextValidator`**: Ensures Arabic content quality
- **`HashtagValidator`**: Validates hashtag format
- **`FileTypeValidator`**: File upload restrictions
- **`ImageDimensionValidator`**: Image size validation
- **`PasswordStrengthValidator`**: Enhanced password security

### Business Logic Encapsulation

- **Service Classes**: All business logic moved from views to services
- **Domain Events**: Trackable actions with audit logging
- **Permission Checks**: Centralized authorization logic
- **Data Validation**: Multi-layer validation (field, model, business)

### Testing Infrastructure

- **Service Testing**: Test business logic independently
- **Model Validation**: Test constraints and validators
- **API Integration**: Test complete workflows
- **Factory Pattern**: Reusable test data generation

### Performance Optimizations

- **Query Optimization**: Select_related and prefetch_related usage
- **Database Indexes**: Optimized for common access patterns
- **Caching Strategy**: Redis integration for production
- **File Handling**: Efficient upload and validation

### Key Model Relationships (Enhanced)

- **Post → Organization**: With permission checks
- **Post → Categories**: Through models with timestamps
- **Post → HashTags**: Auto-extraction with Arabic/English support, trending detection
- **Post → Attachments**: Full file URL support with domain inclusion
- **User → Bookmarks**: With collections, privacy settings, and proper soft delete handling
- **Audit Trail**: Complete change tracking for all models

### Migration Strategy

When making changes to models:
1. Always create migrations: `python manage.py makemigrations`
2. Review generated migrations for correctness
3. Test migrations on staging before production
4. Use `--dry-run` flag to preview changes

### Best Practices Implemented

- **Separation of Concerns**: Clear boundaries between layers
- **DRY Principle**: Base classes eliminate code duplication
- **Security First**: Production-ready security configurations
- **Validation at All Levels**: Database, model, and business logic validation
- **Audit Everything**: Complete tracking of user actions
- **Bilingual by Design**: Full Arabic/English support throughout

## API Features and Capabilities

### Authentication & Authorization
- **JWT Tokens**: Access tokens expire after 30 days, refresh tokens after 90 days
- **Automatic Login**: New user registration returns JWT tokens immediately
- **Permission System**: Role-based access control with public endpoints for reference data

### Content Management
- **Automatic Hashtag Extraction**: Posts are automatically scanned for #hashtags in all content fields
- **Bilingual Support**: Full Arabic and English content with proper validation
- **Soft Delete**: All models support soft deletion for data recovery
- **File Attachments**: Full URL support with domain inclusion for frontend consumption

### API Endpoints Structure
- **Content**: `/api/v1/content/` - Posts, categories, hashtags, bookmarks
- **Users**: `/api/v1/users/` - Authentication, profiles, management
- **Public Access**: Categories, hashtags, post types, and search are publicly accessible
- **Protected Access**: User-specific data requires authentication

### Advanced Features
- **Bookmark System**: Full bookmark management with soft delete support
- **Hashtag Analytics**: Trending and popular hashtag tracking
- **Search & Filtering**: Comprehensive search across all content types
- **Caching Strategy**: Optimized caching for performance with real-time bookmark status
- **File Management**: Secure file uploads with validation and full URL generation

### Monitoring & Health Checks
- **Performance Monitoring**: Built-in performance tracking and metrics
- **Health Endpoints**: System health checks with component status
- **Error Handling**: Comprehensive error handling with standardized responses
- **Audit Logging**: Complete user action tracking for security and analytics