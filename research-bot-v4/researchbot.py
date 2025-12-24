# researchbot.py
# ResearchBot v4 - Agentic RAG with LangGraph

import os
import glob
import re
from typing import TypedDict, List, Optional
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import StateGraph, END
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

load_dotenv()


# ============================================================================
# State Definition
# ============================================================================

class ResearchBotState(TypedDict):
    research_query: str
    research_plan: Optional[List[str]]   # Sub-questions to investigate
    sources: List[dict]                  # Retrieved research materials
    findings: Optional[str]              # Synthesized research findings
    confidence: Optional[float]          # How confident we are in findings
    iteration: int                       # Current research iteration
    max_iterations: int                  # Prevent infinite loops


# ============================================================================
# ResearchBot Class
# ============================================================================

class ResearchBot:
    """ResearchBot v4 - Agentic RAG powered by LangGraph"""
    
    def __init__(self, collection_name: str = "research_docs"):
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-5-nano"
        )
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small"
        )
        
        # Initialize Qdrant (in-memory for development)
        self.client = QdrantClient(":memory:")
        self.collection_name = collection_name
        
        # Create collection
        self._create_collection()
        
        # Initialize vector store
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings
        )
        
        # Create retriever
        self.retriever = self.vector_store.as_retriever(
            search_kwargs={"k": 5}
        )
        
        # Build the LangGraph agent
        self.graph = self._build_graph()
    
    def _create_collection(self):
        """Create Qdrant collection if it doesn't exist."""
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=1536,  # text-embedding-3-small dimensions
                    distance=Distance.COSINE
                )
            )
    
    # ========================================================================
    # Node Functions
    # ========================================================================
    
    def _planning_node(self, state: ResearchBotState) -> dict:
        """
        Analyzes the research query and creates a research plan.
        Decomposes complex queries into sub-questions for better retrieval.
        """
        query = state["research_query"]

        # Use LLM to decompose the query into sub-questions if needed
        prompt = f"""You are ResearchBot planning a research strategy.

Query: {query}

Break this query into focused sub-questions if it would benefit from multiple searches.
For simple, direct questions, no sub-questions are needed.

Examples:
- "What was VaporWare?" -> No sub-questions needed
- "Who was Diana Reeves?" -> No sub-questions needed
- "Why did Vapor Labs fail and what lessons were learned?" -> "Why did Vapor Labs fail?", "What lessons were learned from Vapor Labs?"

Respond in this exact format:
SUB_QUESTIONS: comma-separated list, or "none" if the original query is sufficient
"""

        response = self.llm.invoke(prompt)
        content = response.content

        # Extract sub-questions if present
        sub_questions = None
        if "SUB_QUESTIONS:" in content:
            sq_line = content.split("SUB_QUESTIONS:")[1].split("\n")[0].strip()
            if sq_line and sq_line.lower() not in ["none", "n/a", ""]:
                sub_questions = [q.strip() for q in sq_line.split(",") if q.strip()]

        return {
            "needs_clarification": False,
            "research_plan": sub_questions
        }
    
    def _retrieval_node(self, state: ResearchBotState) -> dict:
        """
        Retrieves sources based on the research plan.
        """
        # Get queries from the research plan, or use the main query
        queries = state.get("research_plan") or [state["research_query"]]
        
        all_sources = []
        for query in queries:
            try:
                results = self.retriever.invoke(query)
                for doc in results:
                    all_sources.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "query": query
                    })
            except Exception:
                # No documents found for this query
                pass
        
        # Deduplicate by content
        seen_content = set()
        unique_sources = []
        for source in all_sources:
            content_hash = hash(source["content"][:200])
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_sources.append(source)
        
        return {"sources": unique_sources}
    
    def _synthesis_node(self, state: ResearchBotState) -> dict:
        """
        Synthesizes research findings from retrieved sources.
        """
        query = state["research_query"]
        sources = state["sources"]
        
        if not sources:
            return {
                "findings": "I couldn't find any relevant information in my knowledge base to answer your research question. Could you try rephrasing your query or ask about a different topic?"
            }
        
        # Format sources for the LLM
        context = "\n\n".join([
            f"[Source {i+1}] {source['content']}"
            for i, source in enumerate(sources)
        ])
        
        prompt = f"""You are ResearchBot synthesizing research findings.

Research Question: {query}

Sources:
{context}

Instructions:
- Synthesize the information into clear, well-organized findings
- Cite sources using [1], [2], etc.
- Note any conflicting information between sources
- Acknowledge gaps if the sources don't fully answer the question
- Be thorough but concise

Research Findings:
"""
        
        response = self.llm.invoke(prompt)
        return {"findings": response.content}
    
    def _reflection_node(self, state: ResearchBotState) -> dict:
        """
        Evaluates the quality of research findings and calculates confidence.
        """
        findings = state["findings"]
        query = state["research_query"]
        
        prompt = f"""Evaluate these research findings on a scale of 0.0 to 1.0:

Original Question: {query}
Findings: {findings}

Consider:
- Does it fully address the question?
- Is it well-supported by cited sources?
- Are there significant gaps?

Respond with ONLY a number between 0.0 and 1.0:
"""
        
        response = self.llm.invoke(prompt)
        
        try:
            # Extract the confidence score
            score_text = response.content.strip()
            # Handle cases like "0.8" or "Confidence: 0.8"
            numbers = re.findall(r"0?\.\d+|1\.0|0|1", score_text)
            confidence = float(numbers[0]) if numbers else 0.7
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        except (ValueError, IndexError):
            confidence = 0.7  # Default if parsing fails
        
        return {
            "confidence": confidence,
            "iteration": state.get("iteration", 0) + 1
        }
    
    # ========================================================================
    # Edge Functions (Conditional Routing)
    # ========================================================================

    def _should_continue(self, state: ResearchBotState) -> str:
        """
        Decides if ResearchBot needs more research or should finish.
        """
        iteration = state.get("iteration", 0)
        max_iterations = state.get("max_iterations", 3)
        confidence = state.get("confidence", 0)
        
        if iteration >= max_iterations:
            return "end"
        elif confidence < 0.6:
            # Not confident enough, try more research
            return "retrieve"
        else:
            return "end"
    
    # ========================================================================
    # Graph Construction
    # ========================================================================
    
    def _build_graph(self):
        """Build the LangGraph state machine for ResearchBot."""
        
        # Create the graph
        graph = StateGraph(ResearchBotState)
        
        # Add nodes
        graph.add_node("plan", self._planning_node)
        graph.add_node("retrieve", self._retrieval_node)
        graph.add_node("synthesize", self._synthesis_node)
        graph.add_node("reflect", self._reflection_node)
        
        # Set entry point
        graph.set_entry_point("plan")

        # After planning, always retrieve
        graph.add_edge("plan", "retrieve")

        # After retrieval, always synthesize
        graph.add_edge("retrieve", "synthesize")
        
        # After synthesis, always reflect
        graph.add_edge("synthesize", "reflect")
        
        # From reflection, conditionally continue or end
        graph.add_conditional_edges(
            "reflect",
            self._should_continue,
            {
                "retrieve": "retrieve",
                "end": END
            }
        )
        
        # Compile the graph
        return graph.compile()
    
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
        Conduct research on a question using the agentic RAG pipeline.
        
        Args:
            question: The research question to investigate
            
        Returns:
            The research findings as a string
        """
        # Initialize state
        initial_state = {
            "research_query": question,
            "research_plan": None,
            "sources": [],
            "findings": None,
            "confidence": None,
            "iteration": 0,
            "max_iterations": 3
        }

        # Run the graph
        result = self.graph.invoke(initial_state)

        return result.get("findings", "I wasn't able to find relevant information for your query.")
    
    def chat(self):
        """Interactive research session."""
        print("ResearchBot v3 (Agentic RAG) ready. Type 'quit' to exit.")
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
    print("Testing ResearchBot v3...")
    response = bot.research("What is retrieval augmented generation?")
    print(f"\nResponse: {response}")