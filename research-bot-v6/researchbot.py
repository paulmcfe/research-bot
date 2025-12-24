# researchbot.py
# ResearchBot v6 - Multi-Agent RAG with Native Memory

import os
import glob
from typing import List
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langgraph_supervisor import create_supervisor
from langgraph.store.memory import InMemoryStore
from langmem import create_manage_memory_tool, create_search_memory_tool
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

load_dotenv()


# ============================================================================
# ResearchBot Class
# ============================================================================

class ResearchBot:
    """ResearchBot v6 - Multi-Agent RAG with Native Memory"""

    def __init__(self, collection_name: str = "research_docs"):
        # Initialize LLM
        self.llm = ChatOpenAI(model="gpt-5-nano")

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small"
        )

        # Initialize Qdrant for document storage (RAG)
        self.qdrant_client = QdrantClient(":memory:")
        self.collection_name = collection_name
        self._create_collection()

        self.vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=self.collection_name,
            embedding=self.embeddings
        )

        self.retriever = self.vector_store.as_retriever(
            search_kwargs={"k": 5}
        )

        # Initialize memory store (LangGraph native)
        self.memory_store = InMemoryStore(
            index={
                "dims": 1536,
                "embed": "openai:text-embedding-3-small",
            }
        )

        # Default user for development
        self.current_user_id = "default_user"

        # Build the multi-agent system
        self.graph = self._build_multi_agent_system()

    def _create_collection(self):
        """Create Qdrant collection if it doesn't exist."""
        try:
            self.qdrant_client.get_collection(self.collection_name)
        except Exception:
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=1536,  # text-embedding-3-small dimensions
                    distance=Distance.COSINE
                )
            )

    # ========================================================================
    # Tools
    # ========================================================================

    def _create_memory_tools(self):
        """Create memory management tools for agents."""
        # Tool to save new memories
        manage_memory = create_manage_memory_tool(
            namespace=("memories", "{user_id}"),
            instructions="""Save important information about the user's research:
- Research topics and goals
- Preferences for detail level
- Key findings they've discovered
- Questions they're still exploring""",
            store=self.memory_store
        )

        # Tool to search past memories
        search_memory = create_search_memory_tool(
            namespace=("memories", "{user_id}"),
            store=self.memory_store
        )

        return manage_memory, search_memory

    def _create_search_tool(self):
        """Create the search_documents tool with access to the retriever."""
        retriever = self.retriever

        @tool
        def search_documents(query: str) -> str:
            """Search the knowledge base for documents relevant to the query.

            Args:
                query: The search query to find relevant documents

            Returns:
                A formatted string of relevant document excerpts with source info
            """
            results = retriever.invoke(query)

            if not results:
                return "No relevant documents found for this query."

            # Format results
            formatted = []
            for i, doc in enumerate(results, 1):
                source = doc.metadata.get("source", "Unknown")
                formatted.append(f"[Source {i}: {source}]\n{doc.page_content}")

            return "\n\n---\n\n".join(formatted)

        return search_documents

    # ========================================================================
    # Agent Definitions
    # ========================================================================

    def _build_multi_agent_system(self):
        """Build the multi-agent system with memory."""

        # Create tools
        search_tool = self._create_search_tool()
        manage_memory, search_memory = self._create_memory_tools()

        # ---------------------------------------------------------------------
        # Query Analyst Agent
        # Analyzes queries and creates research plans (no tools - pure reasoning)
        # ---------------------------------------------------------------------
        query_analyst = create_agent(
            model="openai:gpt-5-nano",
            tools=[],
            name="query_analyst",
            system_prompt="""You are the Query Analyst for ResearchBot.

Analyze research questions and create focused plans.
Consider any context about the user's ongoing research
that may inform your analysis.

For simple questions, direct search is sufficient.
For complex questions, break them into sub-questions."""
        )

        # ---------------------------------------------------------------------
        # Document Researcher Agent
        # Searches the knowledge base and retrieves findings
        # ---------------------------------------------------------------------
        document_researcher = create_agent(
            model="openai:gpt-5-nano",
            tools=[search_tool],
            name="document_researcher",
            system_prompt="""You are the Document Researcher.

Search the Vapor Labs archive to find relevant information.
Use the search_documents tool thoroughly.
Note source references for each piece of information."""
        )

        # ---------------------------------------------------------------------
        # Report Writer Agent
        # Synthesizes findings into coherent responses (no tools - pure synthesis)
        # ---------------------------------------------------------------------
        report_writer = create_agent(
            model="openai:gpt-5-nano",
            tools=[],
            name="report_writer",
            system_prompt="""You are the Report Writer.

Synthesize research findings into clear responses.
Cite sources using [Source 1], [Source 2], etc.
Consider the user's research context and preferences
when tailoring your response."""
        )

        # ---------------------------------------------------------------------
        # Research Coordinator (Supervisor)
        # Orchestrates agents and manages memory
        # ---------------------------------------------------------------------
        workflow = create_supervisor(
            agents=[query_analyst, document_researcher, report_writer],
            model=self.llm,
            tools=[manage_memory, search_memory],
            prompt="""You are the Research Coordinator for ResearchBot.

You coordinate a research team:
- query_analyst: Analyzes questions and creates plans
- document_researcher: Searches the knowledge base
- report_writer: Synthesizes findings into responses

MEMORY CAPABILITIES:
1. At the START of each conversation, use search_memory
   to find relevant context about this user's research.
2. Share relevant memories with the team to personalize
   their work.
3. Use manage_memory to save important information:
   - Research topics and goals
   - Discovered key insights
   - User preferences
   - When user explicitly asks to remember something

WORKFLOW:
1. Search memories for context
2. Delegate to query_analyst
3. Delegate to document_researcher
4. Delegate to report_writer
5. Save any new important information to memory"""
        )

        return workflow.compile(store=self.memory_store)

    # ========================================================================
    # Public Methods
    # ========================================================================

    def index_documents(self, directory: str, extensions: List[str] = None):
        """Load and index documents from a directory."""
        if extensions is None:
            extensions = [".txt"]

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

        all_docs = []
        for ext in extensions:
            pattern = os.path.join(directory, f"*{ext}")
            for filepath in glob.glob(pattern):
                try:
                    loader = TextLoader(filepath)
                    docs = loader.load()
                    chunks = splitter.split_documents(docs)
                    all_docs.extend(chunks)
                except Exception as e:
                    print(f"Error loading {filepath}: {e}")

        if all_docs:
            self.vector_store.add_documents(all_docs)
            print(f"Indexed {len(all_docs)} chunks from {directory}")
        else:
            print(f"No documents found in {directory}")

        return len(all_docs)

    def research(self, question: str, user_id: str = None) -> str:
        """
        Conduct research with memory-enhanced context.

        Args:
            question: The research question to investigate
            user_id: Optional user ID for memory isolation

        Returns:
            The research findings as a string
        """
        user_id = user_id or self.current_user_id

        # Invoke with user context for memory
        result = self.graph.invoke(
            {"messages": [HumanMessage(content=question)]},
            config={"configurable": {"user_id": user_id}}
        )

        # Extract the final response from the last message
        messages = result.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content:
                return msg.content

        return "Unable to find relevant information."

    def chat(self):
        """Interactive research session."""
        print("ResearchBot v6 (Multi-Agent) ready. Type 'quit' to exit.")
        print("-" * 50)

        while True:
            question = input("\nYou: ").strip()

            if question.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            if not question:
                continue

            print("\nResearchBot is researching...")
            answer = self.research(question)
            print(f"\nResearchBot: {answer}")


# ============================================================================
# Main (for testing)
# ============================================================================

if __name__ == "__main__":
    # Quick test
    bot = ResearchBot()

    # Test with a sample query
    print("Testing ResearchBot v6 (Multi-Agent)...")
    response = bot.research("What was VaporWare?")
    print(f"\nResponse: {response}")
