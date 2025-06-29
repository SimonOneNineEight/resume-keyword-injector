from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from .exceptions import KeywordGeneratorError


@dataclass
class ProcessingResult:
    success: bool
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    error_detail: Optional[Dict[str, Any]] = None
    exception: Optional[KeywordGeneratorError] = None

    @classmethod
    def success_result(cls, **kwargs):
        return cls(success=True, **kwargs)

    @classmethod
    def error_result(cls, exception: KeywordGeneratorError, **kwargs):
        return cls(
            success=False,
            error_message=exception.message,
            error_code=exception.error_code,
            error_detail=exception.details,
            exception=exception,
            **kwargs,
        )


@dataclass
class PDFTextResult(ProcessingResult):
    text: Optional[str] = None
    page_count: Optional[int] = None
    page_texts: Optional[List[str]] = None
    metadata: Optional[Dict[str, str]] = None
    extraction_time: Optional[float] = None

    @classmethod
    def success_result(
        cls,
        **kwargs,
    ):
        return cls(
            success=True,
            **kwargs,
        )

    @classmethod
    def error_result(
        cls, exception: KeywordGeneratorError, extraction_time: float = 0.0, **kwargs
    ):
        return cls(
            success=False,
            error_message=exception.message,
            error_code=exception.error_code,
            error_detail=exception.details,
            exception=exception,
            extraction_time=extraction_time,
            text="",
            page_count=0,
            page_texts=[],
            metadata={},
            **kwargs,
        )


@dataclass
class KeywordInjectionResult(ProcessingResult):
    output_path: Optional[str] = None
    keywords_injected: Optional[List[str]] = None
    injection_methods: Optional[List[str]] = None
    original_text_length: Optional[int] = None
    final_text_length: Optional[int] = None
    processing_time: Optional[float] = None
