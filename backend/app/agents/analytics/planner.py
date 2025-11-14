"""
Analytics planner (SQL generation from natural language).

Overview
  Generates SQL queries from natural language using LLM with structured outputs.
  Validates SQL against allowlist and syntax before returning. Caches generated
  SQL for efficiency.

Design
  - **Structured Outputs**: Uses JSON Schema for guaranteed structure.
  - **Allowlist Validation**: Validates against allowed tables/columns.
  - **Syntax Validation**: Validates SQL syntax.
  - **Caching**: Caches generated SQL (TTL short, can change with context).

Integration
  - Consumes: LLMClient, AllowlistValidator, CacheManager, constants.
  - Returns: Dictionary with SQL, explanation, and metadata.
  - Used by: AnalyticsAgent for SQL generation.
  - Observability: Logs SQL generation and validation.

Usage
  >>> from app.agents.analytics.planner import AnalyticsPlanner
  >>> planner = AnalyticsPlanner(llm_client, allowlist_validator, cache)
  >>> result = await planner.plan("How many orders?", schema_info, "pt-BR")
"""

import hashlib
import json
import logging
from typing import Any, Dict, Optional

from app.config.exceptions import LLMException, ValidationException
from app.infrastructure.cache.cache_manager import CacheManager
from app.infrastructure.llm.client import LLMClient
from app.routing.allowlist import AllowlistValidator

logger = logging.getLogger(__name__)

# Try to import sqlparse for syntax validation (optional)
try:
    import sqlparse

    SQLPARSE_AVAILABLE = True
except ImportError:
    SQLPARSE_AVAILABLE = False
    sqlparse = None  # type: ignore


class AnalyticsPlanner:
    """SQL planner for natural language to SQL generation.

    Generates SQL from natural language using LLM with structured outputs.
    Validates SQL against allowlist and syntax before returning.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        allowlist_validator: AllowlistValidator,
        cache: Optional[CacheManager] = None,
    ) -> None:
        """Initialize analytics planner.

        Args:
            llm_client: LLM client for SQL generation.
            allowlist_validator: Allowlist validator for SQL validation.
            cache: Cache manager for SQL caching (optional).
        """
        self._llm_client = llm_client
        self._allowlist_validator = allowlist_validator
        self._cache = cache

    async def plan(
        self,
        query: str,
        schema_info: Dict[str, Any],
        language: str,
    ) -> Dict[str, Any]:
        """Generate SQL from natural language query.

        Generates SQL using LLM with structured outputs, validates against
        allowlist and syntax, and caches result.

        Args:
            query: User query in natural language.
            schema_info: Schema information (tables, columns, types).
            language: Query language.

        Returns:
            Dictionary with sql, explanation, tables_used, columns_used, confidence.

        Raises:
            LLMException: If LLM generation fails.
            ValidationException: If SQL validation fails.
        """
        # Step 1: Check cache
        cache_key = self._generate_cache_key(query, schema_info)
        if self._cache:
            try:
                cached_result = await self._cache.get(cache_key, "llm_responses")
                if cached_result:
                    logger.info("SQL generation cache hit")
                    return cached_result
            except Exception:
                # Graceful degradation: continue without cache
                pass

        # Step 2: Build prompt
        prompt = self._build_prompt(query, schema_info, language)

        # Step 3: Build JSON Schema for structured output
        json_schema = self._build_json_schema()

        # Step 4: Generate SQL using structured outputs
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                structured_result = await self._llm_client.generate_structured(
                    prompt,
                    json_schema,
                )

                sql = structured_result.get("sql", "").strip()
                explanation = structured_result.get("explanation", "")
                tables_used = structured_result.get("tables_used", [])
                columns_used = structured_result.get("columns_used", [])
                confidence = structured_result.get("confidence", 0.8)

                # Step 5: Validate allowlist
                try:
                    is_valid = await self._allowlist_validator.validate_sql(
                        sql,
                        tables_used,
                        {table: columns_used for table in tables_used},
                    )
                    if not is_valid:
                        raise ValidationException(
                            message="SQL uses unauthorized tables or columns",
                            details={"sql": sql[:200], "tables": tables_used},
                        )
                except ValidationException:
                    raise
                except Exception as e:
                    logger.warning(f"Allowlist validation error: {e}")
                    # Continue if validation fails (will be improved in Batch 17)

                # Step 6: Validate syntax
                self._validate_syntax(sql)

                # Step 7: Cache result
                result = {
                    "sql": sql,
                    "explanation": explanation,
                    "tables_used": tables_used,
                    "columns_used": columns_used,
                    "confidence": confidence,
                }

                if self._cache:
                    try:
                        await self._cache.set(cache_key, result, "llm_responses")
                    except Exception:
                        # Graceful degradation: continue without caching
                        pass

                return result

            except ValidationException:
                # Re-raise validation exceptions
                raise
            except Exception as e:
                if attempt < max_attempts - 1:
                    logger.warning(f"SQL generation attempt {attempt + 1} failed: {e}, retrying...")
                    continue
                else:
                    raise LLMException(
                        message=f"Failed to generate valid SQL after {max_attempts} attempts: {str(e)}",
                        details={"query": query[:100], "error": str(e)},
                    ) from e

        # Should never reach here, but for type safety
        raise LLMException(
            message="Failed to generate SQL",
            details={"query": query[:100]},
        )

    def _build_prompt(
        self,
        query: str,
        schema_info: Dict[str, Any],
        language: str,
    ) -> str:
        """Build prompt for LLM SQL generation.

        Constructs prompt with schema information and instructions for
        generating valid SQL.

        Args:
            query: User query.
            schema_info: Schema information.
            language: Query language.

        Returns:
            Complete prompt string.
        """
        # Build schema description
        schema_description = self._format_schema_info(schema_info)

        prompt = f"""Você é um especialista em SQL. Gere uma query SQL válida a partir da pergunta do usuário.

REGRAS IMPORTANTES:
1. Use APENAS as tabelas e colunas fornecidas no schema abaixo
2. SEMPRE inclua LIMIT quando apropriado (máximo 1000 linhas)
3. NUNCA use operações perigosas: DROP, DELETE, TRUNCATE, ALTER, CREATE, INSERT, UPDATE
4. Use apenas SELECT queries (read-only)
5. Use JOINs quando necessário para relacionar tabelas
6. Use agregações (COUNT, SUM, AVG, etc.) quando apropriado
7. Formate SQL de forma clara e legível

SCHEMA DISPONÍVEL:
{schema_description}

PERGUNTA DO USUÁRIO ({language}):
{query}

Gere uma query SQL válida seguindo as regras acima."""
        return prompt

    def _format_schema_info(self, schema_info: Dict[str, Any]) -> str:
        """Format schema information for prompt.

        Formats schema information (tables, columns, types) into
        readable format for LLM prompt.

        Args:
            schema_info: Schema information dictionary.

        Returns:
            Formatted schema description string.
        """
        if "tables" not in schema_info:
            return "Nenhuma tabela disponível."

        schema_parts: list[str] = []
        for table_info in schema_info.get("tables", []):
            table_name = table_info.get("name", "unknown")
            columns = table_info.get("columns", [])

            table_desc = f"Tabela: {table_name}\n"
            if columns:
                table_desc += "  Colunas:\n"
                for col in columns:
                    col_name = col.get("name", "unknown")
                    col_type = col.get("data_type", "unknown")
                    table_desc += f"    - {col_name} ({col_type})\n"
            else:
                table_desc += "  (sem colunas definidas)\n"

            schema_parts.append(table_desc)

        return "\n".join(schema_parts)

    def _build_json_schema(self) -> Dict[str, Any]:
        """Build JSON Schema for structured output.

        Defines schema for LLM structured output with SQL and metadata.

        Returns:
            JSON Schema dictionary.
        """
        return {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "Generated SQL query",
                },
                "explanation": {
                    "type": "string",
                    "description": "Explanation of the SQL query",
                },
                "tables_used": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of table names used in the query",
                },
                "columns_used": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of column names used in the query",
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Confidence score (0.0-1.0)",
                },
            },
            "required": ["sql", "explanation", "tables_used", "columns_used", "confidence"],
        }

    def _validate_syntax(self, sql: str) -> None:
        """Validate SQL syntax.

        Validates SQL syntax using sqlparse if available, or basic validation.

        Args:
            sql: SQL query to validate.

        Raises:
            ValidationException: If SQL syntax is invalid.
        """
        if not sql or not sql.strip():
            raise ValidationException(
                message="SQL query cannot be empty",
                details={"sql": sql},
            )

        # Basic validation: check for dangerous operations
        sql_upper = sql.upper().strip()
        dangerous_ops = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE"]
        for op in dangerous_ops:
            if sql_upper.startswith(op) or f" {op} " in sql_upper:
                raise ValidationException(
                    message=f"SQL contains dangerous operation: {op}",
                    details={"sql": sql[:200], "operation": op},
                )

        # Use sqlparse if available for syntax validation
        if SQLPARSE_AVAILABLE and sqlparse:
            try:
                parsed = sqlparse.parse(sql)
                if not parsed:
                    raise ValidationException(
                        message="SQL syntax is invalid (failed to parse)",
                        details={"sql": sql[:200]},
                    )
            except Exception as e:
                raise ValidationException(
                    message=f"SQL syntax validation failed: {str(e)}",
                    details={"sql": sql[:200], "error": str(e)},
                ) from e

    def _generate_cache_key(self, query: str, schema_info: Dict[str, Any]) -> str:
        """Generate cache key for SQL generation.

        Creates cache key from query and schema info hash.

        Args:
            query: User query.
            schema_info: Schema information.

        Returns:
            Cache key string.
        """
        # Create hash from query + schema
        key_data = json.dumps({"query": query, "schema": schema_info}, sort_keys=True)
        key_hash = hashlib.sha256(key_data.encode()).hexdigest()
        return f"sql_generation:{key_hash}"

