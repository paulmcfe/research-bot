import os
import glob
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient

load_dotenv()

RESEARCHBOT_PROMPT = """You are ResearchBot, an AI research
assistant.

Your job is to help users find and synthesize information from
the research document collection. When answering questions:

1. Use the search_documents tool to find relevant information
2. Always cite which sources your information comes from
3. If you need more detail from a source, use get_more_context
4. If you can't find relevant information, say so clearly
5. Be thorough but concise in your responses

Think step by step about what information you need before
searching."""


class ResearchBot:
    """A research assistant powered by LangChain 1.0"""
    
    def __init__(self):
        # Initialize vector store
        self.client = QdrantClient(":memory:")
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small"
        )

        # Create collection if it doesn't exist
        from qdrant_client.models import Distance, VectorParams
        collection_name = "research_docs"

        try:
            self.client.get_collection(collection_name)
        except:
            # Collection doesn't exist, create it
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )

        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=collection_name,
            embedding=self.embeddings
        )
        self.retriever = self.vector_store.as_retriever(
            search_kwargs={"k": 5}
        )
        
        # Create tools
        self.tools = self._create_tools()
        
        # Create agent
        self.agent = create_agent(
            model="openai:gpt-5",
            tools=self.tools,
            system_prompt=RESEARCHBOT_PROMPT
        )
    
    def _create_tools(self):
        retriever = self.retriever  # Closure for tools
        
        @tool
        def search_documents(query: str) -> str:
            """Search for relevant research documents."""
            docs = retriever.invoke(query)
            if not docs:
                return "No relevant documents found."
            results = []
            for i, doc in enumerate(docs, 1):
                source = doc.metadata.get("source", "Unknown")
                results.append(f"[{i}] From '{source}':\n{doc.page_content}")
            return "\n\n".join(results)
        
        @tool
        def get_more_context(source_name: str, topic: str) -> str:
            """Get more context from a specific source."""
            docs = retriever.invoke(topic)
            matching = [
                doc for doc in docs
                if source_name.lower() in doc.metadata.get("source", "").lower()
            ]
            if not matching:
                return f"No additional information in '{source_name}'."
            return "\n\n---\n\n".join([d.page_content for d in matching])
        
        return [search_documents, get_more_context]
    
    def index_documents(self, directory: str):
        """Load documents from a directory."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )
        
        all_docs = []
        for filepath in glob.glob(f"{directory}/*.txt"):
            loader = TextLoader(filepath)
            docs = loader.load()
            chunks = splitter.split_documents(docs)
            all_docs.extend(chunks)
        
        if all_docs:
            self.vector_store.add_documents(all_docs)
            print(f"Loaded {len(all_docs)} chunks")
    
    def research(self, question: str) -> str:
        """Ask a research question."""
        result = self.agent.invoke({
            "messages": [
                {"role": "user", "content": question}
            ]
        })
        # Return the final message content
        final_message = result["messages"][-1]
        return final_message.content if hasattr(final_message, 'content') else str(final_message)
    
    def chat(self):
        """Interactive research session."""
        print("ResearchBot ready. Type 'quit' to exit.")
        while True:
            question = input("\nYou: ").strip()
            if question.lower() == "quit":
                break
            if question:
                answer = self.research(question)
                print(f"\nResearchBot: {answer}")
