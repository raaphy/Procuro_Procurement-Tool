# Procuro

Procurement Request Management System.

## Features

- **Create Requests**: Submit procurement requests with vendor details and order lines
- **PDF Upload & Auto-extraction**: Upload vendor offers to auto-fill the form using AI
- **Auto Commodity Classification**: AI automatically suggests the appropriate commodity group
- **Request Overview**: View, filter, and manage all procurement requests
- **Status Tracking**: Track request status (Open → In Progress → Closed) with full history

## Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key

# Run the application
streamlit run app.py

# Run tests
python -m pytest tests/ -v 
```

## Environment Variables

Create a `.env` file with:

```
OPENAI_API_KEY=your-api-key-here
DATABASE_URL=sqlite:///./procuro.db
```

## Tech Stack

- **Frontend**: Streamlit
- **Database**: SQLite + SQLAlchemy
- **AI**: OpenAI GPT-4o-mini for extraction and classification
- **PDF Processing**: PyPDF2
