import time
import io
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.colors import white, black, Color
from reportlab.lib.units import inch, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .reader import PDFReader
from ..utils.exceptions import *
from ..utils.error_handlers import (
    FileSystemValidator,
    PDFValidator,
    handle_pdf_processing_error,
)
from ..utils.result_types import KeywordInjectionResult


class InvisibleMethod(Enum):
    WHITE_TEXT = "white_text"
    TINY_FONT = "tiny_font"
    MARGIN_PLACEMENT = "margin"
    BACKGROUND_LAYER = "background"
    TRANSPARENT_TEXT = "transparent"


@dataclass
class InjectionStrategy:
    methods: List[InvisibleMethod]
    keyword_density: float = 0.1
    position_randomization: bool = True
    font_size_range: Tuple[float, float] = (0.1, 0.5)
    color_opacity: float = 0.1
    margin_width: float = 10


class PDFWriter:
    def __init__(
        self,
        page_size: Tuple[float, float] = letter,
        default_font: str = "Helvetica",
        debug_mode: bool = False,
    ):
        self.page_size = page_size
        self.default_font = default_font
        self.debug_mode = debug_mode
        self.width, self.height = page_size

    def create_optimized_resume(
        self,
        original_content: str,
        keywords: List[str],
        output_path: Union[str, Path],
        strategy: Optional[InjectionStrategy] = None,
    ) -> KeywordInjectionResult:
        start_time = time.time()
        output_path = Path(output_path)

        if strategy is None:
            strategy = InjectionStrategy(
                methods=[InvisibleMethod.WHITE_TEXT, InvisibleMethod.MARGIN_PLACEMENT]
            )

        try:
            c = canvas.Canvas(str(output_path), pagesize=self.page_size)

            self._add_original_content(c, original_content)

            injected_keywords = []

            for method in strategy.methods:
                method_keywords = self._inject_keywords_by_method(
                    c, keywords, method, strategy
                )
                injected_keywords.extend(method_keywords)

            c.save()
            processing_time = time.time() - start_time

            verification_result = self._verify_keyword_injection(output_path, keywords)

            return KeywordInjectionResult.success_result(
                output_path=str(output_path),
                keywords_injected=list(set(injected_keywords)),
                injection_methods=[m.value for m in strategy.methods],
                original_text_length=len(original_content),
                final_text_length=verification_result.get("final_length", 0),
                processing_time=processing_time,
            )
        except Exception as e:
            specific_error = handle_pdf_processing_error(
                e, "keyword injection", str(output_path)
            )
            return KeywordInjectionResult.error_result(specific_error)

    def enhance_existing_pdf(
        self,
        input_path: Union[str, Path],
        keywords: List[str],
        output_path: Union[str, Path],
        strategy: Optional[InjectionStrategy] = None,
    ) -> KeywordInjectionResult:
        start_time = time.time()

        try:
            PDFValidator.validate_pdf_file(input_path)
            FileSystemValidator.validate_output_path(output_path)

            input_pdf = Path(input_path)
            output_pdf = Path(output_path)

            if strategy is None:
                strategy = InjectionStrategy(
                    methods=[InvisibleMethod.WHITE_TEXT, InvisibleMethod.TINY_FONT]
                )

            with open(input_pdf, "rb") as file:
                original_pdf = PdfReader(file)

                reader = PDFReader()
                extraction_result = reader.extract_text(input_pdf)
                original_text_length = (
                    len(extraction_result.text or "") if extraction_result else 0
                )

                overlay_pdf_bytes, injected_keywords = self._create_keyword_overlay(
                    original_pdf, keywords, strategy
                )

                final_pdf = self._merge_pdfs(original_pdf, overlay_pdf_bytes)

                with open(output_pdf, "wb") as output_file:
                    final_pdf.write(output_file)

                processing_time = time.time() - start_time

                verification_result = self._verify_keyword_injection(
                    output_pdf, keywords
                )

                return KeywordInjectionResult.success_result(
                    output_path=str(output_path),
                    injection_methods=[m.value for m in strategy.methods],
                    final_text_length=verification_result.get(
                        "final_length", original_text_length
                    ),
                    processing_time=processing_time,
                    keywords_injected=injected_keywords,
                    original_text_length=original_text_length,
                )
        except (PDFError, FileSystemError) as e:
            return KeywordInjectionResult.error_result(e)

        except PdfReadError as e:
            specific_error = handle_pdf_processing_error(
                e, "keyword_injection", str(input_path)
            )
            return KeywordInjectionResult.error_result(specific_error)

        except Exception as e:
            specific_error = handle_pdf_processing_error(
                e, "keyword_injection", str(input_path)
            )
            return KeywordInjectionResult.error_result(specific_error)

    def _create_keyword_overlay(
        self, original_pdf: PdfReader, keywords: List[str], strategy: InjectionStrategy
    ) -> Tuple[bytes, List[str]]:
        buffer = io.BytesIO()

        first_page = original_pdf.pages[0]
        page_box = first_page.mediabox
        self.width = float(page_box.width)
        self.height = float(page_box.height)

        c = canvas.Canvas(buffer, pagesize=(self.width, self.height))

        injected_keywords = []
        for page_num in range(len(original_pdf.pages)):
            if page_num > 0:
                c.showPage()
            for method in strategy.methods:
                method_keywords = self._inject_keywords_by_method(
                    c, keywords, method, strategy
                )
                injected_keywords.extend(method_keywords)

        c.save()
        buffer.seek(0)
        return buffer.getvalue(), list(set(injected_keywords))

    def _merge_pdfs(
        self, original_pdf: PdfReader, overlay_pdf_bytes: bytes
    ) -> PdfWriter:
        overlay_buffer = io.BytesIO(overlay_pdf_bytes)
        overlay_pdf = PdfReader(overlay_buffer)

        output_pdf = PdfWriter()

        for page_num in range(len(original_pdf.pages)):
            original_page = original_pdf.pages[page_num]

            overlay_page_num = min(page_num, len(overlay_pdf.pages) - 1)
            overlay_page = overlay_pdf.pages[overlay_page_num]

            original_page.merge_page(overlay_page)

            output_pdf.add_page(original_page)

        if original_pdf.metadata:
            output_pdf.add_metadata(original_pdf.metadata)

        return output_pdf

    def _add_original_content(self, canvas_obj: canvas.Canvas, content: str):
        lines = content.split("\n")
        y_position = self.height - 100

        for line in lines:
            if y_position < 100:
                canvas_obj.showPage()
                y_position = self.height - 100

            canvas_obj.setFont(self.default_font, 12)
            canvas_obj.setFillColor(black)
            canvas_obj.drawString(100, y_position, line.strip())
            y_position -= 20

    def _inject_keywords_by_method(
        self,
        canvas_obj: canvas.Canvas,
        keywords: List[str],
        method: InvisibleMethod,
        strategy: InjectionStrategy,
    ) -> List[str]:
        if method == InvisibleMethod.WHITE_TEXT:
            return self._inject_white_text(
                canvas_obj,
                keywords,
                strategy,
            )
        elif method == InvisibleMethod.TINY_FONT:
            return self._inject_tiny_font(canvas_obj, keywords, strategy)
        elif method == InvisibleMethod.MARGIN_PLACEMENT:
            return self._inject_margin_keywords(canvas_obj, keywords, strategy)
        elif method == InvisibleMethod.BACKGROUND_LAYER:
            return self._inject_background_layer(canvas_obj, keywords, strategy)
        elif method == InvisibleMethod.TRANSPARENT_TEXT:
            return self._inject_transparent_text(canvas_obj, keywords, strategy)

        return []

    def _inject_white_text(
        self,
        canvas_obj: canvas.Canvas,
        keywords: List[str],
        strategy: InjectionStrategy,
    ) -> List[str]:
        if self.debug_mode:
            canvas_obj.setFillColor(Color(0.9, 0.9, 0.9))
        else:
            canvas_obj.setFillColor(white)

        canvas_obj.setFont(self.default_font, 8)

        x, y = self.width * 0.2, self.height * 0.95
        keyword_string = " ".join(keywords)
        canvas_obj.drawString(x, y, keyword_string)

        return keywords

    def _inject_tiny_font(
        self,
        canvas_obj: canvas.Canvas,
        keywords: List[str],
        strategy: InjectionStrategy,
    ) -> List[str]:
        min_size, max_size = strategy.font_size_range
        font_size = min_size if not self.debug_mode else 2.0

        canvas_obj.setFont(self.default_font, font_size)
        # Use white color for true invisibility
        if self.debug_mode:
            canvas_obj.setFillColor(Color(0.8, 0.8, 0.8))  # Light gray for debugging
        else:
            canvas_obj.setFillColor(white)  # Invisible white text

        import random

        injected = []
        for keyword in keywords[:10]:
            x = random.randint(100, int(self.width - 200))
            y = random.randint(100, int(self.height - 200))

            canvas_obj.drawString(x, y, keyword)
            injected.append(keyword)

        return injected

    def _inject_margin_keywords(
        self,
        canvas_obj: canvas.Canvas,
        keywords: List[str],
        strategy: InjectionStrategy,
    ) -> List[str]:
        margin = strategy.margin_width * mm

        canvas_obj.setFont(self.default_font, 6)
        if self.debug_mode:
            canvas_obj.setFillColor(Color(0.9, 0.9, 0.9))
        else:
            canvas_obj.setFillColor(white)

        y_position = self.height - 100

        injected = []

        for keyword in keywords[:5]:
            canvas_obj.drawString(margin, y_position, keyword)
            y_position -= 30
            injected.append(keyword)

        y_position = self.height - 150
        for keyword in keywords[5:10]:
            if keyword not in injected:
                canvas_obj.drawString(self.width - 100, y_position, keyword)
                y_position -= 30
                injected.append(keyword)

        return injected

    def _inject_background_layer(
        self,
        canvas_obj: canvas.Canvas,
        keywords: List[str],
        strategy: InjectionStrategy,
    ) -> List[str]:
        canvas_obj.saveState()

        canvas_obj.setFont(self.default_font, 4)
        canvas_obj.setFillColor(Color(1, 1, 1, alpha=0.01))

        keyword_text = " ".join(keywords)

        positions = [
            (50, 50),
            (200, 100),
            (350, 150),
            (100, 300),
            (400, 400),
        ]

        injected = []
        for x, y in positions:
            canvas_obj.drawString(x, y, keyword_text)
            injected.extend(keywords)

        canvas_obj.restoreState()

        return list(set(injected))

    def _inject_transparent_text(
        self,
        canvas_obj: canvas.Canvas,
        keywords: List[str],
        strategy: InjectionStrategy,
    ) -> List[str]:
        opacity = strategy.color_opacity if not self.debug_mode else 0.3

        canvas_obj.setFont(self.default_font, 10)
        canvas_obj.setFillColor(Color(0, 0, 0, alpha=opacity))

        injected = []

        y_position = 0
        for i, keyword in enumerate(keywords[:10]):
            canvas_obj.drawString(150 + (i * 100), self.height - y_position, keyword)
            y_position += 50
            injected.append(keyword)

        return injected

    def _verify_keyword_injection(
        self, pdf_path: Path, expected_keywords: List[str]
    ) -> Dict:
        try:
            reader = PDFReader()
            result = reader.extract_text(pdf_path)

            if not result.success:
                return {"success": False, "error": result.error_message}

            detected_keywords = []
            for keyword in expected_keywords:
                text = result.text or ""
                if keyword.lower() in text.lower():
                    detected_keywords.append(keyword)

            return {
                "success": True,
                "final_length": len(result.text or ""),
                "detected_keywords": detected_keywords,
                "detection_rate": len(detected_keywords) / len(expected_keywords)
                if expected_keywords
                else 0,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


def create_ats_optimized_pdf(
    original_text: str,
    keywords: List[str],
    output_path: Union[str, Path],
    methods: Optional[List[InvisibleMethod]] = None,
) -> KeywordInjectionResult:
    if methods is None:
        methods = [
            InvisibleMethod.WHITE_TEXT,
            InvisibleMethod.TINY_FONT,
            InvisibleMethod.TRANSPARENT_TEXT,
        ]
    else:
        try:
            methods = [InvisibleMethod(m) for m in methods]
        except ValueError as e:
            raise ValueError(f"Invalid injection method: {e}")

    strategy = InjectionStrategy(methods=methods)
    writer = PDFWriter()

    return writer.create_optimized_resume(
        original_content=original_text,
        keywords=keywords,
        output_path=output_path,
        strategy=strategy,
    )


def enhance_pdf_with_keywords(
    input_pdf: Union[str, Path], keywords: List[str], output_path: Union[str, Path]
) -> KeywordInjectionResult:
    writer = PDFWriter()
    return writer.enhance_existing_pdf(input_pdf, keywords, output_path)
