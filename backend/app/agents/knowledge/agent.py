"""
Knowledge agent (RAG pipeline orchestrator).

Overview
  Main orchestrator for Knowledge Agent RAG pipeline. Coordinates retrieval,
  re-ranking, and answer generation. Inherits from BaseAgent for common
  functionality (logging, error handling, state validation).

Design
  - **Pipeline Orchestration**: Coordinates retrieve → rerank → answer pipeline.
  - **Base Agent**: Inherits from BaseAgent for common functionality.
  - **Dependency Injection**: Receives dependencies via constructor.
  - **Error Handling**: Uses BaseAgent error handling.

Integration
  - Consumes: BaseAgent, KnowledgeRetriever, KnowledgeRanker, KnowledgeAnswerer.
  - Returns: Updated GraphState with Answer in agent_response.
  - Used by: LangGraph orchestration layer.
  - Observability: Logs via BaseAgent._log_processing.

Usage
  >>> from app.agents.knowledge.agent import KnowledgeAgent
  >>> agent = KnowledgeAgent(llm_client, repository, cache)
  >>> state = await agent.process(state)
"""

from typing import Any

from app.agents.base import BaseAgent
from app.agents.knowledge.answerer import KnowledgeAnswerer
from app.agents.knowledge.ranker import KnowledgeRanker
from app.agents.knowledge.retriever import KnowledgeRetriever
from app.infrastructure.cache.cache_manager import CacheManager
from app.infrastructure.database.repositories.knowledge_repo import KnowledgeRepository
from app.infrastructure.llm.client import LLMClient


class KnowledgeAgent(BaseAgent):
    """Knowledge Agent with RAG pipeline.

    Orchestrates retrieval, re-ranking, and answer generation for knowledge
    base queries. Inherits from BaseAgent for common functionality.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        repository: KnowledgeRepository,
        cache: CacheManager | None = None,
    ) -> None:
        """Initialize Knowledge Agent.

        Creates retriever, ranker, and answerer instances with dependencies.

        Args:
            llm_client: LLM client for embeddings and answer generation.
            repository: Knowledge repository for database access.
            cache: Cache manager for embedding caching (optional).
        """
        super().__init__(llm_client, name="knowledge")

        # Create pipeline components
        self._retriever = KnowledgeRetriever(repository, llm_client, cache)
        self._ranker = KnowledgeRanker(use_cross_encoder=False)  # Can be configurable
        self._answerer = KnowledgeAnswerer(llm_client)

    async def process(self, state: Any) -> Any:
        """Process query and generate answer.

        Implements abstract method from BaseAgent. Orchestrates RAG pipeline:
        retrieve → rerank → answer. Updates state with Answer.

        Args:
            state: Graph state with query, language, etc.

        Returns:
            Updated state with agent_response containing Answer.
        """
        # Step 1: Validate state
        self._validate_state(state)

        try:
            # Extract query and language from state
            query = getattr(state, "query", "")
            language = getattr(state, "language", "pt-BR")

            # Step 2: Retrieve relevant chunks
            chunks = await self._retriever.retrieve(query)

            # Step 3: Re-rank chunks for improved precision
            reranked_chunks = await self._ranker.rerank(query, chunks)

            # Step 4: Generate answer with citations
            answer = await self._answerer.generate_answer(
                query,
                reranked_chunks,
                language,
            )

            # Step 5: Update state with answer
            if hasattr(state, "agent_response"):
                state.agent_response = answer
            else:
                setattr(state, "agent_response", answer)

            # Step 6: Log processing
            await self._log_processing(state, answer)

            return state
        except Exception as e:
            # Use BaseAgent error handling
            return await self._handle_error(e, state)

