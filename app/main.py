from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Crypto Router MVP")

app.include_router(router)