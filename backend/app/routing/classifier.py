"""
LLM classifier (semantic-based routing classification).

Overview
  Classifies queries semantically using LLM with structured outputs to determine
  which agent should handle the query. CRITICAL: NEVER uses keywords for routing,
  only semantic understanding based on intent and context.

Design
  - **Semantic Classification**: Uses LLM to understand query intent semantically.
  - **NO Keywords**: NEVER uses keyword matching for routing decisions.
  - **Structured Outputs**: Uses JSON Schema for guaranteed structure.
  - **Caching**: Caches routing decisions for performance.

Integration
  - Consumes: LLMClient, CacheManager, RouterDecision contract.
  - Returns: RouterDecision with selected agent and confidence.
  - Used by: Router for semantic routing.
  - Observability: Logs classification decisions.

Usage
  >>> from app.routing.classifier import LLMClassifier
  >>> classifier = LLMClassifier(llm_client, cache)
  >>> decision = await classifier.classify("How many orders?", embedding, "pt-BR")
"""

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

from app.config.exceptions import LLMException
from app.contracts.router_decision import RouterDecision, RoutingSignal
from app.infrastructure.cache.cache_manager import CacheManager
from app.infrastructure.llm.client import LLMClient

logger = logging.getLogger(__name__)


class LLMClassifier:
    """LLM-based classifier for semantic routing.

    Classifies queries semantically using LLM to determine appropriate agent.
    CRITICAL: NEVER uses keywords, only semantic understanding.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        cache: Optional[CacheManager] = None,
    ) -> None:
        """Initialize LLM classifier.

        Args:
            llm_client: LLM client for classification.
            cache: Cache manager for routing decisions (optional).
        """
        self._llm_client = llm_client
        self._cache = cache

    async def classify(
        self,
        query: str,
        query_embedding: List[float],
        language: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> RouterDecision:
        """Classify query and return routing decision.

        Classifies query semantically using LLM to determine appropriate agent.
        NEVER uses keywords, only semantic understanding of intent.

        Args:
            query: User query.
            query_embedding: Query embedding vector (already generated).
            language: Query language.
            conversation_history: Conversation history for context (optional).

        Returns:
            RouterDecision with selected agent, confidence, and reason.

        Raises:
            LLMException: If classification fails (graceful degradation to triage).
        """
        # Step 1: Check cache
        cache_key = self._generate_cache_key(query_embedding)
        if self._cache:
            try:
                cached_decision = await self._cache.get(cache_key, "routing_decisions")
                if cached_decision:
                    logger.info("Routing decision cache hit")
                    # Convert cached dict back to RouterDecision
                    return RouterDecision(**cached_decision)
            except Exception:
                # Graceful degradation: continue without cache
                pass

        try:
            # Step 2: Build prompt
            prompt = self._build_prompt(query, language, conversation_history)

            # Step 3: Build JSON Schema for structured output
            json_schema = self._build_json_schema()

            # Step 4: Generate classification using structured outputs
            structured_result = await self._llm_client.generate_structured(
                prompt,
                json_schema,
            )

            # Step 5: Extract and validate classification
            agent = structured_result.get("agent", "triage")
            confidence = structured_result.get("confidence", 0.5)
            reason = structured_result.get("reason", "No reason provided")
            signals = structured_result.get("signals", [])

            # Validate agent
            valid_agents = ["knowledge", "analytics", "commerce", "triage"]
            if agent not in valid_agents:
                logger.warning(f"Invalid agent from LLM: {agent}, defaulting to triage")
                agent = "triage"
                confidence = 0.3

            # Step 6: Create RouterDecision
            routing_signals = None
            if signals:
                routing_signals = [
                    RoutingSignal(
                        type=sig.get("type", "unknown"),
                        value=sig.get("value", ""),
                        confidence=sig.get("confidence", 0.5),
                    )
                    for sig in signals
                ]

            decision = RouterDecision(
                agent=agent,
                confidence=confidence,
                reason=reason,
                query_embedding=query_embedding,
                signals=routing_signals,
            )

            # Step 7: Cache result
            if self._cache:
                try:
                    await self._cache.set(
                        cache_key,
                        decision.model_dump(),
                        "routing_decisions",
                    )
                except Exception:
                    # Graceful degradation: continue without caching
                    pass

            return decision

        except Exception as e:
            logger.error(f"Classification failed: {e}, falling back to triage")
            # Graceful degradation: return triage decision
            return RouterDecision(
                agent="triage",
                confidence=0.3,
                reason=f"Classification failed, defaulting to triage: {str(e)}",
                query_embedding=query_embedding,
            )

    def _build_prompt(
        self,
        query: str,
        language: str,
        conversation_history: Optional[List[Dict[str, Any]]],
    ) -> str:
        """Build prompt for semantic classification.

        Constructs prompt instructing LLM to classify query semantically,
        NOT using keywords but understanding intent.

        Args:
            query: User query.
            language: Query language.
            conversation_history: Conversation history (optional).

        Returns:
            Complete prompt string.
        """
        # Build context from conversation history
        context = ""
        if conversation_history:
            context = "\n\nContexto da conversa:\n"
            for msg in conversation_history[-3:]:  # Last 3 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                context += f"{role}: {content}\n"

        prompt = f"""Você é um classificador semântico de intenções. Sua tarefa é classificar a query do usuário baseando-se na INTENÇÃO SEMÂNTICA, NÃO em palavras-chave.

CRÍTICO: NUNCA use palavras-chave para classificar. Entenda a INTENÇÃO por trás da query.

AGENTES DISPONÍVEIS:

1. **knowledge** (Base de Conhecimento):
   - Perguntas conceituais sobre e-commerce, políticas, procedimentos, documentação
   - Perguntas sobre "como funciona", "o que é", "quais são as regras"
   - Busca de informações em documentos e manuais
   - Exemplo: "Como funciona o processo de devolução?" → knowledge (intenção: entender processo)

2. **analytics** (Analytics):
   - Consultas sobre dados tabulares, métricas, análises, agregações
   - Perguntas sobre "quantos", "qual a média", "mostre os dados"
   - Intenção de consultar ou analisar dados numéricos
   - Exemplo: "Quantos pedidos temos este mês?" → analytics (intenção: consultar dados, não a palavra "pedido")

3. **commerce** (Documentos Comerciais):
   - Processamento de documentos comerciais (notas fiscais, pedidos, faturas)
   - Intenção de processar, analisar ou extrair informações de documentos
   - Exemplo: "Processe esta nota fiscal" → commerce (intenção: processar documento)

4. **triage** (Triagem):
   - Saudações, perguntas fora do escopo, pedidos de ajuda
   - Queries que não se encaixam nos outros agentes
   - Exemplo: "Olá!" → triage (intenção: saudação)

REGRAS IMPORTANTES:
- Classifique baseado na INTENÇÃO SEMÂNTICA, não em palavras-chave
- "pedido" pode aparecer em knowledge ("o que é um pedido?") ou analytics ("quantos pedidos?")
- Entenda o CONTEXTO e a INTENÇÃO por trás da query
- Use confidence score baseado na clareza da intenção

QUERY DO USUÁRIO ({language}):
{query}
{context}

Classifique a query baseando-se na INTENÇÃO SEMÂNTICA e retorne o agente apropriado."""
        return prompt

    def _build_json_schema(self) -> Dict[str, Any]:
        """Build JSON Schema for structured output.

        Defines schema for LLM structured output with agent, confidence, reason, signals.

        Returns:
            JSON Schema dictionary.
        """
        return {
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "enum": ["knowledge", "analytics", "commerce", "triage"],
                    "description": "Selected agent based on semantic intent",
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Confidence score (0.0-1.0)",
                },
                "reason": {
                    "type": "string",
                    "description": "Explanation of classification based on semantic intent",
                },
                "signals": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "value": {"type": "string"},
                            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        },
                        "required": ["type", "value", "confidence"],
                    },
                    "description": "Detected routing signals (optional)",
                },
            },
            "required": ["agent", "confidence", "reason"],
        }

    def _generate_cache_key(self, query_embedding: List[float]) -> str:
        """Generate cache key for routing decision.

        Creates cache key from query embedding hash.

        Args:
            query_embedding: Query embedding vector.

        Returns:
            Cache key string.
        """
        # Create hash from embedding
        embedding_str = json.dumps(query_embedding, sort_keys=True)
        key_hash = hashlib.sha256(embedding_str.encode()).hexdigest()
        return f"routing_decision:{key_hash}"

