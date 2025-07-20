#!/usr/bin/env python3
"""
Development Server Startup Script

This script starts the LogBERT Hadoop RCA API in development mode.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.main import app
    import uvicorn
    
    if __name__ == "__main__":
        print("🚀 Starting LogBERT Hadoop RCA API in development mode...")
        print("📚 API Documentation will be available at: http://localhost:8000/docs")
        print("🔍 Health check available at: http://localhost:8000/api/health")
        print("📊 Root endpoint available at: http://localhost:8000/")
        print("ℹ️  Socket.IO requests handled with info responses")
        print("")
        print("🛠️  Development Features:")
        print("   - Auto-reload on code changes")
        print("   - Detailed logging")
        print("   - Interactive API documentation")
        print("   - Socket.IO request handling")
        print("")
        print("⚡ Starting server...")
        
        # Start the server
        uvicorn.run(
            "src.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you have activated the virtual environment and installed dependencies:")
    print("   source venv/bin/activate")
    print("   pip install -r requirements.txt")
    print("")
    print("🔧 If you're missing FastAPI, install it with:")
    print("   pip install fastapi uvicorn")
    sys.exit(1)
except KeyboardInterrupt:
    print("\n🛑 Server stopped by user")
    print("👋 Thanks for using LogBERT Hadoop RCA API!")
    sys.exit(0)
except Exception as e:
    print(f"❌ Error starting server: {e}")
    print("💡 Check the logs above for more details")
    sys.exit(1)
