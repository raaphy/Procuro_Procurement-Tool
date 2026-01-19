# Procuro

Procurement Request Management System.

## Features

- **Create Requests**: Submit procurement requests with vendor details and order lines
- **PDF Upload & Auto-extraction**: Upload vendor offers to auto-fill the form using AI
- **Auto Commodity Classification**: AI automatically suggests the appropriate commodity group
- **Request Overview**: View, filter, and manage all procurement requests
- **Status Tracking**: Track request status (Open → In Progress → Closed) with full history

## Tech Stack

- **Frontend**: React + TypeScript + TailwindCSS (Vite)
- **Backend**: FastAPI (Python)
- **Database**: SQLite + SQLAlchemy
- **AI**: OpenAI GPT-4o for extraction and classification
- **PDF Processing**: PyMuPDF + pypdf

## Quick Start

```bash
# Create virtual environment (Python 3.14)
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Frontend dependencies
cd frontend && npm install && cd ..

# Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key

# Start development servers
./start-dev.sh
```

### Manual Start

**Backend** (http://localhost:8000):
```bash
cd backend
PYTHONPATH=.. uvicorn main:app --reload --port 8000
```

**Frontend** (http://localhost:5173):
```bash
cd frontend
npm run dev
```

**API Docs**: http://localhost:8000/docs

## Environment Variables

Create a `.env` file with:

```
OPENAI_API_KEY=your-api-key-here
DATABASE_URL=sqlite:///./procuro.db
```

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_api_requests.py

# Run with coverage
pytest --cov=backend --cov=database
```

## Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t procuro .
docker run -p 8000:8000 -e OPENAI_API_KEY=your-key procuro
```

The app runs at http://localhost:8000 (frontend + API).

## Project Structure

```
├── backend/               # FastAPI Backend
│   ├── main.py           # App + CORS + Routers
│   ├── schemas.py        # Pydantic DTOs
│   ├── extraction.py     # OpenAI Integration
│   └── routers/          # API Endpoints
├── frontend/              # React Frontend
│   └── src/
│       ├── api/          # API Client
│       ├── components/   # React Components
│       ├── pages/        # Route Pages
│       └── types/        # TypeScript Types
├── database/              # SQLAlchemy Models
├── tests/                 # Pytest Tests
├── Dockerfile             # Production build
├── docker-compose.yml     # Docker Compose config
└── start-dev.sh           # Dev startup script
```


