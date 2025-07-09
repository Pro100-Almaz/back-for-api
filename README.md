# Django REST Framework User Management Platform

A comprehensive Django REST Framework project with JWT authentication and role-based authorization for a user management platform.

## Features

- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: Three distinct user roles with specific permissions
- **User Management**: Create, manage, and track users with role-based access
- **Points System**: Manage user points for service usage
- **Revenue Tracking**: Monitor revenue and payouts for tool creators
- **Admin Interface**: Comprehensive Django admin for all models

## User Roles & Permissions

### 🔐 Platform-Specific Roles

| Role | Permissions |
|------|-------------|
| **Client** | Browse content, use services (deduct points), view history, submit feedback |
| **Tool Creator** | Manage API keys, track usage/revenue, receive payouts |
| **Admin** | Full access: manage users, payouts, refunds, support, and site content |

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

### User Registration

| Endpoint | Method | Description | Permissions |
|----------|--------|-------------|-------------|
| `/api/users/register/client/` | POST | Register new client | Public |
| `/api/users/register/tool-creator/` | POST | Register new tool creator | Public |
| `/api/users/register/admin/` | POST | Register new admin | Admin only |

### User Management

| Endpoint | Method | Description | Permissions |
|----------|--------|-------------|-------------|
| `/api/users/clients/` | GET | List clients | Admin only |
| `/api/users/clients/points_balance/` | GET | Get client points balance | Client only |
| `/api/users/tool-creators/` | GET | List tool creators | Admin only |
| `/api/users/tool-creators/revenue_stats/` | GET | Get revenue statistics | Tool Creator only |

## Role-Based Access Control

### Client Role
- **Browse content**: View available content
- **Use services**: Consume points to use services
- **View points balance**: Check their current points balance
- **Submit feedback**: Rate and review services they've used

### Tool Creator Role
- **Manage API keys**: Generate and manage API keys
- **Track usage/revenue**: Monitor usage and revenue statistics
- **Receive payouts**: Access payout information
- **View revenue stats**: Check their revenue and payout data

### Admin Role
- **Manage users**: Full user management capabilities
- **Manage content**: Approve, suspend, or modify any content
- **Manage payouts**: Process payouts to tool creators
- **Manage refunds**: Handle refund requests
- **Manage support**: Access support ticket system
- **Manage site content**: Update platform content

## Database Models

### User Models
- `User`: Custom user model with role-based permissions
- `UserProfile`: Extended user profile information

## Authentication Flow

1. **Registration**: Users register with email/password for specific roles
2. **Login**: Users authenticate and receive JWT tokens
3. **Authorization**: Role-based permissions control access to endpoints
4. **Token Refresh**: Automatic token refresh for long sessions

## Points System

- **Clients** start with 0 points
- **Points** are deducted when using services
- **Admins** can add/deduct points from clients
- **Service usage** costs are set by service providers

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
- User profiles
- Points management
- Revenue tracking

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

### Register a Client

```bash
curl -X POST http://localhost:8000/api/users/register/client/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "client@example.com",
    "username": "clientuser",
    "password": "password123",
    "password_confirm": "password123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Register a Tool Creator

```bash
curl -X POST http://localhost:8000/api/users/register/tool-creator/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "creator@example.com",
    "username": "toolcreator",
    "password": "password123",
    "password_confirm": "password123",
    "first_name": "Jane",
    "last_name": "Smith"
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

### Get Client Points Balance

```bash
curl -X GET http://localhost:8000/api/users/clients/points_balance/ \
  -H "Authorization: Bearer <your-jwt-token>"
```

### Get Tool Creator Revenue Stats

```bash
curl -X GET http://localhost:8000/api/users/tool-creators/revenue_stats/ \
  -H "Authorization: Bearer <your-jwt-token>"
``` 