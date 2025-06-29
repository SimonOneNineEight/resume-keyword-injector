"""
Comprehensive tests for PDF Writer with invisible keyword injection
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.keyword_generator.pdf.writer import (
    PDFWriter, 
    InvisibleMethod, 
    InjectionStrategy,
    create_ats_optimized_pdf, 
    enhance_pdf_with_keywords
)
from src.keyword_generator.utils.result_types import KeywordInjectionResult
from src.keyword_generator.pdf.reader import PDFReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


class TestPDFWriter:
    
    @pytest.fixture
    def sample_resume_text(self):
        """Sample resume content for testing"""
        return """John Doe
Software Engineer

Experience:
• Senior Developer at TechCorp (2020-2024)
• Built scalable web applications using Python and React
• Led team of 5 developers on microservices architecture
• Improved system performance by 40%

Skills:
Python, JavaScript, React, AWS, Docker, Kubernetes

Education:
Computer Science Degree - University of Tech (2016-2020)
GPA: 3.8/4.0"""
    
    @pytest.fixture
    def test_keywords(self):
        """Sample keywords for ATS optimization"""
        return [
            "Python", "React", "AWS", "Docker", "Kubernetes",
            "Machine Learning", "DevOps", "Agile", "Scrum",
            "API Development", "Database Design", "CI/CD"
        ]
    
    @pytest.fixture
    def simple_pdf(self):
        """Create a simple PDF for enhancement testing"""
        temp_path = tempfile.mktemp(suffix='.pdf')
        
        c = canvas.Canvas(temp_path, pagesize=letter)
        width, height = letter
        
        # Add basic content
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 100, "Jane Smith")
        
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 130, "Data Scientist")
        c.drawString(100, height - 160, "Skills: Python, Machine Learning")
        c.drawString(100, height - 190, "Experience: 3 years in AI/ML")
        
        c.save()
        yield temp_path
        
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)
    
    def test_writer_initialization(self):
        """Test PDFWriter initialization with different parameters"""
        # Default initialization
        writer = PDFWriter()
        assert writer.page_size == letter
        assert writer.default_font == "Helvetica"
        assert writer.debug_mode is False
        assert writer.width > 0
        assert writer.height > 0
        
        # Custom initialization
        writer_debug = PDFWriter(debug_mode=True, default_font="Times-Roman")
        assert writer_debug.debug_mode is True
        assert writer_debug.default_font == "Times-Roman"
    
    def test_invisible_method_enum(self):
        """Test InvisibleMethod enum values"""
        # Test all enum values
        assert InvisibleMethod.WHITE_TEXT.value == "white_text"
        assert InvisibleMethod.TINY_FONT.value == "tiny_font"
        assert InvisibleMethod.MARGIN_PLACEMENT.value == "margin"
        assert InvisibleMethod.BACKGROUND_LAYER.value == "background"
        assert InvisibleMethod.TRANSPARENT_TEXT.value == "transparent"
        
        # Test enum list comprehension
        methods = [m.value for m in InvisibleMethod]
        assert len(methods) == 5
        assert "white_text" in methods
    
    def test_injection_strategy_dataclass(self):
        """Test InjectionStrategy configuration"""
        # Default strategy
        strategy = InjectionStrategy(methods=[InvisibleMethod.WHITE_TEXT])
        assert strategy.keyword_density == 0.1
        assert strategy.position_randomization is True
        assert strategy.font_size_range == (0.1, 0.5)
        
        # Custom strategy
        custom_strategy = InjectionStrategy(
            methods=[InvisibleMethod.TINY_FONT, InvisibleMethod.TRANSPARENT_TEXT],
            keyword_density=0.2,
            color_opacity=0.05
        )
        assert len(custom_strategy.methods) == 2
        assert custom_strategy.keyword_density == 0.2
        assert custom_strategy.color_opacity == 0.05
    
    def test_create_optimized_resume_basic(self, sample_resume_text, test_keywords):
        """Test basic PDF creation with invisible keywords"""
        temp_path = tempfile.mktemp(suffix='.pdf')
        
        try:
            writer = PDFWriter()
            result = writer.create_optimized_resume(
                original_content=sample_resume_text,
                keywords=test_keywords[:5],
                output_path=temp_path
            )
            
            # Check success
            assert result.success is True
            assert result.error_message is None
            assert Path(temp_path).exists()
            assert Path(temp_path).stat().st_size > 0
            
            # Check result metadata
            assert len(result.keywords_injected) > 0
            assert len(result.injection_methods) > 0
            assert result.processing_time > 0
            assert result.original_text_length == len(sample_resume_text)
            assert result.final_text_length > result.original_text_length
            assert result.output_path == temp_path
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_individual_invisible_methods(self, sample_resume_text, test_keywords):
        """Test each invisible injection method individually"""
        methods_to_test = [
            InvisibleMethod.WHITE_TEXT,
            InvisibleMethod.TINY_FONT,
            InvisibleMethod.MARGIN_PLACEMENT,
            InvisibleMethod.BACKGROUND_LAYER,
            InvisibleMethod.TRANSPARENT_TEXT
        ]
        
        for method in methods_to_test:
            temp_path = tempfile.mktemp(suffix='.pdf')
            
            try:
                strategy = InjectionStrategy(methods=[method])
                writer = PDFWriter()
                
                result = writer.create_optimized_resume(
                    original_content=sample_resume_text,
                    keywords=test_keywords[:3],
                    output_path=temp_path,
                    strategy=strategy
                )
                
                # Check success
                assert result.success is True, f"Method {method.value} failed"
                assert Path(temp_path).exists()
                
                # Check method was used
                assert method.value in result.injection_methods
                assert len(result.keywords_injected) > 0
                
            finally:
                Path(temp_path).unlink(missing_ok=True)
    
    def test_multiple_method_combination(self, sample_resume_text, test_keywords):
        """Test combining multiple invisible methods"""
        method_combinations = [
            [InvisibleMethod.WHITE_TEXT, InvisibleMethod.MARGIN_PLACEMENT],
            [InvisibleMethod.TINY_FONT, InvisibleMethod.TRANSPARENT_TEXT],
            [InvisibleMethod.WHITE_TEXT, InvisibleMethod.TINY_FONT, InvisibleMethod.BACKGROUND_LAYER]
        ]
        
        for methods in method_combinations:
            temp_path = tempfile.mktemp(suffix='.pdf')
            
            try:
                strategy = InjectionStrategy(methods=methods)
                writer = PDFWriter()
                
                result = writer.create_optimized_resume(
                    original_content=sample_resume_text,
                    keywords=test_keywords[:4],
                    output_path=temp_path,
                    strategy=strategy
                )
                
                assert result.success is True
                
                # Check all methods were used
                expected_methods = [m.value for m in methods]
                assert all(method in result.injection_methods for method in expected_methods)
                
            finally:
                Path(temp_path).unlink(missing_ok=True)
    
    def test_keyword_detection_verification(self, sample_resume_text, test_keywords):
        """Test that injected keywords are detectable by ATS (PDF reader)"""
        temp_path = tempfile.mktemp(suffix='.pdf')
        
        try:
            writer = PDFWriter()
            test_keywords_subset = test_keywords[:4]
            
            result = writer.create_optimized_resume(
                original_content=sample_resume_text,
                keywords=test_keywords_subset,
                output_path=temp_path
            )
            
            assert result.success is True
            
            # Use our PDFReader to verify keywords are detectable
            reader = PDFReader()
            extraction = reader.extract_text(temp_path)
            
            assert extraction.success is True
            
            # Check that keywords are actually in the extracted text
            detected_keywords = []
            for keyword in test_keywords_subset:
                if keyword.lower() in extraction.text.lower():
                    detected_keywords.append(keyword)
            
            # At least 75% of keywords should be detectable
            detection_rate = len(detected_keywords) / len(test_keywords_subset)
            assert detection_rate >= 0.75, f"Detection rate too low: {detection_rate:.2f}"
            
            # Text should be longer than original (due to invisible keywords)
            assert len(extraction.text) > len(sample_resume_text)
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_debug_mode_functionality(self, sample_resume_text, test_keywords):
        """Test debug mode makes invisible content slightly visible"""
        temp_path_normal = tempfile.mktemp(suffix='.pdf')
        temp_path_debug = tempfile.mktemp(suffix='.pdf')
        
        try:
            # Create normal PDF
            writer_normal = PDFWriter(debug_mode=False)
            result_normal = writer_normal.create_optimized_resume(
                original_content=sample_resume_text,
                keywords=test_keywords[:3],
                output_path=temp_path_normal
            )
            
            # Create debug PDF
            writer_debug = PDFWriter(debug_mode=True)
            result_debug = writer_debug.create_optimized_resume(
                original_content=sample_resume_text,
                keywords=test_keywords[:3],
                output_path=temp_path_debug
            )
            
            assert result_normal.success is True
            assert result_debug.success is True
            
            # Both should have keywords injected
            assert len(result_normal.keywords_injected) > 0
            assert len(result_debug.keywords_injected) > 0
            
            # Files should exist and have content
            assert Path(temp_path_normal).exists()
            assert Path(temp_path_debug).exists()
            
        finally:
            for path in [temp_path_normal, temp_path_debug]:
                Path(path).unlink(missing_ok=True)
    
    def test_enhance_existing_pdf(self, simple_pdf, test_keywords):
        """Test enhancing existing PDF with keywords"""
        enhanced_pdf = tempfile.mktemp(suffix='.pdf')
        
        try:
            writer = PDFWriter()
            result = writer.enhance_existing_pdf(
                input_path=simple_pdf,
                keywords=test_keywords[:4],
                output_path=enhanced_pdf
            )
            
            assert result.success is True
            assert Path(enhanced_pdf).exists()
            assert len(result.keywords_injected) > 0
            
            # Verify original content + keywords are present
            reader = PDFReader()
            extraction = reader.extract_text(enhanced_pdf)
            
            assert extraction.success is True
            # Should contain original content
            assert "Jane Smith" in extraction.text
            assert "Data Scientist" in extraction.text
            
            # Should contain some injected keywords
            detected_count = 0
            for keyword in test_keywords[:4]:
                if keyword.lower() in extraction.text.lower():
                    detected_count += 1
            
            assert detected_count > 0
            
        finally:
            Path(enhanced_pdf).unlink(missing_ok=True)
    
    def test_large_keyword_list(self, sample_resume_text):
        """Test handling of large keyword lists"""
        # Generate large keyword list
        large_keyword_list = [f"keyword_{i}" for i in range(50)]
        temp_path = tempfile.mktemp(suffix='.pdf')
        
        try:
            writer = PDFWriter()
            result = writer.create_optimized_resume(
                original_content=sample_resume_text,
                keywords=large_keyword_list,
                output_path=temp_path
            )
            
            assert result.success is True
            assert len(result.keywords_injected) > 0
            # Should handle large lists without errors
            assert len(result.keywords_injected) <= len(large_keyword_list)
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_empty_content_handling(self, test_keywords):
        """Test handling of empty or minimal content"""
        temp_path = tempfile.mktemp(suffix='.pdf')
        
        try:
            writer = PDFWriter()
            result = writer.create_optimized_resume(
                original_content="",  # Empty content
                keywords=test_keywords[:3],
                output_path=temp_path
            )
            
            assert result.success is True
            assert Path(temp_path).exists()
            assert len(result.keywords_injected) > 0
            
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestConvenienceFunctions:
    """Test convenience functions for common use cases"""
    
    @pytest.fixture
    def sample_text(self):
        return "John Doe\nSoftware Engineer\nPython, JavaScript, React experience"
    
    @pytest.fixture
    def keywords(self):
        return ["Python", "React", "AWS", "Docker"]
    
    def test_create_ats_optimized_pdf_default(self, sample_text, keywords):
        """Test create_ats_optimized_pdf with default parameters"""
        temp_path = tempfile.mktemp(suffix='.pdf')
        
        try:
            result = create_ats_optimized_pdf(
                original_text=sample_text,
                keywords=keywords,
                output_path=temp_path
            )
            
            assert result.success is True
            assert Path(temp_path).exists()
            assert len(result.keywords_injected) > 0
            # Should use default methods
            assert "white_text" in result.injection_methods
            assert "tiny_font" in result.injection_methods
            assert "transparent" in result.injection_methods
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_create_ats_optimized_pdf_custom_methods(self, sample_text, keywords):
        """Test create_ats_optimized_pdf with custom methods"""
        temp_path = tempfile.mktemp(suffix='.pdf')
        
        try:
            result = create_ats_optimized_pdf(
                original_text=sample_text,
                keywords=keywords,
                output_path=temp_path,
                methods=["white_text", "margin"]
            )
            
            assert result.success is True
            assert "white_text" in result.injection_methods
            assert "margin" in result.injection_methods
            assert len(result.injection_methods) == 2
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_enhance_pdf_with_keywords_function(self, keywords):
        """Test enhance_pdf_with_keywords convenience function"""
        # Create original PDF
        original_pdf = tempfile.mktemp(suffix='.pdf')
        enhanced_pdf = tempfile.mktemp(suffix='.pdf')
        
        try:
            # Create simple original PDF
            c = canvas.Canvas(original_pdf, pagesize=letter)
            c.setFont("Helvetica", 12)
            c.drawString(100, 700, "Test Resume")
            c.drawString(100, 680, "Software Engineer")
            c.save()
            
            # Enhance with keywords
            result = enhance_pdf_with_keywords(
                input_pdf=original_pdf,
                keywords=keywords,
                output_path=enhanced_pdf
            )
            
            assert result.success is True
            assert Path(enhanced_pdf).exists()
            assert len(result.keywords_injected) > 0
            
        finally:
            for path in [original_pdf, enhanced_pdf]:
                Path(path).unlink(missing_ok=True)


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_invalid_output_path(self):
        """Test handling of invalid output paths"""
        writer = PDFWriter()
        
        result = writer.create_optimized_resume(
            original_content="Test content",
            keywords=["test"],
            output_path="/invalid/directory/file.pdf"  # Invalid path
        )
        
        assert result.success is False
        assert result.error_message is not None
        assert "permission" in result.error_message.lower() or "no such file" in result.error_message.lower()
    
    def test_invalid_input_pdf_enhancement(self):
        """Test enhancing non-existent PDF"""
        writer = PDFWriter()
        temp_output = tempfile.mktemp(suffix='.pdf')
        
        try:
            result = writer.enhance_existing_pdf(
                input_path="/nonexistent/file.pdf",
                keywords=["test"],
                output_path=temp_output
            )
            
            assert result.success is False
            assert result.error_message is not None
            assert "Input file not found" in result.error_message
            
        finally:
            Path(temp_output).unlink(missing_ok=True)
    
    def test_invalid_injection_methods(self):
        """Test handling of invalid injection method names"""
        with pytest.raises(ValueError) as exc_info:
            create_ats_optimized_pdf(
                original_text="Test",
                keywords=["test"],
                output_path="test.pdf",
                methods=["invalid_method"]  # Invalid method name
            )
        
        assert "Invalid injection method" in str(exc_info.value)
    
    def test_empty_keywords_list(self):
        """Test handling of empty keywords list"""
        temp_path = tempfile.mktemp(suffix='.pdf')
        
        try:
            result = create_ats_optimized_pdf(
                original_text="Test content",
                keywords=[],  # Empty keywords
                output_path=temp_path
            )
            
            # Should succeed but with no keywords injected
            assert result.success is True
            assert len(result.keywords_injected) == 0
            
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestPerformance:
    """Test performance characteristics"""
    
    def test_processing_time_reasonable(self):
        """Test that processing time is reasonable for typical use"""
        temp_path = tempfile.mktemp(suffix='.pdf')
        
        try:
            # Create a reasonably sized resume
            large_content = "John Doe\nSoftware Engineer\n" + "\n".join([
                f"• Experience line {i}: Worked on various projects using different technologies"
                for i in range(20)
            ])
            
            result = create_ats_optimized_pdf(
                original_text=large_content,
                keywords=["Python", "React", "AWS", "Docker", "Kubernetes"],
                output_path=temp_path
            )
            
            assert result.success is True
            # Should complete in reasonable time (less than 1 second for this size)
            assert result.processing_time < 1.0
            
        finally:
            Path(temp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])