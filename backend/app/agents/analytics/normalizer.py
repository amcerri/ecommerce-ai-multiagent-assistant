"""
Analytics normalizer (intelligent result formatting and analysis).

Overview
  Normalizes and formats SQL query results with intelligent formatting,
  semantic analysis, and visualization suggestions. Provides graceful
  degradation if LLM analysis is unavailable.

Design
  - **Intelligent Formatting**: Formats numbers, dates, booleans by language.
  - **Semantic Analysis**: Optional LLM-based analysis for insights.
  - **Visualization Suggestions**: Suggests best display format.
  - **Statistical Summary**: Calculates basic statistics when applicable.

Integration
  - Consumes: LLMClient (optional), date utilities, constants.
  - Returns: Formatted results with summary, insights, and suggestions.
  - Used by: AnalyticsAgent for result normalization.
  - Observability: Logs normalization operations.

Usage
  >>> from app.agents.analytics.normalizer import AnalyticsNormalizer
  >>> normalizer = AnalyticsNormalizer(llm_client)
  >>> result = await normalizer.normalize(rows, sql, "pt-BR")
"""

import logging
from typing import Any, Dict, List, Optional

from app.infrastructure.llm.client import LLMClient
from app.utils.date import format_date, format_date_relative

logger = logging.getLogger(__name__)

# Try to import pandas (optional, for analysis)
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None  # type: ignore


class AnalyticsNormalizer:
    """Result normalizer for analytics queries.

    Normalizes and formats SQL query results with intelligent formatting,
    semantic analysis, and visualization suggestions.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        """Initialize analytics normalizer.

        Args:
            llm_client: LLM client for semantic analysis (optional).
        """
        self._llm_client = llm_client

    async def normalize(
        self,
        rows: List[Dict[str, Any]],
        sql: str,
        language: str,
    ) -> Dict[str, Any]:
        """Normalize and format query results.

        Formats results, performs semantic analysis (if LLM available),
        calculates statistics, and suggests visualization format.

        Args:
            rows: Query results (list of dictionaries).
            sql: SQL query executed.
            language: Language for formatting.

        Returns:
            Dictionary with formatted_data, summary, insights, display_suggestions.
        """
        if not rows:
            return {
                "formatted_data": [],
                "summary": {"row_count": 0},
                "insights": None,
                "display_suggestions": {"type": "table", "reason": "Empty result set"},
            }

        # Step 1: Basic formatting
        formatted_data = self._format_rows(rows, language)

        # Step 2: Statistical summary
        summary = self._calculate_summary(rows)

        # Step 3: Semantic analysis (if LLM available)
        insights = None
        if self._llm_client:
            try:
                insights = await self._analyze_semantically(rows, sql, language)
            except Exception as e:
                logger.warning(f"Semantic analysis failed: {e}")
                # Graceful degradation: continue without insights

        # Step 4: Visualization suggestions
        display_suggestions = self._suggest_display(rows, sql)

        return {
            "formatted_data": formatted_data,
            "summary": summary,
            "insights": insights,
            "display_suggestions": display_suggestions,
        }

    def _format_rows(
        self,
        rows: List[Dict[str, Any]],
        language: str,
    ) -> List[Dict[str, Any]]:
        """Format rows with language-specific formatting.

        Formats numbers, dates, and booleans according to language.

        Args:
            rows: Query results.
            language: Language for formatting.

        Returns:
            List of formatted row dictionaries.
        """
        formatted: List[Dict[str, Any]] = []

        for row in rows:
            formatted_row: Dict[str, Any] = {}
            for key, value in row.items():
                formatted_row[key] = self._format_value(value, language)
            formatted.append(formatted_row)

        return formatted

    def _format_value(self, value: Any, language: str) -> Any:
        """Format single value according to type and language.

        Formats numbers, dates, and booleans with language-specific formatting.

        Args:
            value: Value to format.
            language: Language for formatting.

        Returns:
            Formatted value.
        """
        if value is None:
            return None

        # Format booleans
        if isinstance(value, bool):
            if language.startswith("pt"):
                return "Sim" if value else "Não"
            return "Yes" if value else "No"

        # Format dates
        if isinstance(value, (str, int, float)):
            # Try to parse as date
            try:
                from datetime import datetime

                if isinstance(value, str):
                    # Try common date formats
                    for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"]:
                        try:
                            dt = datetime.strptime(value, fmt)
                            return format_date(dt, language)
                        except ValueError:
                            continue
            except Exception:
                pass

        # Format numbers
        if isinstance(value, (int, float)):
            if language.startswith("pt"):
                # Portuguese formatting: 1.234,56
                if isinstance(value, float):
                    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                return f"{value:,}".replace(",", ".")
            else:
                # English formatting: 1,234.56
                if isinstance(value, float):
                    return f"{value:,.2f}"
                return f"{value:,}"

        return value

    def _calculate_summary(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistical summary.

        Calculates basic statistics (count, sum, avg, min, max) when applicable.

        Args:
            rows: Query results.

        Returns:
            Summary dictionary with statistics.
        """
        summary: Dict[str, Any] = {
            "row_count": len(rows),
        }

        if not rows:
            return summary

        # Use pandas if available for better analysis
        if PANDAS_AVAILABLE and pd:
            try:
                df = pd.DataFrame(rows)
                numeric_cols = df.select_dtypes(include=["number"]).columns

                if len(numeric_cols) > 0:
                    summary["numeric_columns"] = {}
                    for col in numeric_cols:
                        summary["numeric_columns"][col] = {
                            "sum": float(df[col].sum()),
                            "avg": float(df[col].mean()),
                            "min": float(df[col].min()),
                            "max": float(df[col].max()),
                        }
            except Exception:
                # Graceful degradation: continue without pandas analysis
                pass

        return summary

    async def _analyze_semantically(
        self,
        rows: List[Dict[str, Any]],
        sql: str,
        language: str,
    ) -> Optional[Dict[str, Any]]:
        """Perform semantic analysis using LLM.

        Analyzes results to detect patterns and generate insights.

        Args:
            rows: Query results.
            sql: SQL query executed.
            language: Language for insights.

        Returns:
            Dictionary with insights, or None if analysis fails.
        """
        if not self._llm_client:
            return None

        try:
            # Prepare data summary for LLM
            row_count = len(rows)
            sample_rows = rows[:5]  # Sample for analysis
            columns = list(rows[0].keys()) if rows else []

            prompt = f"""Analise os resultados da seguinte query SQL e forneça insights:

Query SQL: {sql[:200]}

Resultados:
- Total de linhas: {row_count}
- Colunas: {', '.join(columns)}
- Amostra (primeiras 5 linhas): {sample_rows}

Forneça:
1. Insights descritivos (o que os dados mostram)
2. Insights interpretativos (o que isso significa)
3. Insights acionáveis (o que fazer com essa informação)

Responda em {language}."""

            response = await self._llm_client.generate(prompt)
            insights_text = response.text

            return {
                "descriptive": insights_text,
                "interpretive": None,  # Could be extracted from LLM response
                "actionable": None,  # Could be extracted from LLM response
            }
        except Exception as e:
            logger.warning(f"Semantic analysis failed: {e}")
            return None

    def _suggest_display(
        self,
        rows: List[Dict[str, Any]],
        sql: str,
    ) -> Dict[str, Any]:
        """Suggest visualization format.

        Suggests best display format based on data structure and query type.

        Args:
            rows: Query results.
            sql: SQL query executed.

        Returns:
            Dictionary with display suggestion (type, reason).
        """
        if not rows:
            return {"type": "table", "reason": "Empty result set"}

        sql_upper = sql.upper()

        # Check for aggregation queries
        has_aggregation = any(
            agg in sql_upper
            for agg in ["COUNT", "SUM", "AVG", "MAX", "MIN", "GROUP BY"]
        )

        # Check for time series (date columns)
        has_date = any(
            "date" in key.lower() or "time" in key.lower()
            for key in rows[0].keys()
            if rows
        )

        # Suggest based on query type
        if has_aggregation and len(rows) <= 20:
            if has_date:
                return {"type": "line_chart", "reason": "Time series aggregation"}
            return {"type": "bar_chart", "reason": "Aggregation results"}

        if len(rows) > 100:
            return {"type": "table", "reason": "Large result set"}

        return {"type": "table", "reason": "Standard tabular data"}

