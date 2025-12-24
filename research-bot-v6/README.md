# ResearchBot v6

A multi-agent research assistant built with LangChain 1.0 and LangGraph Supervisor that helps you find and synthesize information from your document collection using coordinated specialist agents with persistent memory.

## Features

- **Multi-Agent Architecture**: Coordinated team of specialist agents using the Supervisor pattern
- **Native Memory**: Remembers user research interests, preferences, and conversation context across sessions
- **Query Analysis**: Dedicated agent for analyzing queries and creating research plans
- **Document Research**: Specialized agent for searching the knowledge base
- **Report Writing**: Focused agent for synthesizing findings into coherent responses
- **Document Indexing**: Load and index text documents (.txt files) into a vector database
- **Semantic Search**: Find relevant information using natural language queries
- **Multi-Source Synthesis**: Combines information from multiple sources with proper citations
- **FastAPI Backend**: RESTful API for chat and document indexing
- **Automatic Indexing**: Documents are indexed automatically at server startup

## Architecture

ResearchBot v6 uses a **LangGraph Supervisor** pattern with four coordinated agents and native memory:

1. **Research Coordinator** (Supervisor): Receives queries, coordinates specialists, manages memory, delivers responses
2. **Query Analyst** (Worker): Analyzes questions and creates focused research plans
3. **Document Researcher** (Worker): Searches the knowledge base using the `search_documents` tool
4. **Report Writer** (Worker): Synthesizes findings into clear, cited responses

**Tech Stack:**
- **Backend**: FastAPI + LangChain 1.0 + LangGraph Supervisor
- **LLM**: OpenAI GPT-5-nano (fast, cost-efficient reasoning model)
- **Embeddings**: OpenAI text-embedding-3-small
- **Vector Database**: Qdrant (in-memory for development)
- **Memory Store**: LangGraph InMemoryStore with semantic search
- **Multi-Agent**: langgraph-supervisor for agent coordination
- **Memory Tools**: langmem for memory management

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

### Multi-Agent Pipeline

ResearchBot v6 processes queries through a coordinated multi-agent workflow:

1. **Research Coordinator** (Supervisor)
   - Receives the user's research question
   - Delegates to specialist agents in sequence
   - Delivers the final synthesized response

2. **Query Analyst**
   - Analyzes the complexity of the query
   - For simple questions: confirms direct search is sufficient
   - For complex questions: breaks them into 2-3 focused sub-questions
   - Example: "Why did Vapor Labs fail and what lessons were learned?" → separate queries for each aspect

3. **Document Researcher**
   - Executes searches against the knowledge base
   - Uses the `search_documents` tool to retrieve relevant content
   - Compiles key findings with source references

4. **Report Writer**
   - Synthesizes all research findings into a coherent response
   - Cites sources using [Source 1], [Source 2], etc.
   - Notes conflicting information and acknowledges gaps

### Document Processing

1. **Loading**: Text files (.txt) are loaded from the `./documents` directory at startup
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
- `langgraph>=0.2.0` - Graph-based agent orchestration
- `langgraph-supervisor>=0.0.30` - Multi-agent supervisor pattern
- `langmem>=0.0.30` - Memory management tools
- `langchain-openai>=0.2.0` - OpenAI integration
- `langchain-qdrant>=0.2.0` - Qdrant vector store
- `langchain-text-splitters>=0.3.0` - Document splitting
- `langsmith>=0.1.0` - Observability and tracing
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
3. Restarted the server (documents are indexed automatically at startup)

### Import Errors

Make sure you've installed dependencies:

```bash
uv sync
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
