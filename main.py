from src.api.api import router

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(router, prefix="/api", tags=["API"])
@app.get("/")
async def root():
    return {"message": "Welcome to the Text2SQL Agents. "}

# If you want to run the FastAPI app, you can use the command:
# uvicorn main:app --reload