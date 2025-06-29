import pytest
from click.testing import CliRunner
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from src.keyword_generator.cli.commands import main


class TestCLICommands:
    """Test suite for CLI command functionality"""
    
    def setup_method(self):
        """Set up test fixtures - creates temporary files for each test"""
        self.runner = CliRunner()
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_pdf = Path(self.temp_dir) / "test_resume.pdf"
        
        # Create a minimal PDF for testing
        self.create_test_pdf(self.test_pdf)
    
    def teardown_method(self):
        """Clean up test fixtures - removes temporary files after each test"""
        shutil.rmtree(self.temp_dir)
    
    def create_test_pdf(self, path: Path):
        """Create a simple test PDF file using ReportLab"""
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(str(path))
        c.drawString(100, 750, "Test Resume")
        c.drawString(100, 700, "John Doe")
        c.drawString(100, 650, "Software Engineer")
        c.drawString(100, 600, "Python, JavaScript, React")
        c.save()
    
    def test_command_line_mode_success(self):
        """
        Test full command-line mode with all arguments provided.
        
        This tests the "power user" workflow where everything is specified
        via command line flags, no interactive prompts should appear.
        """
        output_path = Path(self.temp_dir) / 'output.pdf'
        
        with patch('src.keyword_generator.cli.commands.enhance_pdf_with_keywords') as mock_enhance:
            # Mock successful PDF processing
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.keywords_injected = ['python', 'developer', 'software']
            mock_result.processing_time = 1.5
            mock_result.original_text_length = 100
            mock_result.final_text_length = 150
            mock_enhance.return_value = mock_result
            
            result = self.runner.invoke(main, [
                str(self.test_pdf),
                '--keywords', 'python,developer,software',
                '--output', str(output_path),
                '--methods', 'white_text,margin'
            ])
            
            assert result.exit_code == 0
            assert 'Success!' in result.output
            assert 'python' in result.output
            assert 'developer' in result.output
            assert 'software' in result.output
    
    def test_missing_pdf_file(self):
        """
        Test error handling when PDF file doesn't exist.
        
        Should fail gracefully with a clear error message,
        not crash the application.
        """
        nonexistent_pdf = Path(self.temp_dir) / 'nonexistent.pdf'
        
        result = self.runner.invoke(main, [
            str(nonexistent_pdf),
            '--keywords', 'python,developer'
        ])
        
        # Click should catch the file not found error during argument parsing
        assert result.exit_code != 0
        assert 'does not exist' in result.output or 'No such file' in result.output
    
    def test_interactive_mode_with_input(self):
        """
        Test full interactive mode (NextJS create-app style).
        
        When no arguments provided, should prompt user for:
        1. PDF file path
        2. Keywords
        3. Output path (with default)
        """
        output_path = Path(self.temp_dir) / f"{self.test_pdf.stem}_optimized.pdf"
        
        with patch('src.keyword_generator.cli.commands.enhance_pdf_with_keywords') as mock_enhance:
            # Mock successful PDF processing
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.keywords_injected = ['python', 'developer', 'software']
            mock_result.processing_time = 1.5
            mock_result.original_text_length = 100
            mock_result.final_text_length = 150
            mock_enhance.return_value = mock_result
            
            # Simulate user input: PDF path, keywords, accept default output
            user_input = f"{self.test_pdf}\npython,developer,software\n\n"
            
            result = self.runner.invoke(main, input=user_input)
            
            assert result.exit_code == 0
            assert 'PDF Keyword Injector' in result.output
            assert 'Select you PDF resume' in result.output
            assert 'Add some keywords' in result.output
    
    def test_partial_interactive_mode(self):
        """
        Test hybrid mode where PDF provided but keywords missing.
        
        Should prompt only for missing information, not re-ask for PDF.
        This tests the progressive interactive approach.
        """
        with patch('src.keyword_generator.cli.commands.enhance_pdf_with_keywords') as mock_enhance:
            # Mock successful PDF processing
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.keywords_injected = ['python', 'developer', 'software']
            mock_result.processing_time = 1.5
            mock_result.original_text_length = 100
            mock_result.final_text_length = 150
            mock_enhance.return_value = mock_result
            
            # Simulate user input: keywords and accept default output
            user_input = "python,developer,software\n\n"
            
            result = self.runner.invoke(main, [str(self.test_pdf)], input=user_input)
            
            assert result.exit_code == 0
            assert 'Add some keywords' in result.output
            # Should NOT prompt for PDF since it was provided
            assert 'Select your PDF resume' not in result.output
    
    def test_empty_keywords_validation(self):
        """
        Test validation for empty/whitespace-only keywords.
        
        User might input: "  ,  , " or just hit enter.
        Should detect this and show validation error.
        """
        # Test with whitespace and empty keywords
        user_input = f"{self.test_pdf}\n   ,  , \n\n"
        
        result = self.runner.invoke(main, input=user_input)
        
        assert result.exit_code != 0
        assert 'No valid keywords provided' in result.output
    
    def test_help_text(self):
        """
        Test that help documentation is correct and complete.
        
        Should show usage, all options, and clear descriptions.
        """
        result = self.runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert 'INPUT_PDF' in result.output
        assert '--keywords' in result.output
        assert '--output' in result.output
        assert '--methods' in result.output
        assert '--debug' in result.output
    
    def test_default_output_path(self):
        """
        Test automatic output filename generation.
        
        When user doesn't specify output, should create:
        {original_name}_optimized.pdf in same directory
        """
        with patch('src.keyword_generator.cli.commands.enhance_pdf_with_keywords') as mock_enhance:
            # Mock successful PDF processing
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.keywords_injected = ['python', 'developer']
            mock_result.processing_time = 1.5
            mock_result.original_text_length = 100
            mock_result.final_text_length = 150
            mock_enhance.return_value = mock_result
            
            # Provide keywords but use default output (empty input)
            user_input = "python,developer\n\n"
            
            result = self.runner.invoke(main, [str(self.test_pdf)], input=user_input)
            
            assert result.exit_code == 0
            # Check that default output path was used
            expected_output = f"{self.test_pdf.stem}_optimized.pdf"
            assert expected_output in result.output
    
    def test_debug_mode(self):
        """
        Test debug mode flag functionality.
        
        --debug flag should be recognized and shown in configuration.
        Later this will make invisible text visible for testing.
        """
        output_path = Path(self.temp_dir) / 'debug_output.pdf'
        
        with patch('src.keyword_generator.cli.commands.enhance_pdf_with_keywords') as mock_enhance:
            # Mock successful PDF processing
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.keywords_injected = ['python', 'developer']
            mock_result.processing_time = 1.5
            mock_result.original_text_length = 100
            mock_result.final_text_length = 150
            mock_enhance.return_value = mock_result
            
            result = self.runner.invoke(main, [
                str(self.test_pdf),
                '--keywords', 'python,developer',
                '--output', str(output_path),
                '--debug'
            ])
            
            assert result.exit_code == 0
            assert 'Debug Mode: ON' in result.output

    def test_pdf_validation_error_with_new_system(self):
        """Test the new PDF validation error handling with specific exceptions"""
        # Create invalid PDF
        invalid_pdf = Path(self.temp_dir) / "invalid.pdf"
        invalid_pdf.write_text("Not a PDF")
        output_path = Path(self.temp_dir) / 'invalid_output.pdf'
        
        result = self.runner.invoke(main, [
            str(invalid_pdf),
            '--keywords', 'python,developer',
            '--output', str(output_path)
        ])
        
        assert result.exit_code != 0
        assert 'PDF Validation Error' in result.output
        assert 'Suggested Solutions:' in result.output
        assert 'Check that the PDF file is not corrupted' in result.output

    def test_file_permission_error_handling(self):
        """Test file permission error handling"""
        import os
        
        # Try to write to a location that requires permissions (skip on Windows)
        if os.name != 'nt':
            result = self.runner.invoke(main, [
                str(self.test_pdf),
                '--keywords', 'python,developer',
                '--output', '/root/restricted.pdf'
            ])
            
            assert result.exit_code != 0
            assert ('Output path Error' in result.output or 
                   'Validation Failed' in result.output or
                   'Permission' in result.output)

    def test_processing_error_handling(self):
        """Test processing error handling with mock PDF errors"""
        output_path = Path(self.temp_dir) / 'error_output.pdf'
        
        with patch('src.keyword_generator.cli.commands.enhance_pdf_with_keywords') as mock_enhance:
            # Mock a processing error
            mock_result = MagicMock()
            mock_result.success = False
            mock_result.error_code = "PDF_CORRUPTED"
            mock_result.error_message = "PDF file appears corrupted"
            mock_result.error_detail = {'path': str(self.test_pdf)}
            mock_enhance.return_value = mock_result
            
            result = self.runner.invoke(main, [
                str(self.test_pdf),
                '--keywords', 'python,developer',
                '--output', str(output_path)
            ])
            
            assert result.exit_code != 0
            assert 'Corrupted PDF' in result.output
            assert 'Try opening the PDF in a PDF viewer' in result.output

    def test_encrypted_pdf_error_handling(self):
        """Test encrypted PDF error handling"""
        output_path = Path(self.temp_dir) / 'encrypted_output.pdf'
        
        with patch('src.keyword_generator.cli.commands.enhance_pdf_with_keywords') as mock_enhance:
            # Mock an encrypted PDF error
            mock_result = MagicMock()
            mock_result.success = False
            mock_result.error_code = "PDF_ENCRYPTED"
            mock_result.error_message = "PDF is password-protected"
            mock_result.error_detail = {'path': str(self.test_pdf)}
            mock_enhance.return_value = mock_result
            
            result = self.runner.invoke(main, [
                str(self.test_pdf),
                '--keywords', 'python,developer',
                '--output', str(output_path)
            ])
            
            assert result.exit_code != 0
            assert 'Encrypted PDF' in result.output
            assert 'Remove password protection' in result.output

    def test_disk_space_error_handling(self):
        """Test insufficient disk space error handling"""
        output_path = Path(self.temp_dir) / 'space_output.pdf'
        
        with patch('src.keyword_generator.cli.commands.enhance_pdf_with_keywords') as mock_enhance:
            # Mock a disk space error
            mock_result = MagicMock()
            mock_result.success = False
            mock_result.error_code = "INSUFFICIENT_DISK_SPACE"
            mock_result.error_message = "Insufficient disk space"
            mock_result.error_detail = {'available_mb': 5.2, 'required_mb': 10}
            mock_enhance.return_value = mock_result
            
            result = self.runner.invoke(main, [
                str(self.test_pdf),
                '--keywords', 'python,developer',
                '--output', str(output_path)
            ])
            
            assert result.exit_code != 0
            assert 'Disk Space Error' in result.output
            assert 'Free up disk space' in result.output
            assert '5.2MB available' in result.output


class TestCLIValidation:
    """Test suite for input validation and parsing"""
    
    def test_keyword_parsing_various_formats(self):
        """
        Test various keyword input formats are parsed correctly.
        
        Should handle:
        - Clean: "python,developer,software"
        - Spaces: "python, developer , software"  
        - Empty entries: "python,   ,developer,  , software"
        """
        runner = CliRunner()
        temp_dir = tempfile.mkdtemp()
        test_pdf = Path(temp_dir) / "test.pdf"
        
        try:
            # Create test PDF
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(str(test_pdf))
            c.drawString(100, 750, "Test")
            c.save()
            
            with patch('src.keyword_generator.cli.commands.enhance_pdf_with_keywords') as mock_enhance:
                # Mock successful PDF processing
                mock_result = MagicMock()
                mock_result.success = True
                mock_result.keywords_injected = []
                mock_result.processing_time = 1.0
                mock_result.original_text_length = 100
                mock_result.final_text_length = 100
                
                # Test cases: input -> expected parsed keywords
                test_cases = [
                    ("python,developer,software", ["python", "developer", "software"]),
                    ("python, developer , software", ["python", "developer", "software"]),
                    ("python,   ,developer,  , software", ["python", "developer", "software"]),
                    ("  python  , developer, software  ", ["python", "developer", "software"]),
                ]
                
                for keyword_input, expected_keywords in test_cases:
                    mock_result.keywords_injected = expected_keywords
                    mock_enhance.return_value = mock_result
                    
                    output_path = Path(temp_dir) / 'test_output.pdf'
                    result = runner.invoke(main, [
                        str(test_pdf),
                        '--keywords', keyword_input,
                        '--output', str(output_path)
                    ])
                    
                    assert result.exit_code == 0
                    # Verify all expected keywords appear in output
                    for keyword in expected_keywords:
                        assert keyword in result.output
        
        finally:
            shutil.rmtree(temp_dir)
    
    def test_method_parsing_validation(self):
        """
        Test injection method parsing and validation.
        
        Should accept valid methods and use defaults appropriately.
        """
        runner = CliRunner()
        temp_dir = tempfile.mkdtemp()
        test_pdf = Path(temp_dir) / "test.pdf"
        
        try:
            # Create test PDF
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(str(test_pdf))
            c.drawString(100, 750, "Test")
            c.save()
            
            with patch('src.keyword_generator.cli.commands.enhance_pdf_with_keywords') as mock_enhance:
                # Mock successful PDF processing
                mock_result = MagicMock()
                mock_result.success = True
                mock_result.keywords_injected = ['python']
                mock_result.processing_time = 1.0
                mock_result.original_text_length = 100
                mock_result.final_text_length = 100
                mock_enhance.return_value = mock_result
                
                # Test valid methods
                output_path = Path(temp_dir) / 'test_output.pdf'
                result = runner.invoke(main, [
                    str(test_pdf),
                    '--keywords', 'python',
                    '--methods', 'white_text,margin,tiny_font',
                    '--output', str(output_path)
                ])
                
                assert result.exit_code == 0
                assert 'white_text' in result.output
                assert 'margin' in result.output
                assert 'tiny_font' in result.output
                
                # Test default methods (when not specified)
                output_path2 = Path(temp_dir) / 'test_output2.pdf'
                result = runner.invoke(main, [
                    str(test_pdf),
                    '--keywords', 'python',
                    '--output', str(output_path2)
                ])
                
                assert result.exit_code == 0
                # Should use default methods
                assert 'white_text' in result.output or 'tiny_font' in result.output
        
        finally:
            shutil.rmtree(temp_dir)
    
    def test_pdf_validation_error_handling(self):
        """
        Test PDF validation and error handling.
        
        Should handle various file issues gracefully.
        """
        runner = CliRunner()
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Test with non-PDF file
            fake_pdf = Path(temp_dir) / "fake.pdf"
            fake_pdf.write_text("This is not a PDF file")
            
            with patch('src.keyword_generator.cli.commands.PDFReader') as mock_reader:
                # Mock PDF reader to simulate read error
                mock_reader_instance = MagicMock()
                mock_validation_result = MagicMock()
                mock_validation_result.success = False
                mock_validation_result.error_message = "Invalid PDF file"
                mock_reader_instance.extract_text.return_value = mock_validation_result
                mock_reader.return_value = mock_reader_instance
                
                output_path = Path(temp_dir) / 'test_output.pdf'
                result = runner.invoke(main, [
                    str(fake_pdf),
                    '--keywords', 'python,developer',
                    '--output', str(output_path)
                ])
                
                assert result.exit_code != 0
                assert ('PDF Validation Error' in result.output or 
                       'Error reading PDF' in result.output or
                       'File is not a PDF' in result.output)
        
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])