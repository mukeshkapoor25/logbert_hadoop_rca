#!/usr/bin/env python3
"""
LogBERT AI Agents - Startup Script
This script starts the FastAPI application with AI agents and UI integration.
"""

import sys
import os
import subprocess
import argparse
import socket
from pathlib import Path

def check_requirements():
    """Check if all required packages are installed."""
    try:
        import uvicorn
        import fastapi
        import torch
        import transformers
        print("✓ All required packages are available")
        return True
    except ImportError as e:
        print(f"✗ Missing required package: {e}")
        print("  Run with --install-deps to install missing packages")
        return False

def install_requirements():
    """Install required packages."""
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def check_port_available(host, port):
    """Check if a port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            return True
    except OSError:
        return False

def setup_environment():
    """Set up the environment for the application."""
    # Add project root to Python path
    project_root = Path(__file__).parent.absolute()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Set environment variables
    os.environ.setdefault("LOGBERT_ENV", "development")
    os.environ.setdefault("LOGBERT_LOG_LEVEL", "INFO")
    os.environ.setdefault("PYTHONPATH", str(project_root))
    
    print("✓ Environment configured")
    print(f"   - Project root: {project_root}")
    print(f"   - Python path includes project root")

def start_application(host="0.0.0.0", port=8000, reload=False, workers=1):
    """Start the FastAPI application."""
    try:
        import uvicorn
        
        # Check if port is available
        if not check_port_available(host, port):
            print(f"❌ Port {port} is already in use!")
            print(f"   Try a different port with --port <number>")
            print(f"   Or stop the existing service running on port {port}")
            return
        
        print(f"🚀 Starting LogBERT AI Agents application...")
        print(f"   - Host: {host}")
        print(f"   - Port: {port}")
        print(f"   - Workers: {workers}")
        print(f"   - Reload: {reload}")
        print(f"   - UI: http://{host}:{port}")
        print(f"   - API Docs: http://{host}:{port}/docs")
        
        # Set PYTHONPATH to include the project root
        project_root = str(Path(__file__).parent.absolute())
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        uvicorn.run(
            "src.main:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="LogBERT AI Agents Startup Script",
        epilog="""
Examples:
  python start_ai_agents.py                     # Start on default port 8000
  python start_ai_agents.py --dev               # Start in development mode with auto-reload
  python start_ai_agents.py --port 8080         # Start on custom port
  python start_ai_agents.py --install-deps      # Install dependencies and start
  python start_ai_agents.py --workers 4         # Start with 4 workers (production)
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--install-deps", action="store_true", help="Install dependencies before starting")
    parser.add_argument("--dev", action="store_true", help="Development mode (reload + single worker)")
    
    args = parser.parse_args()
    
    print("🤖 LogBERT AI Agents - Starting Application")
    print("=" * 50)
    
    # Install dependencies if requested
    if args.install_deps:
        if not check_requirements():
            install_requirements()
    
    # Check requirements (but don't fail if missing, just warn)
    check_requirements()
    
    # Setup environment
    setup_environment()
    
    # Development mode shortcuts
    if args.dev:
        args.reload = True
        args.workers = 1
        print("🔧 Development mode enabled")
    
    # Start the application
    start_application(
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers
    )

if __name__ == "__main__":
    main()
