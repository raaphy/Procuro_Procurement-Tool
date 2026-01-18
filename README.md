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
# Create virtual environment
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

## Project Structure

```
procuro/
├── backend/               # FastAPI Backend
│   ├── main.py           # App + CORS + Routers
│   ├── schemas.py        # Pydantic DTOs
│   └── routers/          # API Endpoints
├── frontend/              # React Frontend
│   ├── src/
│   │   ├── api/          # API Client
│   │   ├── components/   # React Components
│   │   ├── pages/        # Route Pages
│   │   └── types/        # TypeScript Types
├── database/              # SQLAlchemy Models
├── extraction.py          # OpenAI Integration
└── start-dev.sh          # Dev startup script
```


