# StepIn

StepIn - physical meeting application.

## Backend Project Structure

```
backend/
│
├── app/                   # Main application package
│   ├── __init__.py        # Package initialization
│   ├── main.py            # FastAPI application creation
│   │
│   ├── api/               # API endpoints
│   │   ├── __init__.py    # Package initialization
│   │   └── api_v1/        # API version 1
│   │       ├── __init__.py # Package initialization
│   │       ├── api.py     # Router aggregation
│   │       └── endpoints/ # Endpoint modules
│   │           ├── __init__.py # Package initialization
│   │           ├── chat.py    # Chat API endpoints
│   │           ├── meetings.py # Meetings API endpoints
│   │           └── users.py   # Users API endpoints
│   │
│   ├── core/              # Core functionality
│   │   ├── config.py      # Configuration settings
│   │   ├── constants.py   # Application constants
│   │   └── scheduler.py   # Meeting scheduler
│   │
│   ├── db/                # Database models and operations
│   │   └── database.py    # Database access layer
│   │
│   ├── models/            # Pydantic models for API
│   │   ├── __init__.py    # Package initialization
│   │   ├── meeting.py     # Meeting models
│   │   ├── message.py     # Chat message models
│   │   └── user.py        # User models
│   │
│   ├── services/          # Business logic services
│   │   ├── chat_service.py     # Chat business logic
│   │   ├── meeting_service.py  # Meeting business logic
│   │   ├── redis_service.py    # Redis interactions
│   │   └── user_service.py     # User business logic
│   │
│   ├── templates/         # HTML templates (if any)
│   │
│   └── utils/             # Utility functions
│
├── main.py                # Application entry point
├── requirements.txt       # Dependencies
├── scripts/               # Utility scripts
└── tests/                 # Test suite
```

## Features

- **REST API**: Comprehensive API for user and meeting management
- **OpenAPI Documentation**: Automatic API documentation
- **Database Abstraction**: Works with SQLite and PostgreSQL
- **Redis Integration**: Real-time functionality with Redis (or FakeRedis for development)
- **Scheduler**: Automatic meeting activation/deactivation
- **Geospatial**: Find nearby meetings functionality
- **Real-time Chat**: Meeting chat functionality

## Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation and settings management
- **SQLAlchemy**: SQL toolkit and ORM
- **Redis**: In-memory data structure store
- **APScheduler**: Advanced Python scheduler
- **GeoJSON**: Geographical functionality
- **Uvicorn**: ASGI server

## Development

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy example environment file
cp .env.example .env

# Edit .env file with your configuration
```

### Running

```bash
# Development with auto-reload
uvicorn app.main:app --reload

# Production
uvicorn app.main:app
```

### API Documentation

When the application is running, you can access the OpenAPI documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Users

- `POST /api/users/`: Create a new user
- `GET /api/users/{email}`: Get user details
- `PUT /api/users/{email}`: Update user details
- `DELETE /api/users/{email}`: Delete a user

### Meetings

- `POST /api/meetings/`: Create a new meeting
- `GET /api/meetings/{meeting_id}`: Get meeting details
- `GET /api/meetings/nearby`: Find nearby meetings
- `PUT /api/meetings/{meeting_id}`: Update meeting details
- `DELETE /api/meetings/{meeting_id}`: Delete a meeting
- `POST /api/meetings/{meeting_id}/join`: Join a meeting
- `POST /api/meetings/{meeting_id}/leave`: Leave a meeting
- `GET /api/meetings/{meeting_id}/participants`: Get meeting participants
- `POST /api/meetings/{meeting_id}/end`: End a meeting

### Chat

- `POST /api/chat/{meeting_id}`: Send a chat message
- `GET /api/chat/{meeting_id}`: Get chat messages for a meeting

## Database

The application can work with both SQLite (for development) and PostgreSQL (for production).

## Testing

```bash
# Run tests
pytest
```
