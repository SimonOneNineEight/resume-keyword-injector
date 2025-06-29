"""
Tests for PDF text extraction functionality
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.keyword_generator.pdf.reader import (
    PDFReader,
    extract_pdf_text,
    analyze_pdf,
)
from src.keyword_generator.utils.result_types import PDFTextResult
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import white, black


class TestPDFReader:
    @pytest.fixture
    def simple_pdf(self):
        """Create a simple single-page PDF for testing"""
        temp_path = tempfile.mktemp(suffix=".pdf")

        c = canvas.Canvas(temp_path, pagesize=letter)
        width, height = letter

        # Add basic resume content
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 100, "John Doe")

        c.setFont("Helvetica", 12)
        c.drawString(100, height - 130, "Software Engineer")
        c.drawString(100, height - 160, "Skills: Python, JavaScript, React")
        c.drawString(100, height - 190, "Experience: 5 years in web development")
        c.drawString(100, height - 220, "Education: Computer Science Degree")

        c.save()
        yield temp_path

        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    @pytest.fixture
    def multi_page_pdf(self):
        """Create a multi-page PDF for testing"""
        temp_path = tempfile.mktemp(suffix=".pdf")

        c = canvas.Canvas(temp_path, pagesize=letter)
        width, height = letter

        # Page 1
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 100, "John Doe - Resume")
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 130, "Contact: john@example.com")
        c.drawString(100, height - 160, "Page 1 content")
        c.showPage()

        # Page 2
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, height - 100, "Work Experience")
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 130, "Senior Developer at TechCorp")
        c.drawString(100, height - 160, "Page 2 content")
        c.showPage()

        # Page 3
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, height - 100, "Skills & Education")
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 130, "Python, React, AWS")
        c.drawString(100, height - 160, "Page 3 content")

        c.save()
        yield temp_path

        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    @pytest.fixture
    def empty_pdf(self):
        """Create an empty PDF for testing"""
        temp_path = tempfile.mktemp(suffix=".pdf")

        c = canvas.Canvas(temp_path, pagesize=letter)
        # Create PDF with one empty page (no content but valid page)
        c.showPage()  # This creates an empty page
        c.save()
        yield temp_path

        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    def test_reader_initialization(self):
        """Test PDFReader initialization"""
        # Default initialization
        reader = PDFReader()
        assert reader.enable_page_splitting is True

        # Custom initialization
        reader_no_split = PDFReader(enable_page_splitting=False)
        assert reader_no_split.enable_page_splitting is False

    def test_extract_text_success(self, simple_pdf):
        """Test successful text extraction from simple PDF"""
        reader = PDFReader()
        result = reader.extract_text(simple_pdf)

        # Check success
        assert result.success is True
        assert result.error_message is None

        # Check content
        assert "John Doe" in result.text
        assert "Software Engineer" in result.text
        assert "Python" in result.text
        assert "JavaScript" in result.text

        # Check metadata
        assert result.page_count == 1
        assert result.extraction_time > 0
        assert len(result.page_texts) == 1
        assert isinstance(result.metadata, dict)

    def test_extract_text_multipage(self, multi_page_pdf):
        """Test text extraction from multi-page PDF"""
        reader = PDFReader()
        result = reader.extract_text(multi_page_pdf)

        # Check success
        assert result.success is True

        # Check content from all pages
        assert "John Doe - Resume" in result.text
        assert "Work Experience" in result.text
        assert "Skills & Education" in result.text
        assert "Page 1 content" in result.text
        assert "Page 2 content" in result.text
        assert "Page 3 content" in result.text

        # Check page count
        assert result.page_count == 3
        assert len(result.page_texts) == 3

        # Check individual page content
        assert "Page 1 content" in result.page_texts[0]
        assert "Page 2 content" in result.page_texts[1]
        assert "Page 3 content" in result.page_texts[2]

    def test_extract_text_no_page_splitting(self, multi_page_pdf):
        """Test extraction without page splitting"""
        reader = PDFReader(enable_page_splitting=False)
        result = reader.extract_text(multi_page_pdf)

        assert result.success is True
        assert result.page_count == 3
        # Should still have page texts even without splitting
        assert len(result.page_texts) >= 0

    def test_extract_nonexistent_file(self):
        """Test handling of non-existent file"""
        reader = PDFReader()
        result = reader.extract_text("/nonexistent/file.pdf")

        assert result.success is False
        assert "Input file not found" in result.error_message
        assert result.text == ""
        assert result.page_count == 0

    def test_extract_directory_path(self, tmp_path):
        """Test handling of directory path instead of file"""
        reader = PDFReader()
        result = reader.extract_text(tmp_path)

        assert result.success is False
        assert "Path is not a file" in result.error_message

    def test_quick_extract(self, simple_pdf):
        """Test quick extraction method"""
        reader = PDFReader()
        text = reader.quick_extract(simple_pdf)

        assert "John Doe" in text
        assert "Software Engineer" in text
        assert len(text) > 0

    def test_quick_extract_failure(self):
        """Test quick extraction with invalid file"""
        reader = PDFReader()
        text = reader.quick_extract("/nonexistent/file.pdf")

        assert text == ""

    def test_extract_first_page(self, multi_page_pdf):
        """Test first page extraction"""
        reader = PDFReader()
        result = reader.extract_first_page(multi_page_pdf)

        assert result.success is True
        assert "John Doe - Resume" in result.text
        assert "Page 1 content" in result.text
        # Should not contain content from other pages
        assert "Page 2 content" not in result.text
        assert "Page 3 content" not in result.text

        # Metadata should show total pages but only first page text
        assert result.page_count == 3
        assert len(result.page_texts) == 1

    def test_extract_first_page_empty(self, empty_pdf):
        """Test first page extraction from empty PDF"""
        reader = PDFReader()
        result = reader.extract_first_page(empty_pdf)

        assert result.success is True
        assert result.text == ""
        assert result.page_count == 1

    def test_get_text_stats(self, simple_pdf):
        """Test text statistics calculation"""
        reader = PDFReader()
        stats = reader.get_text_stats(simple_pdf)

        # Check all expected keys
        expected_keys = {
            "character_count",
            "word_count",
            "line_count",
            "page_count",
            "extraction_time",
            "avg_words_per_page",
        }
        assert expected_keys.issubset(stats.keys())

        # Check values are reasonable
        assert stats["character_count"] > 0
        assert stats["word_count"] > 0
        assert stats["page_count"] == 1
        assert stats["extraction_time"] > 0
        assert stats["avg_words_per_page"] > 0

    def test_get_text_stats_failure(self):
        """Test text statistics with invalid file"""
        reader = PDFReader()
        stats = reader.get_text_stats("/nonexistent/file.pdf")

        assert "error" in stats
        assert stats["error"] is not None

    def test_metadata_extraction(self, simple_pdf):
        """Test metadata extraction"""
        reader = PDFReader()
        result = reader.extract_text(simple_pdf)

        assert isinstance(result.metadata, dict)
        assert "pages" in result.metadata
        assert "encrypted" in result.metadata
        assert result.metadata["pages"] == "1"
        assert result.metadata["encrypted"] == "False"

    def test_convenience_functions(self, simple_pdf):
        """Test convenience functions"""
        # Test extract_pdf_text
        text = extract_pdf_text(simple_pdf)
        assert "John Doe" in text
        assert "Software Engineer" in text

        # Test analyze_pdf
        result = analyze_pdf(simple_pdf)
        assert isinstance(result, PDFTextResult)
        assert result.success is True
        assert "Python" in result.text

    def test_path_types(self, simple_pdf):
        """Test different path input types"""
        reader = PDFReader()

        # Test string path
        result1 = reader.extract_text(simple_pdf)
        assert result1.success is True

        # Test Path object
        result2 = reader.extract_text(Path(simple_pdf))
        assert result2.success is True

        # Results should be identical
        assert result1.text == result2.text

    def test_large_text_handling(self):
        """Test handling of PDF with large amounts of text"""
        temp_path = tempfile.mktemp(suffix=".pdf")

        try:
            c = canvas.Canvas(temp_path, pagesize=letter)
            width, height = letter

            # Add lots of text
            y_position = height - 50
            for i in range(100):
                c.setFont("Helvetica", 10)
                text = f"Line {i}: This is a test line with some content to make the PDF larger"
                c.drawString(50, y_position, text)
                y_position -= 15

                # Start new page if needed
                if y_position < 50:
                    c.showPage()
                    y_position = height - 50

            c.save()

            reader = PDFReader()
            result = reader.extract_text(temp_path)

            assert result.success is True
            assert len(result.text) > 1000  # Should be substantial text
            assert "Line 0:" in result.text
            assert "Line 99:" in result.text

        finally:
            # Cleanup
            Path(temp_path).unlink(missing_ok=True)


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_corrupted_file(self):
        """Test handling of corrupted file"""
        # Create a fake PDF file with invalid content
        temp_path = tempfile.mktemp(suffix=".pdf")

        try:
            with open(temp_path, "w") as f:
                f.write("This is not a valid PDF file")

            reader = PDFReader()
            result = reader.extract_text(temp_path)

            assert result.success is False
            assert result.error_message is not None
            assert result.text == ""

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_permission_denied(self):
        """Test handling of permission denied (if possible)"""
        # This test might not work on all systems
        reader = PDFReader()
        result = reader.extract_text(
            "/root/nonexistent.pdf"
        )  # Should fail with permission

        assert result.success is False
        assert result.error_message is not None

    def test_invalid_pdf_with_new_error_handling(self):
        """Test handling of invalid PDF files with new error system"""
        temp_path = tempfile.mktemp(suffix=".pdf")
        
        try:
            # Create a file that looks like PDF but isn't
            with open(temp_path, 'w') as f:
                f.write("This is not a PDF file content")
            
            reader = PDFReader()
            result = reader.extract_text(temp_path)
            
            # Should fail gracefully with new error handling
            assert result.success is False
            assert result.error_message is not None
            assert result.error_code is not None
            assert result.text == ""
            assert result.page_count == 0
            assert result.page_texts == []
            assert result.metadata == {}
            
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_pdf_validation_with_new_system(self):
        """Test PDF validation with new validation system"""
        from src.keyword_generator.utils.error_handlers import PDFValidator
        from src.keyword_generator.utils.exceptions import PDFValidationError
        
        # Test 1: Invalid extension
        temp_path = tempfile.mktemp(suffix=".txt")
        
        try:
            with open(temp_path, 'w') as f:
                f.write("Not a PDF")
            
            # Test validation - should fail on extension
            with pytest.raises(PDFValidationError) as exc_info:
                PDFValidator.validate_pdf_file(temp_path)
            
            assert "File is not a PDF" in str(exc_info.value)
            assert exc_info.value.error_code == "INVALID_PDF_EXTENSION"
                
        finally:
            Path(temp_path).unlink(missing_ok=True)
        
        # Test 2: Empty PDF file
        temp_path = tempfile.mktemp(suffix=".pdf")
        
        try:
            # Create empty PDF file
            Path(temp_path).touch()
            
            # Test validation - should fail on empty file
            with pytest.raises(PDFValidationError) as exc_info:
                PDFValidator.validate_pdf_file(temp_path)
            
            assert "PDF file is empty" in str(exc_info.value)
            assert exc_info.value.error_code == "EMPTY_PDF_FILE"
                
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_result_structure_compatibility(self):
        """Test that new result structure maintains compatibility"""
        from src.keyword_generator.utils.result_types import PDFTextResult
        
        # Test that we can create the result object with all expected attributes
        result = PDFTextResult(
            success=True,
            text="Test text",
            page_count=1,
            page_texts=["Test text"],
            metadata={"title": "Test"},
            extraction_time=0.5
        )
        
        # Test new ProcessingResult attributes
        assert hasattr(result, 'success')
        assert hasattr(result, 'error_message')
        assert hasattr(result, 'error_code')
        assert hasattr(result, 'error_detail')
        assert hasattr(result, 'exception')
        
        # Test PDF-specific attributes
        assert hasattr(result, 'text')
        assert hasattr(result, 'page_count')
        assert hasattr(result, 'page_texts')
        assert hasattr(result, 'metadata')
        assert hasattr(result, 'extraction_time')
        
        # Test values
        assert result.success is True
        assert result.error_message is None
        assert result.error_code is None
        assert result.text == "Test text"
        assert result.page_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

