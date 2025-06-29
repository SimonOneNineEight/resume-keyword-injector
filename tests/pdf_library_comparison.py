#!/usr/bin/env python3
"""
PDF Library Comparison Test Script
Tests pypdf, pdfplumber, and reportlab for:
1. Text extraction accuracy
2. Invisible keyword injection methods
3. Performance metrics
4. ATS compatibility
"""

import time
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Tuple
import traceback

try:
    import pypdf
    from pypdf import PdfReader, PdfWriter
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    print("Warning: pypdf not available")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("Warning: pdfplumber not available")

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.colors import white, black
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not available")


class PDFLibraryTester:
    def __init__(self):
        self.results = {
            'text_extraction': {},
            'keyword_injection': {},
            'performance': {},
            'errors': []
        }
    
    def create_sample_pdf(self) -> str:
        """Create a sample PDF for testing"""
        if not REPORTLAB_AVAILABLE:
            return None
            
        temp_path = tempfile.mktemp(suffix='.pdf')
        
        c = canvas.Canvas(temp_path, pagesize=letter)
        width, height = letter
        
        # Add normal visible content (resume-like)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 100, "John Doe")
        
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 130, "Software Engineer")
        c.drawString(100, height - 160, "Experience:")
        c.drawString(120, height - 180, "• Developed Python applications")
        c.drawString(120, height - 200, "• Worked with databases and APIs")
        c.drawString(120, height - 220, "• Led team of 5 developers")
        
        c.drawString(100, height - 260, "Skills:")
        c.drawString(120, height - 280, "Python, JavaScript, React, SQL")
        
        c.save()
        return temp_path
    
    def test_text_extraction_pypdf(self, pdf_path: str) -> Dict:
        """Test text extraction using pypdf"""
        if not PYPDF_AVAILABLE:
            return {"error": "pypdf not available"}
        
        try:
            start_time = time.time()
            
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
            
            extraction_time = time.time() - start_time
            
            return {
                "library": "pypdf",
                "text_length": len(text),
                "text_preview": text[:200] + "..." if len(text) > 200 else text,
                "extraction_time": extraction_time,
                "pages_count": len(reader.pages),
                "success": True
            }
        except Exception as e:
            return {
                "library": "pypdf",
                "error": str(e),
                "success": False
            }
    
    def test_text_extraction_pdfplumber(self, pdf_path: str) -> Dict:
        """Test text extraction using pdfplumber"""
        if not PDFPLUMBER_AVAILABLE:
            return {"error": "pdfplumber not available"}
        
        try:
            start_time = time.time()
            
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
            
            extraction_time = time.time() - start_time
            
            return {
                "library": "pdfplumber",
                "text_length": len(text),
                "text_preview": text[:200] + "..." if len(text) > 200 else text,
                "extraction_time": extraction_time,
                "pages_count": len(pdf.pages),
                "success": True
            }
        except Exception as e:
            return {
                "library": "pdfplumber",
                "error": str(e),
                "success": False
            }
    
    def test_invisible_keyword_injection_reportlab(self, keywords: List[str]) -> Dict:
        """Test invisible keyword injection using reportlab"""
        if not REPORTLAB_AVAILABLE:
            return {"error": "reportlab not available"}
        
        results = {}
        temp_path = tempfile.mktemp(suffix='.pdf')
        
        try:
            c = canvas.Canvas(temp_path, pagesize=letter)
            width, height = letter
            
            # Visible content
            c.setFont("Helvetica", 12)
            c.drawString(100, height - 100, "Test Resume")
            c.drawString(100, height - 130, "Software Engineer Position")
            
            # Method 1: White text on white background
            c.setFillColor(white)
            c.setFont("Helvetica", 12)
            keyword_text = " ".join(keywords)
            c.drawString(100, height - 160, f"INVISIBLE: {keyword_text}")
            
            # Method 2: Tiny font size
            c.setFillColor(black)
            c.setFont("Helvetica", 0.1)  # Very small font
            c.drawString(100, height - 170, f"TINY: {keyword_text}")
            
            # Method 3: Margin placement
            c.setFont("Helvetica", 8)
            c.drawString(10, 10, keyword_text)  # Bottom left margin
            c.drawString(width - 200, 10, keyword_text)  # Bottom right margin
            
            c.save()
            
            # Test if keywords are extractable
            pypdf_result = self.test_text_extraction_pypdf(temp_path)
            pdfplumber_result = self.test_text_extraction_pdfplumber(temp_path)
            
            results = {
                "injection_methods": ["white_text", "tiny_font", "margin_placement"],
                "keywords_injected": keywords,
                "file_created": True,
                "file_path": temp_path,
                "pypdf_extraction": pypdf_result,
                "pdfplumber_extraction": pdfplumber_result,
                "success": True
            }
            
        except Exception as e:
            results = {
                "error": str(e),
                "success": False
            }
        
        return results
    
    def test_pypdf_keyword_injection(self, original_pdf: str, keywords: List[str]) -> Dict:
        """Test keyword injection by modifying existing PDF with pypdf"""
        if not PYPDF_AVAILABLE:
            return {"error": "pypdf not available"}
        
        try:
            temp_path = tempfile.mktemp(suffix='.pdf')
            
            # Read original PDF
            reader = PdfReader(original_pdf)
            writer = PdfWriter()
            
            # Copy all pages
            for page in reader.pages:
                writer.add_page(page)
            
            # Try to add invisible content (limited with pypdf)
            # Note: pypdf is better for reading than modifying
            
            with open(temp_path, 'wb') as output_file:
                writer.write(output_file)
            
            # Test extraction from modified PDF
            extraction_result = self.test_text_extraction_pypdf(temp_path)
            
            return {
                "method": "pypdf_modification",
                "original_pdf": original_pdf,
                "modified_pdf": temp_path,
                "extraction_result": extraction_result,
                "success": True,
                "note": "pypdf is limited for content modification"
            }
            
        except Exception as e:
            return {
                "method": "pypdf_modification",
                "error": str(e),
                "success": False
            }
    
    def run_comprehensive_test(self) -> Dict:
        """Run all tests and compile results"""
        print("🔍 Starting PDF Library Comparison Tests...")
        
        # Create sample PDF
        print("\n1. Creating sample PDF...")
        sample_pdf = self.create_sample_pdf()
        if not sample_pdf:
            print("❌ Failed to create sample PDF")
            return {"error": "Could not create sample PDF"}
        
        print(f"✅ Sample PDF created: {sample_pdf}")
        
        # Test text extraction
        print("\n2. Testing text extraction...")
        
        print("   Testing pypdf...")
        pypdf_result = self.test_text_extraction_pypdf(sample_pdf)
        self.results['text_extraction']['pypdf'] = pypdf_result
        
        print("   Testing pdfplumber...")
        pdfplumber_result = self.test_text_extraction_pdfplumber(sample_pdf)
        self.results['text_extraction']['pdfplumber'] = pdfplumber_result
        
        # Test keyword injection
        print("\n3. Testing keyword injection...")
        test_keywords = ["Python", "React", "AWS", "Docker", "Kubernetes", "Machine Learning"]
        
        print("   Testing reportlab injection...")
        reportlab_injection = self.test_invisible_keyword_injection_reportlab(test_keywords)
        self.results['keyword_injection']['reportlab'] = reportlab_injection
        
        print("   Testing pypdf modification...")
        pypdf_injection = self.test_pypdf_keyword_injection(sample_pdf, test_keywords)
        self.results['keyword_injection']['pypdf'] = pypdf_injection
        
        return self.results
    
    def print_comparison_report(self):
        """Print a comprehensive comparison report"""
        print("\n" + "="*80)
        print("📊 PDF LIBRARY COMPARISON REPORT")
        print("="*80)
        
        # Text Extraction Comparison
        print("\n🔤 TEXT EXTRACTION COMPARISON")
        print("-" * 50)
        
        extraction_results = self.results.get('text_extraction', {})
        
        if 'pypdf' in extraction_results:
            result = extraction_results['pypdf']
            print(f"\n📚 PYPDF:")
            if result.get('success'):
                print(f"   ✅ Success: {result['text_length']} characters extracted")
                print(f"   ⏱️  Time: {result['extraction_time']:.4f}s")
                print(f"   📄 Pages: {result['pages_count']}")
                print(f"   📝 Preview: {result['text_preview']}")
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
        
        if 'pdfplumber' in extraction_results:
            result = extraction_results['pdfplumber']
            print(f"\n🔍 PDFPLUMBER:")
            if result.get('success'):
                print(f"   ✅ Success: {result['text_length']} characters extracted")
                print(f"   ⏱️  Time: {result['extraction_time']:.4f}s")
                print(f"   📄 Pages: {result['pages_count']}")
                print(f"   📝 Preview: {result['text_preview']}")
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
        
        # Keyword Injection Comparison
        print("\n🎯 KEYWORD INJECTION COMPARISON")
        print("-" * 50)
        
        injection_results = self.results.get('keyword_injection', {})
        
        if 'reportlab' in injection_results:
            result = injection_results['reportlab']
            print(f"\n📊 REPORTLAB:")
            if result.get('success'):
                print(f"   ✅ Success: PDF created with invisible keywords")
                print(f"   🎨 Methods: {', '.join(result['injection_methods'])}")
                print(f"   🔑 Keywords: {', '.join(result['keywords_injected'])}")
                
                # Check if keywords are detectable
                pypdf_extract = result.get('pypdf_extraction', {})
                pdfplumber_extract = result.get('pdfplumber_extraction', {})
                
                if pypdf_extract.get('success'):
                    print(f"   🔍 pypdf detection: {pypdf_extract['text_length']} chars")
                if pdfplumber_extract.get('success'):
                    print(f"   🔍 pdfplumber detection: {pdfplumber_extract['text_length']} chars")
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
        
        if 'pypdf' in injection_results:
            result = injection_results['pypdf']
            print(f"\n📚 PYPDF MODIFICATION:")
            if result.get('success'):
                print(f"   ⚠️  Limited: {result.get('note', 'pypdf modification attempted')}")
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
        
        # Recommendations
        print("\n🏆 RECOMMENDATIONS")
        print("-" * 50)
        
        print("\n📖 For Text Extraction:")
        if extraction_results.get('pdfplumber', {}).get('success') and extraction_results.get('pypdf', {}).get('success'):
            pdfplumber_time = extraction_results['pdfplumber'].get('extraction_time', float('inf'))
            pypdf_time = extraction_results['pypdf'].get('extraction_time', float('inf'))
            
            if pdfplumber_time < pypdf_time:
                print("   🥇 Winner: pdfplumber (faster + more accurate)")
            else:
                print("   🥇 Winner: pypdf (faster)")
                print("   🥈 Alternative: pdfplumber (more features)")
        elif extraction_results.get('pdfplumber', {}).get('success'):
            print("   🥇 Winner: pdfplumber (only working option)")
        elif extraction_results.get('pypdf', {}).get('success'):
            print("   🥇 Winner: pypdf (only working option)")
        else:
            print("   ❌ No working extraction method found")
        
        print("\n✏️  For Keyword Injection:")
        if injection_results.get('reportlab', {}).get('success'):
            print("   🥇 Winner: reportlab (full control over PDF creation)")
            print("   💡 Best method: Create new PDF with invisible keywords")
        else:
            print("   ❌ No working injection method found")
        
        print("\n🎯 FINAL RECOMMENDATION:")
        print("   📋 Strategy: reportlab for PDF creation + pdfplumber for text extraction")
        print("   🔄 Workflow: Extract text → Generate keywords → Create new PDF with invisible keywords")
        print("   🎨 Invisible method: White text + tiny fonts + margin placement")


def main():
    """Run the PDF library comparison"""
    tester = PDFLibraryTester()
    
    print("Starting PDF Library Comparison Test...")
    print(f"pypdf available: {PYPDF_AVAILABLE}")
    print(f"pdfplumber available: {PDFPLUMBER_AVAILABLE}")
    print(f"reportlab available: {REPORTLAB_AVAILABLE}")
    
    if not any([PYPDF_AVAILABLE, PDFPLUMBER_AVAILABLE, REPORTLAB_AVAILABLE]):
        print("❌ No PDF libraries available. Install with:")
        print("   pip install pypdf pdfplumber reportlab")
        return
    
    try:
        results = tester.run_comprehensive_test()
        tester.print_comparison_report()
        
        print(f"\n💾 Test completed. Check temp files for samples.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()