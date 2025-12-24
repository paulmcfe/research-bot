# researchbot.py
# ResearchBot v5 - Multi-Agent RAG with LangGraph Supervisor

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
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

load_dotenv()


# ============================================================================
# ResearchBot Class
# ============================================================================

class ResearchBot:
    """ResearchBot v5 - Multi-Agent RAG powered by LangGraph Supervisor"""

    def __init__(self, collection_name: str = "research_docs"):
        # Initialize LLM
        self.llm = ChatOpenAI(model="gpt-5-nano")

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small"
        )

        # Initialize Qdrant (in-memory for development)
        self.qdrant_client = QdrantClient(":memory:")
        self.collection_name = collection_name

        # Create collection
        self._create_collection()

        # Initialize vector store
        self.vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=self.collection_name,
            embedding=self.embeddings
        )

        # Create retriever
        self.retriever = self.vector_store.as_retriever(
            search_kwargs={"k": 5}
        )

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
    # Tools for Document Researcher
    # ========================================================================

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
        """Build the multi-agent supervisor system."""

        # Create the search tool
        search_tool = self._create_search_tool()

        # ---------------------------------------------------------------------
        # Query Analyst Agent
        # Analyzes queries and creates research plans (no tools - pure reasoning)
        # ---------------------------------------------------------------------
        query_analyst = create_agent(
            model="openai:gpt-5-nano",
            tools=[],
            name="query_analyst",
            system_prompt="""You are the Query Analyst for ResearchBot, a research assistant.

Your job is to analyze the user's research question and create a focused research plan.

For each query:
1. Determine if it's a simple, direct question or a complex multi-part question
2. For simple questions, state that direct search is sufficient
3. For complex questions, break them into 2-3 focused sub-questions

Examples:
- "What was VaporWare?" -> Simple query, direct search sufficient
- "Who was Diana Reeves?" -> Simple query, direct search sufficient
- "Why did Vapor Labs fail and what lessons were learned?" -> Complex query, break into:
  - "What caused Vapor Labs to fail?"
  - "What lessons were learned from Vapor Labs?"

Always respond with a clear research plan that the Document Researcher can execute."""
        )

        # ---------------------------------------------------------------------
        # Document Researcher Agent
        # Searches the knowledge base and retrieves findings
        # ---------------------------------------------------------------------
        document_researcher = create_agent(
            model="openai:gpt-5-nano",
            tools=[search_tool],
            name="document_researcher",
            system_prompt="""You are the Document Researcher for ResearchBot.

Your job is to search the knowledge base and find relevant information.

When given a research plan or query:
1. Use the search_documents tool to find relevant information
2. For complex queries with sub-questions, search for each sub-question
3. Compile the key findings from your searches
4. Note the source references for each piece of information

Always be thorough but focused. Search for exactly what's needed, no more."""
        )

        # ---------------------------------------------------------------------
        # Report Writer Agent
        # Synthesizes findings into coherent responses (no tools - pure synthesis)
        # ---------------------------------------------------------------------
        report_writer = create_agent(
            model="openai:gpt-5-nano",
            tools=[],
            name="report_writer",
            system_prompt="""You are the Report Writer for ResearchBot.

Your job is to synthesize research findings into clear, well-organized responses.

When writing your response:
1. Synthesize information from all sources into a coherent answer
2. Cite sources using [Source 1], [Source 2], etc.
3. Note any conflicting information between sources
4. Acknowledge gaps if the sources don't fully answer the question
5. Be thorough but concise
6. Write in a professional, informative tone

Your response should directly answer the user's original question."""
        )

        # ---------------------------------------------------------------------
        # Research Coordinator (Supervisor)
        # Coordinates the specialist agents
        # ---------------------------------------------------------------------
        workflow = create_supervisor(
            agents=[query_analyst, document_researcher, report_writer],
            model=self.llm,
            prompt="""You are the Research Coordinator for ResearchBot, a multi-agent research assistant.

You coordinate a team of specialists to answer research questions:
- query_analyst: Analyzes questions and creates research plans
- document_researcher: Searches the knowledge base for information
- report_writer: Synthesizes findings into clear responses

For each user query, follow this workflow:
1. First, delegate to query_analyst to analyze the question and create a research plan
2. Then, delegate to document_researcher to search for relevant information
3. Finally, delegate to report_writer to synthesize the findings into a response

Always follow this order. After report_writer completes, provide the final response to the user."""
        )

        return workflow.compile()

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

    def research(self, question: str) -> str:
        """
        Conduct research on a question using the multi-agent pipeline.

        Args:
            question: The research question to investigate

        Returns:
            The research findings as a string
        """
        # Invoke the multi-agent graph
        result = self.graph.invoke({
            "messages": [HumanMessage(content=question)]
        })

        # Extract the final response from the last message
        messages = result.get("messages", [])
        if messages:
            # Get the last AI message content
            for msg in reversed(messages):
                if hasattr(msg, "content") and msg.content:
                    return msg.content

        return "I wasn't able to find relevant information for your query."

    def chat(self):
        """Interactive research session."""
        print("ResearchBot v5 (Multi-Agent) ready. Type 'quit' to exit.")
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
    print("Testing ResearchBot v5 (Multi-Agent)...")
    response = bot.research("What was VaporWare?")
    print(f"\nResponse: {response}")
