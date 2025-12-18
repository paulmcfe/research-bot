from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS so the frontend can talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/api/chat")
def chat(request: ChatRequest):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    
    try:
        user_message = request.message
        response = client.responses.create(
            model="gpt-5-nano",
            instructions="You are ResearchBot, a personal research assistant. Your job is to help users explore topics, answer questions with clear explanations, and point them toward related ideas worth investigating. Be thorough but concise. When you're uncertain or your knowledge might be outdated, be upfront about it. Think of yourself as a knowledgeable colleague who's great at breaking down complex topics. Format your responses using markdown: use ```language for code blocks, **bold** for emphasis, and proper list formatting with - for bullets.",
            input=user_message
        )
        return {"reply": response.output_text}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling OpenAI API: {str(e)}")
