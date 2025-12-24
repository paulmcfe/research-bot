# ResearchBot v5 - FastAPI Backend

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from researchbot import ResearchBot

load_dotenv()

# Initialize ResearchBot v5
bot = ResearchBot()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Index documents automatically at startup."""
    chunks = bot.index_documents("./documents")
    print(f"✓ Indexed {chunks} chunks from ./documents at startup")
    yield

app = FastAPI(
    title="ResearchBot API",
    description="Agentic RAG-powered research assistant",
    version="5.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    version: str = "5.0"


class IndexRequest(BaseModel):
    directory: str = "./documents"
    extensions: Optional[list] = None


class IndexResponse(BaseModel):
    status: str
    directory: str
    chunks_indexed: int


class HealthResponse(BaseModel):
    status: str
    version: str
    description: str


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/", response_model=HealthResponse)
def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "5.0",
        "description": "ResearchBot v5 - Agentic RAG with LangGraph"
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Send a research query to ResearchBot.
    
    ResearchBot v5 uses an agentic RAG pipeline with:
    - Query planning and decomposition
    - Dynamic retrieval from the knowledge base
    - Multi-source synthesis with citations
    - Self-reflection and confidence scoring
    """
    try:
        response = bot.research(request.message)
        return {"reply": response, "version": "5.0"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Research error: {str(e)}"
        )


@app.post("/api/index", response_model=IndexResponse)
def index_documents(request: IndexRequest):
    """
    Index documents from a directory into ResearchBot's knowledge base.
    
    Supports .txt files by default. Documents are chunked
    and embedded for semantic search.
    """
    try:
        extensions = request.extensions or [".txt"]
        chunks_indexed = bot.index_documents(request.directory, extensions)
        return {
            "status": "indexed",
            "directory": request.directory,
            "chunks_indexed": chunks_indexed
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Indexing error: {str(e)}"
        )


@app.get("/api/health")
def health_check():
    """Detailed health check for ResearchBot v3."""
    return {
        "status": "healthy",
        "version": "5.0",
        "features": [
            "Query planning and decomposition",
            "Dynamic retrieval strategies",
            "Multi-source synthesis with citations",
            "Self-reflection and confidence scoring",
            "Iterative research loops"
        ],
        "model": "gpt-5-nano",
        "embedding_model": "text-embedding-3-small"
    }