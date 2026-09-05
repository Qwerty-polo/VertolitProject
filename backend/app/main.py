from fastapi import FastAPI
from app.config import settings
app = FastAPI()


@app.get("/")
async def root():
    return {"database_url": settings.database_url}