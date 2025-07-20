#!/usr/bin/env python3
"""
API Test Script

Simple test to verify the LogBERT API can be imported and basic functionality works.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test basic imports."""
    print("🧪 Testing imports...")
    
    try:
        from src.utils.config import get_settings
        print("✅ Config module imported successfully")
        
        from src.models.schemas import LogAnalysisRequest
        print("✅ Schemas imported successfully")
        
        from src.utils.logging import setup_logging
        print("✅ Logging module imported successfully")
        
        # Test configuration
        settings = get_settings()
        print(f"✅ Configuration loaded - Environment: {settings.ENVIRONMENT}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_api_creation():
    """Test FastAPI app creation."""
    print("\n🚀 Testing API creation...")
    
    try:
        from fastapi import FastAPI
        from src.api.main import app
        
        if isinstance(app, FastAPI):
            print("✅ FastAPI app created successfully")
            print(f"   Title: {app.title}")
            print(f"   Version: {app.version}")
            return True
        else:
            print("❌ App is not a FastAPI instance")
            return False
            
    except Exception as e:
        print(f"❌ API creation test failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without heavy dependencies."""
    print("\n🔧 Testing basic functionality...")
    
    try:
        # Test configuration
        from src.utils.config import get_settings
        settings = get_settings()
        
        # Test logging setup
        from src.utils.logging import setup_logging
        setup_logging()
        
        # Test schema validation
        from src.models.schemas import LogAnalysisRequest
        
        request = LogAnalysisRequest(
            log_text="2023-07-19 10:00:00 INFO Test log entry",
            threshold=0.7
        )
        
        print("✅ Basic functionality test passed")
        print(f"   Sample request created with {len(request.log_text)} characters")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🎯 LogBERT Hadoop RCA - API Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_api_creation,
        test_basic_functionality,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("📊 Test Results:")
    print(f"   Passed: {passed}/{total}")
    print(f"   Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All tests passed! The API is ready for development.")
        print("💡 Next steps:")
        print("   1. Install ML dependencies (torch, transformers) for full functionality")
        print("   2. Run './start_api.py' to start the development server")
        print("   3. Visit http://localhost:8000/docs for API documentation")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
