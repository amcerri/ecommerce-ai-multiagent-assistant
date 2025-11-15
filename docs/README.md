# Documentation

This documentation set provides an in-depth, implementation-level reference for the E-Commerce AI Multi-Agent Assistant, covering architecture, API, development, operations, and troubleshooting.

## Overview

The E-Commerce AI Multi-Agent Assistant is a multi-agent system built on LangGraph that provides assistance for e-commerce analytics, knowledge retrieval (RAG), and commerce document processing. The system uses semantic routing with LLM-first approaches while maintaining fallbacks for reliability.

### Key Features

- **Multi-Agent Architecture**: Four specialized agents (Analytics, Knowledge, Commerce, Triage) with semantic routing
- **LLM-First Design**: Prompt engineering with Chain-of-Thought reasoning, self-consistency checks, and confidence calibration
- **Performance Optimization**: Semantic caching for routing, embeddings, and responses
- **Cost Tracking**: Automatic LLM cost calculation and monitoring with Prometheus metrics
- **Multi-Language Support**: Native support for multiple languages (PT-BR, EN-US, ES-ES, FR-FR, DE-DE) with automatic detection
- **Fallbacks**: Deterministic heuristics when LLMs are unavailable
- **Safety**: Multiple layers of protection including allowlists, read-only transactions, and human approval gates
- **Observability**: Structured logging, metrics, and distributed tracing

## Documentation Index

### Development

- **[Setup Guide](development/setup.md)** - Environment setup, installation, and configuration
- **[API Documentation](api/endpoints.md)** - Complete API reference with request/response examples
- **[API Overview](api/README.md)** - API overview and quick reference

### Operations

- **[Deployment](operations/deployment.md)** - Production deployment guide with Docker and manual setup
- **[Troubleshooting](operations/troubleshooting.md)** - Common issues, diagnostic procedures, and solutions

## Key Concepts

### Semantic Routing

- **Router (LLM Classifier)**: Primary decision maker using LLM with semantic analysis
  - Implementation: [backend/app/routing/router.py](../backend/app/routing/router.py) and [backend/app/routing/classifier.py](../backend/app/routing/classifier.py)
  - Analyzes query intent, context, and signals
  - Uses prompt engineering with Chain-of-Thought reasoning
  - Produces structured RouterDecision with confidence scores
  - Falls back to deterministic heuristics when LLM unavailable
  - Semantic caching for routing decisions to improve performance

- **Supervisor**: Deterministic guardrails and fallback logic
  - Applies business rules and safety constraints
  - Handles single-pass fallbacks to avoid routing loops
  - Recalibrates confidence scores conservatively
  - Enforces commerce document dominance when detected

### Agent Specializations

1. **Analytics Agent**: Converts natural language to safe SQL
   - Implementation: [backend/app/agents/analytics/agent.py](../backend/app/agents/analytics/agent.py)
   - Planner: NL → SQL with allowlist validation - [backend/app/agents/analytics/planner.py](../backend/app/agents/analytics/planner.py)
   - Executor: Read-only SQL execution with safety guards - [backend/app/agents/analytics/executor.py](../backend/app/agents/analytics/executor.py)
   - Normalizer: Data balancing and multi-language responses - [backend/app/agents/analytics/normalizer.py](../backend/app/agents/analytics/normalizer.py)

2. **Knowledge Agent (RAG)**: Retrieves and synthesizes information
   - Implementation: [backend/app/agents/knowledge/agent.py](../backend/app/agents/knowledge/agent.py)
   - Retriever: Vector search with pgvector embeddings - [backend/app/agents/knowledge/retriever.py](../backend/app/agents/knowledge/retriever.py)
   - Ranker: Heuristic + optional LLM reranking - [backend/app/agents/knowledge/ranker.py](../backend/app/agents/knowledge/ranker.py)
   - Answerer: Cross-validated responses with citations - [backend/app/agents/knowledge/answerer.py](../backend/app/agents/knowledge/answerer.py)

3. **Commerce Agent**: Processes commercial documents
   - Implementation: [backend/app/agents/commerce/agent.py](../backend/app/agents/commerce/agent.py)
   - Processor: Multi-format document extraction (PDF/DOCX/TXT/OCR) - [backend/app/agents/commerce/processor.py](../backend/app/agents/commerce/processor.py)
   - Extractor: Structured data extraction with LLM - [backend/app/agents/commerce/extractor.py](../backend/app/agents/commerce/extractor.py)
   - Summarizer: Executive summaries with risk analysis - [backend/app/agents/commerce/summarizer.py](../backend/app/agents/commerce/summarizer.py)

4. **Triage Agent**: Handles ambiguous or insufficient context queries
   - Implementation: [backend/app/agents/triage/agent.py](../backend/app/agents/triage/agent.py)
   - Provides guidance and follow-up questions
   - Suggests appropriate agents based on signals

### Graph Orchestration

The LangGraph orchestration is defined in [backend/app/graph/build.py](../backend/app/graph/build.py):

- **Graph State**: [backend/app/graph/state.py](../backend/app/graph/state.py)
- **Nodes**: [backend/app/graph/nodes.py](../backend/app/graph/nodes.py)
- **Edges**: [backend/app/graph/edges.py](../backend/app/graph/edges.py)
- **Builder**: [backend/app/graph/builder.py](../backend/app/graph/builder.py)

### Infrastructure

- **Database**: [backend/app/infrastructure/database/connection.py](../backend/app/infrastructure/database/connection.py)
- **Cache**: [backend/app/infrastructure/cache/cache_manager.py](../backend/app/infrastructure/cache/cache_manager.py)
- **LLM Client**: [backend/app/infrastructure/llm/client.py](../backend/app/infrastructure/llm/client.py)
- **Storage**: [backend/app/infrastructure/storage/local_storage.py](../backend/app/infrastructure/storage/local_storage.py)
- **Logging**: [backend/app/infrastructure/logging/logger.py](../backend/app/infrastructure/logging/logger.py)
- **Metrics**: [backend/app/infrastructure/metrics/collector.py](../backend/app/infrastructure/metrics/collector.py)
- **Tracing**: [backend/app/infrastructure/tracing/tracer.py](../backend/app/infrastructure/tracing/tracer.py)

### Configuration

- **Settings**: [backend/app/config/settings.py](../backend/app/config/settings.py)
- **Constants**: [backend/app/config/constants.py](../backend/app/config/constants.py)
- **Exceptions**: [backend/app/config/exceptions.py](../backend/app/config/exceptions.py)

## How to Read This Documentation

### For New Team Members

1. Start with [Setup Guide](development/setup.md) for environment setup
2. Read [API Documentation](api/endpoints.md) for API usage
3. Review [Troubleshooting](operations/troubleshooting.md) for common issues

### For Developers

1. [Setup Guide](development/setup.md) - Environment and configuration
2. [API Documentation](api/endpoints.md) - API reference and examples
3. [Operations](operations/deployment.md) - Deployment procedures

### For Operations/SRE

1. [Operations](operations/deployment.md) - Deployment and runbooks
2. [Troubleshooting](operations/troubleshooting.md) - Diagnostic procedures
3. [API Documentation](api/endpoints.md) - Health checks and endpoints

## Conventions

- **Code references**: Use repository-relative paths (e.g., `backend/app/agents/analytics/agent.py`)
- **Configuration**: References to `backend/app/config/*.py` and environment variables
- **Metrics**: Follow Prometheus naming conventions
- **Logging**: Use structured logging with context variables
- **Testing**: Unit tests in `backend/tests/unit/`, integration tests in `backend/tests/integration/`, E2E tests in `backend/tests/e2e/`
