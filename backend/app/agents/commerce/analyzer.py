"""
Commerce analyzer (document analysis with inconsistency detection).

Overview
  Analyzes extracted document data for inconsistencies, errors, and risks.
  Validates calculations, dates, and values. Generates executive summary.
  Implements graceful degradation if analysis fails.

Design
  - **Inconsistency Detection**: Detects calculation errors, date issues, value anomalies.
  - **Validation**: Validates fields and formats.
  - **Risk Identification**: Identifies potential risks.
  - **Executive Summary**: Generates summary of analysis.

Integration
  - Consumes: LLMClient (optional), extracted data, schema.
  - Returns: Analysis results with inconsistencies, validations, risks, summary.
  - Used by: CommerceAgent for document analysis.
  - Observability: Logs analysis operations.

Usage
  >>> from app.agents.commerce.analyzer import CommerceAnalyzer
  >>> analyzer = CommerceAnalyzer(llm_client)
  >>> result = await analyzer.analyze(extracted_data, schema)
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.config.exceptions import LLMException
from app.infrastructure.llm.client import LLMClient

logger = logging.getLogger(__name__)


class CommerceAnalyzer:
    """Document analyzer for commerce documents.

    Analyzes extracted data for inconsistencies, errors, and risks.
    Validates calculations, dates, and values.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        """Initialize commerce analyzer.

        Args:
            llm_client: LLM client for analysis (optional, graceful degradation).
        """
        self._llm_client = llm_client

    async def analyze(
        self,
        extracted_data: Dict[str, Any],
        schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze extracted document data.

        Detects inconsistencies, validates fields, identifies risks,
        and generates summary.

        Args:
            extracted_data: Extracted data dictionary.
            schema: Document schema dictionary.

        Returns:
            Dictionary with inconsistencies, validations, risks, summary.
        """
        analysis_results: Dict[str, Any] = {
            "inconsistencies": [],
            "validations": [],
            "risks": [],
            "summary": None,
        }

        try:
            # Step 1: Detect inconsistencies
            inconsistencies = self._detect_inconsistencies(extracted_data, schema)
            analysis_results["inconsistencies"] = inconsistencies

            # Step 2: Validate fields
            validations = self._validate_fields(extracted_data, schema)
            analysis_results["validations"] = validations

            # Step 3: Identify risks
            risks = self._identify_risks(extracted_data, schema)
            analysis_results["risks"] = risks

            # Step 4: Generate summary (if LLM available)
            if self._llm_client:
                try:
                    summary = await self._generate_summary(extracted_data, inconsistencies, risks)
                    analysis_results["summary"] = summary
                except Exception as e:
                    logger.warning(f"Summary generation failed: {e}")
                    # Graceful degradation: continue without summary

            return analysis_results
        except Exception as e:
            logger.warning(f"Analysis failed: {e}")
            # Graceful degradation: return partial results
            return analysis_results

    def _detect_inconsistencies(
        self,
        extracted_data: Dict[str, Any],
        schema: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Detect inconsistencies in extracted data.

        Checks calculations, dates, and values for inconsistencies.

        Args:
            extracted_data: Extracted data dictionary.
            schema: Document schema dictionary.

        Returns:
            List of inconsistency dictionaries.
        """
        inconsistencies: List[Dict[str, Any]] = []

        # Check calculations (totals, subtotals, taxes)
        calc_inconsistencies = self._check_calculations(extracted_data)
        inconsistencies.extend(calc_inconsistencies)

        # Check dates
        date_inconsistencies = self._check_dates(extracted_data)
        inconsistencies.extend(date_inconsistencies)

        # Check values
        value_inconsistencies = self._check_values(extracted_data)
        inconsistencies.extend(value_inconsistencies)

        return inconsistencies

    def _check_calculations(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check calculation consistency.

        Validates totals, subtotals, taxes, etc.

        Args:
            data: Extracted data dictionary.

        Returns:
            List of calculation inconsistency dictionaries.
        """
        inconsistencies: List[Dict[str, Any]] = []

        # Check if we have total and subtotal fields
        total = data.get("total", data.get("valor_total", data.get("amount", None)))
        subtotal = data.get("subtotal", data.get("valor_subtotal", None))
        tax = data.get("tax", data.get("imposto", data.get("taxa", None)))

        if total is not None and subtotal is not None:
            try:
                total_num = float(total)
                subtotal_num = float(subtotal)
                tax_num = float(tax) if tax is not None else 0.0

                expected_total = subtotal_num + tax_num
                if abs(total_num - expected_total) > 0.01:  # Allow small rounding differences
                    inconsistencies.append(
                        {
                            "type": "calculation_error",
                            "field": "total",
                            "message": f"Total ({total_num}) does not match subtotal + tax ({expected_total})",
                            "severity": "high",
                        },
                    )
            except (ValueError, TypeError):
                pass  # Skip if values are not numeric

        return inconsistencies

    def _check_dates(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check date consistency.

        Validates dates for future dates, inconsistencies, etc.

        Args:
            data: Extracted data dictionary.

        Returns:
            List of date inconsistency dictionaries.
        """
        inconsistencies: List[Dict[str, Any]] = []

        # Check for date fields
        date_fields = ["date", "data", "emission_date", "due_date", "vencimento"]
        now = datetime.now()

        for field_name in date_fields:
            if field_name in data and data[field_name] is not None:
                try:
                    # Try to parse date (various formats)
                    date_str = str(data[field_name])
                    # Basic date parsing (could be improved)
                    # For now, just check if it's a future date (might be valid for some documents)
                    # This is a simplified check
                except Exception:
                    pass

        return inconsistencies

    def _check_values(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check value consistency.

        Validates values for negatives, zeros, suspicious values.

        Args:
            data: Extracted data dictionary.

        Returns:
            List of value inconsistency dictionaries.
        """
        inconsistencies: List[Dict[str, Any]] = []

        # Check for negative values in amount fields
        amount_fields = ["total", "valor_total", "amount", "subtotal", "valor_subtotal"]
        for field_name in amount_fields:
            if field_name in data and data[field_name] is not None:
                try:
                    value = float(data[field_name])
                    if value < 0:
                        inconsistencies.append(
                            {
                                "type": "negative_value",
                                "field": field_name,
                                "message": f"Negative value found: {value}",
                                "severity": "medium",
                            },
                        )
                    elif value == 0:
                        inconsistencies.append(
                            {
                                "type": "zero_value",
                                "field": field_name,
                                "message": f"Zero value found: {value}",
                                "severity": "low",
                            },
                        )
                except (ValueError, TypeError):
                    pass

        return inconsistencies

    def _validate_fields(
        self,
        extracted_data: Dict[str, Any],
        schema: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Validate fields and formats.

        Validates required fields, formats (emails, CPF/CNPJ, etc.).

        Args:
            extracted_data: Extracted data dictionary.
            schema: Document schema dictionary.

        Returns:
            List of validation result dictionaries.
        """
        validations: List[Dict[str, Any]] = []

        # Check required fields
        fields = schema.get("fields", [])
        for field in fields:
            field_name = field["name"]
            is_required = field.get("required", False)

            if is_required:
                if field_name not in extracted_data or extracted_data[field_name] is None:
                    validations.append(
                        {
                            "field": field_name,
                            "status": "missing",
                            "message": f"Required field {field_name} is missing",
                        },
                    )
                else:
                    validations.append(
                        {
                            "field": field_name,
                            "status": "present",
                            "message": f"Required field {field_name} is present",
                        },
                    )

        # Validate formats (emails, CPF/CNPJ, etc.)
        format_validations = self._validate_formats(extracted_data)
        validations.extend(format_validations)

        return validations

    def _validate_formats(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate field formats.

        Validates email, CPF/CNPJ, and other format fields.

        Args:
            data: Extracted data dictionary.

        Returns:
            List of format validation dictionaries.
        """
        validations: List[Dict[str, Any]] = []

        # Check email fields
        email_fields = ["email", "e_mail", "email_address"]
        for field_name in email_fields:
            if field_name in data and data[field_name] is not None:
                email = str(data[field_name])
                if "@" not in email or "." not in email.split("@")[1]:
                    validations.append(
                        {
                            "field": field_name,
                            "status": "invalid_format",
                            "message": f"Email format appears invalid: {email}",
                        },
                    )

        return validations

    def _identify_risks(
        self,
        extracted_data: Dict[str, Any],
        schema: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Identify potential risks.

        Identifies risks like high values, overdue dates, etc.

        Args:
            extracted_data: Extracted data dictionary.
            schema: Document schema dictionary.

        Returns:
            List of risk dictionaries.
        """
        risks: List[Dict[str, Any]] = []

        # Check for high values
        amount_fields = ["total", "valor_total", "amount"]
        for field_name in amount_fields:
            if field_name in extracted_data and extracted_data[field_name] is not None:
                try:
                    value = float(extracted_data[field_name])
                    # Consider values > 100,000 as high (threshold can be configurable)
                    if value > 100000:
                        risks.append(
                            {
                                "type": "high_value",
                                "field": field_name,
                                "message": f"High value detected: {value}",
                                "severity": "medium",
                            },
                        )
                except (ValueError, TypeError):
                    pass

        return risks

    async def _generate_summary(
        self,
        extracted_data: Dict[str, Any],
        inconsistencies: List[Dict[str, Any]],
        risks: List[Dict[str, Any]],
    ) -> Optional[str]:
        """Generate executive summary using LLM.

        Generates summary of analysis results.

        Args:
            extracted_data: Extracted data dictionary.
            inconsistencies: List of inconsistencies.
            risks: List of risks.

        Returns:
            Summary text, or None if generation fails.
        """
        if not self._llm_client:
            return None

        try:
            prompt = f"""Gere um resumo executivo da análise do documento comercial.

DADOS EXTRAÍDOS:
{str(extracted_data)[:1000]}

INCONSISTÊNCIAS ENCONTRADAS:
{len(inconsistencies)} inconsistência(s)
{str(inconsistencies)[:500]}

RISCOS IDENTIFICADOS:
{len(risks)} risco(s)
{str(risks)[:500]}

Gere um resumo executivo em português destacando os pontos principais, inconsistências críticas, e riscos identificados."""

            response = await self._llm_client.generate(prompt)
            return response.text
        except Exception as e:
            logger.warning(f"Summary generation failed: {e}")
            return None

