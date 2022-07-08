from fastapi import FastAPI
from androguard.core import apk

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}