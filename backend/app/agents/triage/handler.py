"""
Triage handler (query classification and response generation).

Overview
  Identifies and handles different types of out-of-scope queries including
  greetings, clarification requests, help requests, and general out-of-scope
  queries. Generates human-friendly responses with actionable suggestions.

Design
  - **Query Classification**: Uses LLM to classify query types.
  - **Response Generation**: Generates appropriate responses for each type.
  - **Actionable Suggestions**: Provides suggestions for user actions.
  - **Language Support**: Responds in specified language.

Integration
  - Consumes: LLMClient.
  - Returns: Response dictionary with type, text, and suggestions.
  - Used by: TriageAgent for query handling.
  - Observability: Logs query classification and response generation.

Usage
  >>> from app.agents.triage.handler import TriageHandler
  >>> handler = TriageHandler(llm_client)
  >>> result = await handler.handle("Olá!", "pt-BR")
"""

import logging
from typing import Any, Dict

from app.config.exceptions import LLMException
from app.infrastructure.llm.client import LLMClient

logger = logging.getLogger(__name__)


class TriageHandler:
    """Handler for out-of-scope queries.

    Identifies query types and generates appropriate human-friendly responses
    with actionable suggestions.
    """

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize triage handler.

        Args:
            llm_client: LLM client for classification and response generation.
        """
        self._llm_client = llm_client

    async def handle(self, query: str, language: str) -> Dict[str, Any]:
        """Handle query and generate appropriate response.

        Classifies query type and generates human-friendly response with
        actionable suggestions.

        Args:
            query: User query.
            language: Response language.

        Returns:
            Dictionary with response_type, text, suggestions.

        Raises:
            LLMException: If classification or response generation fails.
        """
        try:
            # Step 1: Classify query type
            query_type = await self._classify_query(query, language)

            # Step 2: Generate response based on type
            response_text = await self._generate_response(query, query_type, language)

            # Step 3: Generate suggestions
            suggestions = await self._generate_suggestions(query_type, language)

            return {
                "response_type": query_type,
                "text": response_text,
                "suggestions": suggestions,
            }
        except Exception as e:
            # Graceful degradation: return generic response
            logger.warning(f"Triage handler failed: {e}, returning generic response")
            return self._get_generic_response(language)

    async def _classify_query(self, query: str, language: str) -> str:
        """Classify query type.

        Uses LLM to classify query into categories: greeting, out_of_scope,
        clarification, help, or other.

        Args:
            query: User query.
            language: Query language.

        Returns:
            Query type string.
        """
        try:
            prompt = f"""Classifique a seguinte query do usuário em uma das categorias:
- "greeting": Saudação (olá, oi, bom dia, etc.)
- "out_of_scope": Fora do escopo do sistema
- "clarification": Precisa de esclarecimento
- "help": Pedido de ajuda
- "other": Outro tipo

Query: {query}

Responda APENAS com uma das categorias acima (sem aspas, sem explicação)."""

            response = await self._llm_client.generate(prompt)
            query_type = response.text.strip().lower()

            # Validate and normalize
            valid_types = ["greeting", "out_of_scope", "clarification", "help", "other"]
            if query_type not in valid_types:
                # Default to "other" if classification is invalid
                query_type = "other"

            return query_type
        except Exception as e:
            logger.warning(f"Query classification failed: {e}, defaulting to 'other'")
            return "other"

    async def _generate_response(
        self,
        query: str,
        query_type: str,
        language: str,
    ) -> str:
        """Generate response based on query type.

        Generates appropriate human-friendly response for each query type.

        Args:
            query: User query.
            query_type: Classified query type.
            language: Response language.

        Returns:
            Response text.
        """
        try:
            if query_type == "greeting":
                return await self._generate_greeting_response(language)
            elif query_type == "out_of_scope":
                return await self._generate_out_of_scope_response(query, language)
            elif query_type == "clarification":
                return await self._generate_clarification_response(language)
            elif query_type == "help":
                return await self._generate_help_response(language)
            else:
                return await self._generate_generic_response(query, language)
        except Exception as e:
            logger.warning(f"Response generation failed: {e}, using fallback")
            return self._get_fallback_response(query_type, language)

    async def _generate_greeting_response(self, language: str) -> str:
        """Generate greeting response.

        Generates friendly greeting response offering help.

        Args:
            language: Response language.

        Returns:
            Greeting response text.
        """
        if language.startswith("pt"):
            return """Olá! 👋

Sou seu assistente de e-commerce. Posso ajudá-lo com:

📚 **Base de Conhecimento**: Responder perguntas sobre produtos, políticas, processos
📊 **Analytics**: Consultar dados e gerar relatórios
📄 **Documentos Comerciais**: Processar e analisar documentos (notas fiscais, pedidos, etc.)

Como posso ajudá-lo hoje?"""
        else:
            return """Hello! 👋

I'm your e-commerce assistant. I can help you with:

📚 **Knowledge Base**: Answer questions about products, policies, processes
📊 **Analytics**: Query data and generate reports
📄 **Commercial Documents**: Process and analyze documents (invoices, orders, etc.)

How can I help you today?"""

    async def _generate_out_of_scope_response(
        self,
        query: str,
        language: str,
    ) -> str:
        """Generate out-of-scope response.

        Explains that query is out of scope and suggests what can be done.

        Args:
            query: User query.
            language: Response language.

        Returns:
            Out-of-scope response text.
        """
        if language.startswith("pt"):
            return f"""Entendo sua pergunta, mas ela está fora do escopo do que posso fazer no momento.

Sua pergunta: "{query}"

Posso ajudá-lo com:
- 📚 Perguntas sobre produtos, políticas e processos (Base de Conhecimento)
- 📊 Consultas e análises de dados (Analytics)
- 📄 Processamento de documentos comerciais (notas fiscais, pedidos, etc.)

Se você tiver uma pergunta relacionada a essas áreas, ficarei feliz em ajudar!"""
        else:
            return f"""I understand your question, but it's outside the scope of what I can do right now.

Your question: "{query}"

I can help you with:
- 📚 Questions about products, policies, and processes (Knowledge Base)
- 📊 Data queries and analysis (Analytics)
- 📄 Commercial document processing (invoices, orders, etc.)

If you have a question related to these areas, I'll be happy to help!"""

    async def _generate_clarification_response(self, language: str) -> str:
        """Generate clarification response.

        Asks for clarification about what user needs.

        Args:
            language: Response language.

        Returns:
            Clarification response text.
        """
        if language.startswith("pt"):
            return """Preciso de mais informações para ajudá-lo melhor.

Você pode:
- 📚 Fazer uma pergunta sobre produtos, políticas ou processos
- 📊 Solicitar uma análise ou consulta de dados
- 📄 Enviar um documento comercial para processamento

Pode reformular sua pergunta ou me dizer especificamente o que você precisa?"""
        else:
            return """I need more information to help you better.

You can:
- 📚 Ask a question about products, policies, or processes
- 📊 Request data analysis or queries
- 📄 Send a commercial document for processing

Can you rephrase your question or tell me specifically what you need?"""

    async def _generate_help_response(self, language: str) -> str:
        """Generate help response.

        Provides information about system capabilities.

        Args:
            language: Response language.

        Returns:
            Help response text.
        """
        if language.startswith("pt"):
            return """Claro! Posso ajudá-lo com várias coisas:

📚 **Base de Conhecimento**
   - Responder perguntas sobre produtos, políticas, processos
   - Buscar informações em documentos e manuais
   - Exemplo: "Como funciona o processo de devolução?"

📊 **Analytics**
   - Consultar dados e gerar relatórios
   - Análises de vendas, pedidos, clientes
   - Exemplo: "Quantos pedidos tivemos este mês?"

📄 **Documentos Comerciais**
   - Processar e analisar documentos (notas fiscais, pedidos, etc.)
   - Extrair informações automaticamente
   - Exemplo: Enviar uma nota fiscal para análise

O que você gostaria de fazer?"""
        else:
            return """Of course! I can help you with several things:

📚 **Knowledge Base**
   - Answer questions about products, policies, processes
   - Search information in documents and manuals
   - Example: "How does the return process work?"

📊 **Analytics**
   - Query data and generate reports
   - Sales, orders, customer analysis
   - Example: "How many orders did we have this month?"

📄 **Commercial Documents**
   - Process and analyze documents (invoices, orders, etc.)
   - Automatically extract information
   - Example: Send an invoice for analysis

What would you like to do?"""

    async def _generate_generic_response(
        self,
        query: str,
        language: str,
    ) -> str:
        """Generate generic response.

        Generates helpful generic response for unclassified queries.

        Args:
            query: User query.
            language: Response language.

        Returns:
            Generic response text.
        """
        if language.startswith("pt"):
            return f"""Entendi sua mensagem. Posso ajudá-lo com:

📚 Perguntas sobre produtos, políticas e processos
📊 Consultas e análises de dados
📄 Processamento de documentos comerciais

Pode reformular sua pergunta de forma mais específica? Por exemplo:
- "Quantos pedidos tivemos este mês?"
- "Como funciona o processo de devolução?"
- "Processe esta nota fiscal" """
        else:
            return f"""I understand your message. I can help you with:

📚 Questions about products, policies, and processes
📊 Data queries and analysis
📄 Commercial document processing

Can you rephrase your question more specifically? For example:
- "How many orders did we have this month?"
- "How does the return process work?"
- "Process this invoice" """

    async def _generate_suggestions(
        self,
        query_type: str,
        language: str,
    ) -> list[str]:
        """Generate actionable suggestions.

        Generates suggestions for user actions based on query type.

        Args:
            query_type: Classified query type.
            language: Response language.

        Returns:
            List of suggestion strings.
        """
        if language.startswith("pt"):
            if query_type == "greeting":
                return [
                    "Fazer uma pergunta sobre produtos ou políticas",
                    "Consultar dados e gerar relatórios",
                    "Processar um documento comercial",
                ]
            elif query_type == "out_of_scope":
                return [
                    "Tentar uma pergunta sobre produtos ou políticas",
                    "Solicitar uma análise de dados",
                    "Enviar um documento para processamento",
                ]
            elif query_type == "clarification":
                return [
                    "Reformular a pergunta de forma mais específica",
                    "Fornecer mais detalhes sobre o que você precisa",
                ]
            elif query_type == "help":
                return [
                    "Fazer uma pergunta sobre produtos ou políticas",
                    "Consultar dados e gerar relatórios",
                    "Processar um documento comercial",
                ]
            else:
                return [
                    "Fazer uma pergunta sobre produtos ou políticas",
                    "Consultar dados e gerar relatórios",
                    "Processar um documento comercial",
                ]
        else:
            if query_type == "greeting":
                return [
                    "Ask a question about products or policies",
                    "Query data and generate reports",
                    "Process a commercial document",
                ]
            elif query_type == "out_of_scope":
                return [
                    "Try asking about products or policies",
                    "Request data analysis",
                    "Send a document for processing",
                ]
            elif query_type == "clarification":
                return [
                    "Rephrase the question more specifically",
                    "Provide more details about what you need",
                ]
            elif query_type == "help":
                return [
                    "Ask a question about products or policies",
                    "Query data and generate reports",
                    "Process a commercial document",
                ]
            else:
                return [
                    "Ask a question about products or policies",
                    "Query data and generate reports",
                    "Process a commercial document",
                ]

    def _get_generic_response(self, language: str) -> Dict[str, Any]:
        """Get generic response for graceful degradation.

        Returns generic response when handler fails.

        Args:
            language: Response language.

        Returns:
            Generic response dictionary.
        """
        if language.startswith("pt"):
            return {
                "response_type": "other",
                "text": "Desculpe, não consegui processar sua mensagem. Posso ajudá-lo com perguntas sobre produtos, análises de dados, ou processamento de documentos. Pode reformular sua pergunta?",
                "suggestions": [
                    "Fazer uma pergunta sobre produtos ou políticas",
                    "Consultar dados e gerar relatórios",
                    "Processar um documento comercial",
                ],
            }
        else:
            return {
                "response_type": "other",
                "text": "Sorry, I couldn't process your message. I can help you with questions about products, data analysis, or document processing. Can you rephrase your question?",
                "suggestions": [
                    "Ask a question about products or policies",
                    "Query data and generate reports",
                    "Process a commercial document",
                ],
            }

    def _get_fallback_response(self, query_type: str, language: str) -> str:
        """Get fallback response when generation fails.

        Returns fallback response text for specific query type.

        Args:
            query_type: Query type.
            language: Response language.

        Returns:
            Fallback response text.
        """
        if language.startswith("pt"):
            return "Desculpe, não consegui gerar uma resposta apropriada. Posso ajudá-lo com perguntas sobre produtos, análises de dados, ou processamento de documentos. Pode reformular sua pergunta?"
        else:
            return "Sorry, I couldn't generate an appropriate response. I can help you with questions about products, data analysis, or document processing. Can you rephrase your question?"

