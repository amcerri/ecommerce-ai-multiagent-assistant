"""
Language services module (language detection and translation).

Overview
  Provides language detection and translation services for the application.
  LanguageDetector will be fully implemented in Batch 27.

Design
  - **Language Detection**: Automatic detection from IP and headers.
  - **Translation**: Translation services (future).
  - **Extensibility**: Easy to extend with new languages.

Integration
  - Consumes: IP address, Accept-Language header, geolocation APIs.
  - Returns: Language codes and translations.
  - Used by: Middleware for automatic language detection.
  - Observability: Logs detection operations.

Usage
  >>> from app.services.language import LanguageDetector
  >>> detector = LanguageDetector()
  >>> language = await detector.detect("192.168.1.1", "pt-BR,en-US;q=0.9")
"""

from app.services.language.detector import LanguageDetector

__all__ = [
    "LanguageDetector",
]

