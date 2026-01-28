"""
Test script to verify OpenRouter integration
Run after setting up .env with OPENROUTER_API_KEY
"""
import os
import sys

def test_imports():
    """Test that all modules can be imported."""
    print("✓ Testing imports...")
    try:
        from app.services.openrouter_client import OpenRouterClient
        from app.services.structurer import TextStructurer
        from app.models.po_schemas import OCRPOResult
        print("  ✓ All imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_environment():
    """Test environment variables."""
    print("\n✓ Testing environment...")
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key and api_key != "your_api_key_here":
        print(f"  ✓ OPENROUTER_API_KEY is set (starts with: {api_key[:10]}...)")
        return True
    else:
        print("  ⚠ OPENROUTER_API_KEY not set or using default value")
        print("    Please edit .env and add your actual API key")
        return False


def test_openrouter_client():
    """Test OpenRouter client initialization."""
    print("\n✓ Testing OpenRouter client...")
    try:
        from app.services.openrouter_client import OpenRouterClient
        
        # Test without API key (should raise error)
        try:
            client = OpenRouterClient(api_key=None)
            os.environ.pop("OPENROUTER_API_KEY", None)
            print("  ✗ Should have raised error for missing API key")
            return False
        except ValueError as e:
            print(f"  ✓ Correctly raises error for missing API key")
        
        # Test with API key from env
        from dotenv import load_dotenv
        load_dotenv()
        
        if os.getenv("OPENROUTER_API_KEY") == "your_api_key_here":
            print("  ⚠ Using placeholder API key, skipping actual client test")
            return True
            
        client = OpenRouterClient()
        print(f"  ✓ Client initialized with model: {client.default_model}")
        return True
        
    except Exception as e:
        print(f"  ✗ Client test failed: {e}")
        return False


def test_structurer():
    """Test TextStructurer prompt building."""
    print("\n✓ Testing TextStructurer...")
    try:
        from app.services.structurer import TextStructurer
        
        structurer = TextStructurer()
        
        # Test prompt building
        test_text = "PO-001\nบริษัท ABC จำกัด\n12 x 100 x 2000 mm"
        messages = structurer.build_prompt(test_text)
        
        assert len(messages) == 2, "Should have system and user messages"
        assert messages[0]["role"] == "system", "First message should be system"
        assert messages[1]["role"] == "user", "Second message should be user"
        assert test_text in messages[1]["content"], "User message should contain input text"
        
        print("  ✓ Prompt building works correctly")
        
        # Test JSON parsing
        valid_json = '{"header": {"poNumber": "PO-001", "customer": {"name": "ABC"}}, "items": [], "meta": {"confidence": 0.9}}'
        result = structurer.parse_and_validate(valid_json, include_raw_text=False)
        
        assert result["header"]["poNumber"] == "PO-001", "Should parse header correctly"
        assert result["meta"]["confidence"] == 0.9, "Should parse meta correctly"
        
        print("  ✓ JSON parsing and validation works correctly")
        return True
        
    except Exception as e:
        print(f"  ✗ Structurer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pydantic_models():
    """Test Pydantic models."""
    print("\n✓ Testing Pydantic models...")
    try:
        from app.models.po_schemas import OCRPOResult, POHeader, POItem, POMeta, CustomerInfo
        
        # Test creating a valid model
        data = {
            "header": {
                "poNumber": "PO-001",
                "poDate": "2026-01-27",
                "customer": {
                    "name": "ABC Company",
                    "tel": "02-xxx-xxxx"
                }
            },
            "items": [
                {
                    "codeSteel": "SS400",
                    "thickness": 12.5,
                    "width": 100,
                    "length": 2000,
                    "quantity": 50,
                    "shape": "square",
                    "confidence": 0.95
                }
            ],
            "meta": {
                "confidence": 0.92,
                "warnings": ["Sample warning"],
                "rawText": "Original text..."
            }
        }
        
        result = OCRPOResult(**data)
        assert result.header.poNumber == "PO-001"
        assert len(result.items) == 1
        assert result.items[0].thickness == 12.5
        assert result.meta.confidence == 0.92
        
        print("  ✓ All Pydantic models validate correctly")
        return True
        
    except Exception as e:
        print(f"  ✗ Pydantic model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Thai PDF OCR API - OpenRouter Integration Tests")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Environment", test_environment()))
    results.append(("OpenRouter Client", test_openrouter_client()))
    results.append(("Text Structurer", test_structurer()))
    results.append(("Pydantic Models", test_pydantic_models()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:.<40} {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        print("\nNext steps:")
        print("1. Make sure .env has your OPENROUTER_API_KEY")
        print("2. Run: uvicorn app.main:app --reload")
        print("3. Visit: http://localhost:8000/docs")
        print("4. Test the /pdf/to-structured-json endpoint")
        return 0
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
