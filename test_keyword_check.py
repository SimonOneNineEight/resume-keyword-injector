#!/usr/bin/env python3
"""
Quick test script to check if keywords were injected into PDF
"""

from pathlib import Path
import sys
sys.path.append('src')

from keyword_generator.pdf.reader import PDFReader

def check_keywords_in_pdf(pdf_path, expected_keywords):
    """Check if keywords exist in PDF text"""
    reader = PDFReader()
    result = reader.extract_text(pdf_path)
    
    if not result.success:
        print(f"❌ Error reading PDF: {result.error_message}")
        return
    
    print(f"📄 PDF: {pdf_path}")
    print(f"📊 Total characters: {len(result.text)}")
    print(f"📄 Total pages: {result.pages}")
    print("\n🔍 Keyword Detection:")
    
    found_keywords = []
    missing_keywords = []
    
    for keyword in expected_keywords:
        if keyword.lower() in result.text.lower():
            found_keywords.append(keyword)
            print(f"  ✅ '{keyword}' - FOUND")
        else:
            missing_keywords.append(keyword)
            print(f"  ❌ '{keyword}' - MISSING")
    
    print(f"\n📈 Summary:")
    print(f"  Found: {len(found_keywords)}/{len(expected_keywords)} keywords")
    print(f"  Success rate: {len(found_keywords)/len(expected_keywords)*100:.1f}%")
    
    if missing_keywords:
        print(f"  Missing: {', '.join(missing_keywords)}")
    
    # Show a sample of the extracted text
    print(f"\n📝 Text sample (first 200 chars):")
    print(f"  {result.text[:200]}...")
    
    return len(found_keywords) == len(expected_keywords)

if __name__ == "__main__":
    # Test files
    original_pdf = Path("../resume.pdf")
    enhanced_pdf = Path("../resume_optimized.pdf")
    test_keywords = ["python", "developer", "software"]
    
    print("🔍 KEYWORD INJECTION TEST\n")
    print("=" * 50)
    
    if original_pdf.exists():
        print("\n1️⃣ ORIGINAL PDF:")
        check_keywords_in_pdf(original_pdf, test_keywords)
    else:
        print("❌ Original PDF not found")
    
    if enhanced_pdf.exists():
        print("\n2️⃣ ENHANCED PDF:")
        success = check_keywords_in_pdf(enhanced_pdf, test_keywords)
        
        if success:
            print("\n🎉 SUCCESS! All keywords were injected!")
        else:
            print("\n⚠️  Some keywords are missing from enhanced PDF")
    else:
        print("❌ Enhanced PDF not found")