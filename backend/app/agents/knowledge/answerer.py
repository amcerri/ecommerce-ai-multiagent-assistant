"""
Knowledge answerer (answer generation with citations).

Overview
  Generates answers with citations using LLM. Parses citation markers from
  LLM response and maps them to document chunks. Calculates character positions
  for frontend highlighting. Implements graceful degradation if citation parsing fails.

Design
  - **Citation Parsing**: Parses [1], [2] markers from LLM response.
  - **Position Calculation**: Calculates character positions for citations.
  - **Mapping**: Maps citation markers to document chunks.
  - **Graceful Degradation**: Returns answer without citations if parsing fails.

Integration
  - Consumes: LLMClient, contracts (Answer, Citation), DocumentChunk models.
  - Returns: Answer object with text, citations, and metadata.
  - Used by: KnowledgeAgent for answer generation step.
  - Observability: Logs answer generation and citation parsing.

Usage
  >>> from app.agents.knowledge.answerer import KnowledgeAnswerer
  >>> answerer = KnowledgeAnswerer(llm_client)
  >>> answer = await answerer.generate_answer("query", chunks, "pt-BR")
"""

import re
from typing import List

from app.config.exceptions import LLMException
from app.contracts.answer import Answer, Citation
from app.infrastructure.database.models.knowledge import DocumentChunk
from app.infrastructure.llm.client import LLMClient


class KnowledgeAnswerer:
    """Answer generator with citations for knowledge base.

    Generates answers using LLM with context from chunks, parses citations,
    and calculates character positions for frontend highlighting.
    """

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize knowledge answerer.

        Args:
            llm_client: LLM client for answer generation.
        """
        self._llm_client = llm_client

    async def generate_answer(
        self,
        query: str,
        chunks: List[DocumentChunk],
        language: str,
    ) -> Answer:
        """Generate answer with citations.

        Generates answer using LLM with context from chunks, parses citations,
        and creates Answer object with citations and metadata.

        Args:
            query: User query text.
            chunks: Relevant chunks (already re-ranked).
            language: Response language (e.g., "pt-BR").

        Returns:
            Answer object with text, citations, and metadata.

        Raises:
            LLMException: If LLM generation fails.
        """
        # Step 1: Build context from chunks
        context = self._build_context(chunks)

        # Step 2: Build prompt
        prompt = self._build_prompt(query, context, language, len(chunks))

        # Step 3: Generate response using LLM
        try:
            response = await self._llm_client.generate(prompt)
            answer_text = response.text
        except Exception as e:
            raise LLMException(
                message=f"Failed to generate answer: {str(e)}",
                details={"query": query[:100], "error": str(e)},
            ) from e

        # Step 4: Parse citations
        try:
            citations, clean_text = self._parse_citations(answer_text, chunks)
        except Exception:
            # Graceful degradation: return answer without citations
            citations = []
            clean_text = answer_text

        # Step 5: Create Answer object
        answer = Answer(
            text=clean_text,
            agent="knowledge",
            language=language,
            citations=citations if citations else None,
        )

        return answer

    def _build_context(self, chunks: List[DocumentChunk]) -> str:
        """Build context string from chunks.

        Concatenates chunk contents with citation markers for LLM.

        Args:
            chunks: List of document chunks.

        Returns:
            Context string with chunk contents and markers.
        """
        context_parts: List[str] = []
        for i, chunk in enumerate(chunks, start=1):
            chunk_text = f"[{i}] {chunk.content}"
            context_parts.append(chunk_text)

        return "\n\n".join(context_parts)

    def _build_prompt(
        self,
        query: str,
        context: str,
        language: str,
        num_chunks: int,
    ) -> str:
        """Build prompt for LLM.

        Constructs prompt instructing LLM to answer in specified language
        and include citations with markers [1], [2], etc.

        Args:
            query: User query.
            context: Context from chunks.
            language: Response language.
            num_chunks: Number of chunks provided.

        Returns:
            Complete prompt string.
        """
        prompt = f"""Você é um assistente especializado em responder perguntas com base em documentos fornecidos.

Responda a pergunta do usuário usando APENAS as informações dos documentos fornecidos abaixo.
Responda no idioma: {language}

IMPORTANTE:
- Use citações [1], [2], [3], etc. para referenciar os documentos usados
- Cada número corresponde ao documento na lista abaixo
- Se você usar informações de um documento, DEVE incluir a citação [número]
- Você pode usar múltiplas citações: [1] [2]
- Se não encontrar informações relevantes, diga que não encontrou

Documentos:
{context}

Pergunta: {query}

Resposta:"""
        return prompt

    def _parse_citations(
        self,
        text: str,
        chunks: List[DocumentChunk],
    ) -> tuple[List[Citation], str]:
        """Parse citations from text and calculate positions.

        Finds citation markers [1], [2], etc. in text, maps them to chunks,
        removes markers from text, and calculates character positions.

        Args:
            text: Text with citation markers.
            chunks: List of chunks (indexed 1-based for citations).

        Returns:
            Tuple of (list of citations, clean text without markers).
        """
        # Find all citation markers [1], [2], etc.
        citation_pattern = r"\[(\d+)\]"
        matches = list(re.finditer(citation_pattern, text))

        if not matches:
            return [], text

        # Build mapping of citation number to chunk
        chunk_map: dict[int, DocumentChunk] = {}
        for i, chunk in enumerate(chunks, start=1):
            chunk_map[i] = chunk

        # Remove markers and track positions
        clean_text = text
        citations: List[Citation] = []
        offset = 0  # Track offset from removed markers

        # Process matches in reverse order to preserve positions
        for match in reversed(matches):
            citation_num = int(match.group(1))
            start_pos = match.start() - offset
            end_pos = match.end() - offset

            # Check if citation number is valid
            if citation_num not in chunk_map:
                # Invalid citation - just remove marker
                clean_text = clean_text[:start_pos] + clean_text[end_pos:]
                offset += match.end() - match.start()
                continue

            chunk = chunk_map[citation_num]

            # Create citation
            citation = Citation(
                document_id=str(chunk.document_id),
                document_title=chunk.document.title if chunk.document else "Unknown",
                file_name=chunk.document.file_name if chunk.document else "Unknown",
                chunk_index=chunk.chunk_index,
                page_number=chunk.page_number,
                content=chunk.content[:200],  # Preview of chunk content
                similarity_score=None,  # Not available at this stage
                start_char=start_pos,
                end_char=start_pos,  # Citations are point references, not ranges
            )

            citations.append(citation)

            # Remove marker from text
            clean_text = clean_text[:start_pos] + clean_text[end_pos:]
            offset += match.end() - match.start()

        # Sort citations by position
        citations.sort(key=lambda c: c.start_char)

        return citations, clean_text

