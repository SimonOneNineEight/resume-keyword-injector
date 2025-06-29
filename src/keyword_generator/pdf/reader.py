import time
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from ..utils.exceptions import *
from ..utils.error_handlers import (
    FileSystemValidator,
    PDFValidator,
    handle_pdf_processing_error,
)
from ..utils.result_types import PDFTextResult


# @dataclass
# class PDFTextResult:
#     text: str
#     pages: int
#     extraction_time: float
#     metadata: Dict[str, str]
#     page_texts: List[str]
#     success: bool
#     error_message: Optional[str] = None


class PDFReader:
    def __init__(self, enable_page_splitting: bool = True):
        self.enable_page_splitting = enable_page_splitting

    def extract_text(self, pdf_path: Union[str, Path]) -> PDFTextResult:
        pdf_path = Path(pdf_path)
        start_time = time.time()

        try:
            PDFValidator.validate_pdf_file(pdf_path)

            with open(pdf_path, "rb") as file:
                reader = PdfReader(file)

                metadata = self._extract_metadata(reader)

                full_text = ""
                page_texts = []

                for page_num, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            full_text += page_text + "\n"
                            if self.enable_page_splitting:
                                page_texts.append(page_text)
                    except Exception as e:
                        page_texts.append(
                            f"[Error extracting page {page_num + 1}: {str(e)}"
                        )

                extraction_time = time.time() - start_time
                return PDFTextResult.success_result(
                    text=full_text.strip(),
                    page_count=len(reader.pages),
                    extraction_time=extraction_time,
                    metadata=metadata,
                    page_texts=page_texts,
                )

        except (PDFError, FileSystemError) as e:
            return PDFTextResult.error_result(e)

        except Exception as e:
            specific_error = handle_pdf_processing_error(
                e, "text_extraction", str(pdf_path)
            )
            return PDFTextResult.error_result(specific_error)

    def _extract_metadata(self, reader: PdfReader) -> Dict[str, str]:
        metadata = {}

        try:
            if reader.metadata:
                fields = {
                    "/Title": "title",
                    "/Author": "author",
                    "/Subject": "subject",
                    "/Creator": "creator",
                    "/Producer": "producer",
                    "/CreationDate": "creation_date",
                    "/ModDate": "modification_date",
                }

                for pdf_key, result_key in fields.items():
                    if pdf_key in reader.metadata:
                        metadata[result_key] = str(reader.metadata[pdf_key])

            metadata["pages"] = str(len(reader.pages))
            metadata["encrypted"] = str(reader.is_encrypted)

        except Exception as e:
            metadata["metadata_error"] = str(e)

        return metadata

    def quick_extract(self, pdf_path: Union[str, Path]) -> str:
        result = self.extract_text(pdf_path)
        return result.text or "" if result.success else ""

    def extract_first_page(self, pdf_path: Union[str, Path]) -> PDFTextResult:
        pdf_path = Path(pdf_path)
        start_time = time.time()

        try:
            with open(pdf_path, "rb") as file:
                reader = PdfReader(file)

                if len(reader.pages) == 0:
                    no_pages_error = PDFValidationError(
                        "PDF has no pages", error_code="EMPTY_PDF"
                    )
                    return PDFTextResult.error_result(
                        no_pages_error, extraction_time=time.time() - start_time
                    )

                first_page_text = reader.pages[0].extract_text()
                metadata = self._extract_metadata(reader)

                return PDFTextResult.success_result(
                    text=first_page_text,
                    page_count=len(reader.pages),
                    extraction_time=time.time() - start_time,
                    metadata=metadata,
                    page_texts=[first_page_text],
                )

        except Exception as e:
            specific_error = handle_pdf_processing_error(
                e, "first_page_extraction", str(pdf_path)
            )
            return PDFTextResult.error_result(
                specific_error, extraction_time=time.time() - start_time
            )

    def get_text_stats(
        self, pdf_path: Union[str, Path]
    ) -> Dict[str, Union[int, float, str, None]]:
        result = self.extract_text(pdf_path)

        if not result.success:
            return {"error": result.error_message}

        text = result.text or ""
        words = text.split()

        return {
            "character_count": len(text),
            "word_count": len(words),
            "line_count": text.count("\n") + 1,
            "page_count": result.page_count,
            "extraction_time": result.extraction_time,
            "avg_words_per_page": len(words)
            / (result.page_count if result.page_count and result.page_count > 0 else 0),
        }


def extract_pdf_text(pdf_path: Union[str, Path]) -> str:
    reader = PDFReader()
    return reader.quick_extract(pdf_path)


def analyze_pdf(pdf_path: Union[str, Path]) -> PDFTextResult:
    reader = PDFReader(enable_page_splitting=True)
    return reader.extract_text(pdf_path)
