# Promptly

**URL**: https://promptly.social

AI-powered professional social media content creation platform for LinkedIn. Promptly helps users create, schedule, and publish engaging LinkedIn content by analyzing their writing style, understanding their content preferences, and generating personalized post suggestions.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Development](#development)
- [Deployment](#deployment)
- [Environment Variables](#environment-variables)
- [Contributing](#contributing)

## Features

### Core Functionality

- **LinkedIn Integration**: Dual OAuth flow for post publishing and analytics
- **AI-Powered Content Generation**: Personalized content suggestions based on user preferences and writing style
- **Writing Style Analysis**: Analyzes user's existing LinkedIn posts to match their tone and style
- **Content Ideas Bank**: Store and organize content ideas with AI-powered suggestions
- **Post Scheduling**: Schedule posts with Google Cloud Scheduler integration
- **Interactive Chat**: AI chat assistant for content ideation and refinement
- **User Activity Analysis**: Automated analysis of LinkedIn engagement patterns
- **Onboarding Flow**: Guided setup process for new users

### User Features

- Multi-step onboarding with progress tracking
- Content preferences configuration (topics, sources, writing style)
- Post drafting with AI assistance
- Schedule management with timezone support
- Real-time post preview
- Analytics integration for post performance tracking

## Architecture

Promptly uses a modern cloud-native architecture:

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│   React     │─────▶│   FastAPI    │─────▶│  PostgreSQL     │
│  Frontend   │      │   Backend    │      │  (Cloud SQL)    │
└─────────────┘      └──────────────┘      └─────────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ GCP Cloud    │
                     │ Functions    │
                     └──────────────┘
                            │
                     ┌──────┴────────┐
                     │               │
              ┌──────▼─────┐  ┌─────▼──────┐
              │  User      │  │  Content   │
              │  Activity  │  │  Suggestions│
              │  Analysis  │  │  Generator │
              └────────────┘  └────────────┘
```

### Key Components

1. **Frontend (React + TypeScript)**
   - Built with Vite for fast development
   - UI components from shadcn/ui and Radix UI
   - State management with React Context and TanStack Query
   - Token-based authentication with automatic refresh

2. **Backend (FastAPI + Python)**
   - Async/await throughout for high performance
   - SQLAlchemy ORM with async support
   - Row-Level Security (RLS) using PostgreSQL session variables
   - JWT token authentication
   - OpenAPI documentation

3. **Database (PostgreSQL on Cloud SQL)**
   - Managed PostgreSQL instance
   - Automatic migrations on startup
   - Connection pooling with Cloud SQL connector
   - Row-level security for multi-tenant isolation

4. **Cloud Functions (GCP)**
   - Serverless background processing
   - Scheduled jobs for user activity analysis
   - Content suggestion generation
   - Post publishing automation

5. **Infrastructure (Terraform)**
   - Infrastructure as Code for all GCP resources
   - Separate staging and production environments
   - Cloud Scheduler for recurring jobs

## Tech Stack

### Frontend

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Libraries**:
  - Tailwind CSS for styling
  - shadcn/ui components
  - Radix UI primitives
- **State Management**: React Context + TanStack Query
- **Routing**: React Router v6
- **Form Handling**: React Hook Form + Zod validation
- **Testing**: Vitest + React Testing Library

### Backend

- **Framework**: FastAPI
- **Language**: Python 3.13
- **ORM**: SQLAlchemy with async support
- **Authentication**: JWT tokens + LinkedIn OAuth 2.0
- **Validation**: Pydantic v2
- **Database**: PostgreSQL (Google Cloud SQL)
- **Logging**: Loguru
- **Testing**: pytest + pytest-asyncio
- **AI Integration**: OpenRouter API (Google Gemini, Claude, DeepSeek)

### Infrastructure

- **Cloud Provider**: Google Cloud Platform (GCP)
- **Compute**: Cloud Functions (Python 3.11)
- **Database**: Cloud SQL (PostgreSQL)
- **Scheduling**: Cloud Scheduler
- **Storage**: Cloud Storage (for media)
- **IaC**: Terraform

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (for local development)
- Google Cloud account (for deployment)
- LinkedIn Developer App credentials

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/promptly-social.git
cd promptly-social
```

2. **Backend Setup**

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your configuration

# Run the development server
uvicorn app.main:app --reload
```

The backend API will be available at `http://localhost:8000`

3. **Frontend Setup**

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Development

### Running Tests

**Backend**:
```bash
cd backend
pytest                    # Run all tests
pytest --cov=app         # Run with coverage
pytest tests/test_auth.py # Run specific test file
pytest -v                # Verbose output
```

**Frontend**:
```bash
cd frontend
npm test                 # Run once
npm run test:watch       # Watch mode
npm run test:ui          # UI mode
```

### Code Quality

**Backend**:
- Type hints with Python's typing module
- Pydantic for data validation
- Structured logging with Loguru

**Frontend**:
```bash
npm run lint            # Run ESLint
npm run build           # Production build
npm run build:dev       # Development build
```

### Database Migrations

Migrations are handled programmatically and auto-applied on startup when `AUTO_APPLY_MIGRATIONS=true`:

1. Add migration function to `backend/app/core/migrations.py`
2. Register in the migrations list
3. Restart the backend server

### Docker Development

```bash
cd backend
docker build -t promptly-backend .
docker run -p 8000:8000 --env-file .env promptly-backend
```

## Deployment

### Backend Deployment (Cloud Run)

The backend is designed to run on Google Cloud Run or any container platform:

1. Build the Docker image
2. Push to Google Container Registry
3. Deploy to Cloud Run
4. Configure environment variables
5. Set up Cloud SQL connection

### Frontend Deployment

The frontend can be deployed to any static hosting service:

```bash
cd frontend
npm run build
# Deploy the dist/ directory to your hosting provider
```

### Cloud Functions

Cloud Functions are deployed via Terraform:

```bash
cd terraform/environments/[environment]
terraform init
terraform plan
terraform apply
```

## Environment Variables

### Backend (`backend/.env`)

**Required**:
- `DATABASE_URL` - PostgreSQL connection string
- `CLOUD_SQL_*` - Cloud SQL configuration (production)
- `SUPABASE_URL`, `SUPABASE_KEY` - Supabase authentication
- `JWT_SECRET_KEY` - Secret for JWT signing
- `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET` - LinkedIn OAuth (native)
- `LINKEDIN_ANALYTICS_CLIENT_ID`, `LINKEDIN_ANALYTICS_CLIENT_SECRET` - LinkedIn OAuth (analytics)
- `OPENROUTER_API_KEY` - OpenRouter API key for AI features

**Optional**:
- `DEBUG` - Enable debug mode (default: False)
- `ENVIRONMENT` - Environment name (development/staging/production)
- `CORS_ORIGINS` - Allowed CORS origins (comma-separated)
- `GCP_PROJECT_ID` - Google Cloud project ID
- `POST_MEDIA_BUCKET_NAME` - GCS bucket for post media

See `backend/env.example` for complete list.

### Frontend (`frontend/.env`)

- `VITE_API_URL` - Backend API URL (default: `http://localhost:8000`)

## Key Features Explained

### Dual LinkedIn OAuth

Promptly uses two separate LinkedIn OAuth applications:

1. **Native OAuth** - For post publishing with `w_member_social` scope
2. **Analytics OAuth** - For post analytics with `r_member_postAnalytics` and `r_member_profileAnalytics` scopes

This separation is required because LinkedIn restricts certain scopes to specific use cases.

### Row-Level Security (RLS)

The application enforces data isolation using PostgreSQL session variables:
- Each request sets `app.user_id` in the database session
- All queries automatically filter by the current user
- Prevents data leakage between users

### AI Content Generation

- Uses OpenRouter API with multiple model support
- Primary model: Google Gemini 2.5 Flash (fast)
- Large model: Google Gemini 2.5 Pro (complex tasks)
- Fallback models: DeepSeek, Claude Sonnet
- Temperature settings configurable per use case

### Post Scheduling Workflow

1. User creates/schedules a post
2. Backend creates a Cloud Scheduler job
3. At scheduled time, Cloud Scheduler triggers the `unified_post_scheduler` function
4. Function publishes to LinkedIn and updates post status

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary software. All rights reserved.

## Support

For questions or support, please contact the development team or open an issue in the repository.
