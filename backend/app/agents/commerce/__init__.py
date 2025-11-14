"""
Commerce agent module (document processing pipeline).

Overview
  Provides complete document processing pipeline for commerce documents including
  multi-format processing, OCR, schema detection, extraction, and analysis. Main
  entry point is CommerceAgent which orchestrates the pipeline.

Design
  - **Document Pipeline**: Processing → Schema Detection → Extraction → Analysis.
  - **Multi-Format Support**: PDF, DOCX, TXT, images with OCR fallback.
  - **Dynamic Schema**: Schema detection and extraction using LLM.
  - **Analysis**: Inconsistency detection, validation, and risk identification.
  - **Base Agent**: CommerceAgent inherits from BaseAgent.

Integration
  - Consumes: BaseAgent, LLMClient, LocalStorage, CommerceRepository.
  - Returns: Answer objects with DocumentMetadata and formatted results.
  - Used by: LangGraph orchestration, document processing workflows.
  - Observability: Logs via BaseAgent and individual components.

Usage
  >>> from app.agents.commerce import CommerceAgent
  >>> agent = CommerceAgent(llm_client, storage, repository)
  >>> state = await agent.process(state)
"""

from app.agents.commerce.agent import CommerceAgent
from app.agents.commerce.analyzer import CommerceAnalyzer
from app.agents.commerce.extractor import CommerceExtractor
from app.agents.commerce.processor import CommerceProcessor
from app.agents.commerce.schema_detector import CommerceSchemaDetector

__all__ = [
    "CommerceAgent",
    "CommerceProcessor",
    "CommerceSchemaDetector",
    "CommerceExtractor",
    "CommerceAnalyzer",
]

