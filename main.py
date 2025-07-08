from fastapi import FastAPI
from app.api import webhook, admin_api

app = FastAPI()

app.include_router(webhook.router)
app.include_router(admin_api.router)
