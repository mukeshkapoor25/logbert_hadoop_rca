"""
Simple test to identify the import issue
"""

print("Starting main.py execution...")

try:
    import uvicorn
    print("✓ uvicorn imported")
except Exception as e:
    print(f"❌ uvicorn import failed: {e}")

try:
    from contextlib import asynccontextmanager
    print("✓ asynccontextmanager imported")
except Exception as e:
    print(f"❌ asynccontextmanager import failed: {e}")

try:
    from fastapi import FastAPI
    print("✓ FastAPI imported")
except Exception as e:
    print(f"❌ FastAPI import failed: {e}")

try:
    from fastapi.middleware.cors import CORSMiddleware
    print("✓ CORSMiddleware imported")
except Exception as e:
    print(f"❌ CORSMiddleware import failed: {e}")

try:
    import logging
    print("✓ logging imported")
except Exception as e:
    print(f"❌ logging import failed: {e}")

try:
    import socketio
    print("✓ socketio imported")
except Exception as e:
    print(f"❌ socketio import failed: {e}")

try:
    from src.api.routes import router as api_router
    print("✓ api_router imported")
except Exception as e:
    print(f"❌ api_router import failed: {e}")

try:
    from src.utils.logging import setup_logging
    print("✓ setup_logging imported")
except Exception as e:
    print(f"❌ setup_logging import failed: {e}")

print("Creating simple app...")
app = FastAPI(title="Test App")

print("App created successfully!")
print(f"Module name: {__name__}")
