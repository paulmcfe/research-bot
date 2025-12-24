# api/index.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from researchbot import ResearchBot

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialize ResearchBot once at startup
bot = ResearchBot()

class ChatRequest(BaseModel):
    message: str

class IndexRequest(BaseModel):
    directory: str = "./documents"

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/api/chat")
def chat(request: ChatRequest):
    try:
        response = bot.research(request.message)
        return {"reply": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/index")
def index_documents(request: IndexRequest):
    """Index documents from a directory."""
    try:
        bot.index_documents(request.directory)
        return {"status": "indexed", "directory": request.directory}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error indexing: {str(e)}")