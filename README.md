# Django REST Framework SaaS Platform

A comprehensive Django REST Framework project with JWT authentication and role-based authorization for a SaaS platform that manages tools, users, and usage tracking.

## Features

- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: Three distinct user roles with specific permissions
- **Tool Management**: Create, manage, and use tools with points system
- **Usage Tracking**: Monitor tool usage and generate statistics
- **Feedback System**: Users can rate and review tools
- **API Key Management**: Secure API key generation and management
- **Admin Interface**: Comprehensive Django admin for all models

## User Roles & Permissions

### 🔐 Platform-Specific Roles (Internal to SaaS)

| Role | Permissions |
|------|-------------|
| **Client** | Browse tools, use tools (deduct points), view history, submit feedback |
| **Tool Creator** | Submit tools, manage API keys, track usage/revenue, receive payouts |
| **Admin** | Full access: manage users, tools, payouts, refunds, support, and site content |

## Installation & Setup

### Prerequisites

- Python 3.8+
- pip
- virtualenv (recommended)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd back-for-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 3. Database Setup

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 4. Run the Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/`

## API Endpoints

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/token/` | POST | Get JWT access and refresh tokens |
| `/api/token/refresh/` | POST | Refresh JWT access token |
| `/api/token/verify/` | POST | Verify JWT token |

### User Management

| Endpoint | Method | Description | Permissions |
|----------|--------|-------------|-------------|
| `/api/users/register/` | POST | Register new user | Public |
| `/api/users/users/` | GET | List users | Admin only |
| `/api/users/users/me/` | GET | Get current user profile | Authenticated |
| `/api/users/users/update_me/` | PUT/PATCH | Update current user profile | Authenticated |
| `/api/users/clients/` | GET | List all clients | Admin only |
| `/api/users/tool-creators/` | GET | List all tool creators | Admin only |

### Tool Management

| Endpoint | Method | Description | Permissions |
|----------|--------|-------------|-------------|
| `/api/tools/tools/` | GET | List available tools | All authenticated |
| `/api/tools/tools/` | POST | Create new tool | Tool Creator/Admin |
| `/api/tools/tools/{id}/` | GET | Get tool details | All authenticated |
| `/api/tools/tools/{id}/use/` | POST | Use a tool | All authenticated |
| `/api/tools/tools/{id}/feedback/` | GET | Get tool feedback | All authenticated |
| `/api/tools/tools/{id}/submit_feedback/` | POST | Submit tool feedback | All authenticated |
| `/api/tools/tools/search/` | GET | Search tools | All authenticated |
| `/api/tools/tools/my_tools/` | GET | Get user's created tools | Tool Creator |

### Usage Tracking

| Endpoint | Method | Description | Permissions |
|----------|--------|-------------|-------------|
| `/api/tools/usage/` | GET | List tool usage | Authenticated |
| `/api/tools/usage/my_usage/` | GET | Get user's usage history | Authenticated |

### API Keys

| Endpoint | Method | Description | Permissions |
|----------|--------|-------------|-------------|
| `/api/tools/api-keys/` | GET | List API keys | Authenticated |
| `/api/tools/api-keys/` | POST | Create API key | Authenticated |
| `/api/tools/api-keys/{id}/regenerate/` | POST | Regenerate API key | Owner/Admin |

## Role-Based Access Control

### Client Role
- **Browse tools**: View all active tools
- **Use tools**: Consume points to use tools
- **View history**: See their own usage history
- **Submit feedback**: Rate and review tools they've used

### Tool Creator Role
- **Submit tools**: Create and manage their own tools
- **Manage API keys**: Generate and manage API keys for their tools
- **Track usage/revenue**: Monitor tool usage and revenue statistics
- **Receive payouts**: Access payout information

### Admin Role
- **Manage users**: Full user management capabilities
- **Manage tools**: Approve, suspend, or modify any tool
- **Manage payouts**: Process payouts to tool creators
- **Manage refunds**: Handle refund requests
- **Manage support**: Access support ticket system
- **Manage site content**: Update platform content

## Database Models

### User Models
- `User`: Custom user model with role-based permissions
- `UserProfile`: Extended user profile information

### Tool Models
- `Tool`: Main tool model with metadata and statistics
- `ToolUsage`: Track individual tool usage instances
- `ToolFeedback`: User ratings and reviews for tools
- `ToolApiKey`: API key management for tools

## Authentication Flow

1. **Registration**: Users register with email/password (defaults to Client role)
2. **Login**: Users authenticate and receive JWT tokens
3. **Authorization**: Role-based permissions control access to endpoints
4. **Token Refresh**: Automatic token refresh for long sessions

## Points System

- **Clients** start with 0 points
- **Points** are deducted when using tools
- **Admins** can add/deduct points from clients
- **Tool usage** costs are set by tool creators

## Development

### Running Tests

```bash
python manage.py test
```

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Admin Interface

Access the Django admin at `http://localhost:8000/admin/` to manage:
- Users and roles
- Tools and their status
- Usage tracking
- Feedback and ratings
- API keys

## Production Deployment

### Environment Variables

```env
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=your-database-url
```

### Security Considerations

1. **JWT Settings**: Configure token lifetimes appropriately
2. **CORS**: Set up proper CORS headers for your frontend
3. **Database**: Use PostgreSQL for production
4. **Static Files**: Configure proper static file serving
5. **HTTPS**: Always use HTTPS in production

## API Examples

### Register a User

```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "password123",
    "password_confirm": "password123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Get JWT Token

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

### Use a Tool

```bash
curl -X POST http://localhost:8000/api/tools/tools/1/use/ \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {"text": "Hello world"}
  }'
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License. 