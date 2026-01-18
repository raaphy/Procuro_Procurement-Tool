from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import requests, extraction, commodity_groups
from database.database import init_db

app = FastAPI(title="Procuro API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(requests.router)
app.include_router(extraction.router)
app.include_router(commodity_groups.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
