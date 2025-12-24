# ResearchBot v4

An AI-powered research assistant built with LangChain 1.0 and LangGraph that helps you find and synthesize information from your document collection using an agentic RAG (Retrieval Augmented Generation) pipeline.

## Features

- **Agentic RAG Pipeline**: Multi-stage research workflow with planning, retrieval, synthesis, and reflection
- **Query Decomposition**: Automatically breaks complex questions into focused sub-questions
- **Document Indexing**: Load and index text documents (.txt, .md files) into a vector database
- **Semantic Search**: Find relevant information using natural language queries with context-aware retrieval
- **Multi-Source Synthesis**: Combines information from multiple sources with proper citations
- **Self-Reflection**: Evaluates research quality and iteratively improves results
- **FastAPI Backend**: RESTful API for chat and document indexing
- **Web Frontend**: Interactive chat interface for asking research questions

## Architecture

ResearchBot v4 uses a **LangGraph state machine** with four specialized nodes:

1. **Planning Node**: Analyzes queries and decomposes them into sub-questions
2. **Retrieval Node**: Searches the vector database for relevant sources
3. **Synthesis Node**: Combines sources into coherent, cited findings
4. **Reflection Node**: Evaluates quality and determines if more research is needed

**Tech Stack:**
- **Backend**: FastAPI + LangChain 1.0 + LangGraph
- **LLM**: OpenAI GPT-5-nano (fast, cost-efficient reasoning model)
- **Embeddings**: OpenAI text-embedding-3-small
- **Vector Database**: Qdrant (in-memory for development)
- **State Machine**: LangGraph for agentic workflow orchestration

## Prerequisites

- Python 3.12+
- [`uv`](https://github.com/astral-sh/uv) package manager
- OpenAI API key

## Setup

### 1. Install uv Package Manager

```bash
pip install uv
```

### 2. Clone the Repository

```bash
git clone <your-repo-url>
cd research-bot
```

### 3. Install Dependencies

```bash
uv sync
```

This creates a `.venv/` virtual environment and installs all dependencies from [pyproject.toml](pyproject.toml).

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# OpenAI API Key
OPENAI_API_KEY=sk-your-api-key-here
```

Get your API key from https://platform.openai.com/api-keys

### 5. Add Documents

Place your text documents (.txt files) in the `documents/` directory:

```bash
mkdir -p documents
# Add your .txt files to this directory
```

## Running the Application

### Start the Backend Server

From the project root:

```bash
uv run uvicorn api.index:app --host 127.0.0.1 --port 8000 --reload
```

Or activate the virtual environment first:

```bash
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uvicorn api.index:app --host 127.0.0.1 --port 8000 --reload
```

The server will start on http://127.0.0.1:8000

### Start the Frontend

Follow the instructions in [frontend/README.md](frontend/README.md) to run the web interface.

## API Endpoints

### Index Documents

Load documents from a directory into the vector store:

```bash
curl -X POST http://127.0.0.1:8000/api/index \
  -H "Content-Type: application/json" \
  -d '{"directory": "./documents"}'
```

**Response:**
```json
{
  "status": "indexed",
  "directory": "./documents"
}
```

### Chat with ResearchBot

Ask questions about your indexed documents:

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the chain rule?"}'
```

**Response:**
```json
{
  "reply": "Based on the documents, the chain rule is..."
}
```

### Health Check

```bash
curl http://127.0.0.1:8000/
```

**Response:**
```json
{
  "status": "ok"
}
```

## Using ResearchBot Programmatically

You can also use ResearchBot directly in Python:

```python
from researchbot import ResearchBot

# Initialize the bot
bot = ResearchBot()

# Index your documents
bot.index_documents("./documents")

# Ask questions
answer = bot.research("What is the chain rule?")
print(answer)

# Or use interactive chat mode
bot.chat()
```

## Project Structure

```
research-bot/
├── api/
│   └── index.py          # FastAPI backend
├── frontend/             # Web interface
├── documents/            # Your text documents
├── researchbot.py        # Core ResearchBot class
├── pyproject.toml        # Project dependencies
├── requirements.txt      # Alternative dependency list
├── .env                  # Environment variables (create this)
└── README.md            # This file
```

## How It Works

### Agentic RAG Pipeline

ResearchBot v4 processes queries through a multi-stage LangGraph workflow:

1. **Planning Stage**
   - Analyzes the user's query
   - Decomposes complex questions into focused sub-questions
   - Example: "Compare themes in Moby-Dick and Alice in Wonderland" → separate queries for each book

2. **Retrieval Stage**
   - Performs semantic search using vector embeddings
   - Retrieves top-k relevant document chunks for each sub-question
   - Deduplicates results to avoid redundancy

3. **Synthesis Stage**
   - Combines information from multiple sources
   - Generates coherent findings with proper citations [1], [2], etc.
   - Acknowledges gaps and conflicts in the source material

4. **Reflection Stage**
   - Evaluates the quality of findings (confidence score 0.0-1.0)
   - Determines if more research is needed
   - Can trigger additional retrieval iterations (up to 3 max)

### Document Processing

1. **Loading**: Text files (.txt, .md) are loaded from the specified directory
2. **Chunking**: Documents are split into 1000-character chunks with 200-character overlap
3. **Embedding**: Each chunk is embedded using `text-embedding-3-small` (1536 dimensions)
4. **Storage**: Embeddings are stored in an in-memory Qdrant vector database (COSINE distance)

## API Documentation

Once the server is running, access interactive API docs at:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Dependencies

Key dependencies (see [pyproject.toml](pyproject.toml) for full list):

- `langchain>=0.3.0` - LangChain 1.0 framework
- `langgraph>=0.2.0` - State machine for agentic workflows
- `langchain-openai>=0.2.0` - OpenAI integration
- `langchain-qdrant>=0.2.0` - Qdrant vector store
- `langchain-text-splitters>=0.3.0` - Document splitting
- `qdrant-client>=1.11.0` - Vector database client
- `fastapi>=0.121.2` - Web framework
- `openai>=1.0.0` - OpenAI API

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:

```bash
lsof -ti:8000 | xargs kill -9
```

### OpenAI API Key Error

Make sure your `.env` file exists and contains a valid `OPENAI_API_KEY`.

### No Documents Found

Ensure you've:
1. Created the `documents/` directory
2. Added `.txt` files to it
3. Called the `/api/index` endpoint to index them

### Import Errors

Make sure you've installed dependencies:

```bash
uv sync
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
