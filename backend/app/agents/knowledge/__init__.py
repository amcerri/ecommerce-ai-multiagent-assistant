"""
Knowledge agent module (RAG pipeline for knowledge base).

Overview
  Provides complete RAG pipeline for knowledge base queries including retrieval,
  re-ranking, answer generation, chunking, and ingestion. Main entry point is
  KnowledgeAgent which orchestrates the pipeline.

Design
  - **RAG Pipeline**: Retrieval → Re-ranking → Answer generation.
  - **Modular Components**: Separate classes for each pipeline step.
  - **Base Agent**: KnowledgeAgent inherits from BaseAgent.
  - **Repository Pattern**: Uses KnowledgeRepository for data access.

Integration
  - Consumes: BaseAgent, LLMClient, KnowledgeRepository, CacheManager, Storage.
  - Returns: Answer objects with citations and metadata.
  - Used by: LangGraph orchestration, administrative scripts (ingester).
  - Observability: Logs via BaseAgent and individual components.

Usage
  >>> from app.agents.knowledge import KnowledgeAgent
  >>> agent = KnowledgeAgent(llm_client, repository, cache)
  >>> state = await agent.process(state)
"""

from app.agents.knowledge.agent import KnowledgeAgent
from app.agents.knowledge.answerer import KnowledgeAnswerer
from app.agents.knowledge.chunker import KnowledgeChunker
from app.agents.knowledge.ingester import KnowledgeIngester
from app.agents.knowledge.ranker import KnowledgeRanker
from app.agents.knowledge.retriever import KnowledgeRetriever

__all__ = [
    "KnowledgeAgent",
    "KnowledgeRetriever",
    "KnowledgeRanker",
    "KnowledgeAnswerer",
    "KnowledgeChunker",
    "KnowledgeIngester",
]

