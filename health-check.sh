#!/bin/bash

# Health Check Script for LogBERT AI Agents Backend
# This script checks if the backend services are running and accessible

echo "🔍 LogBERT AI Agents Backend Health Check"
echo "========================================"

# Check if backend is accessible
echo "1. Checking backend connectivity..."
BACKEND_URL="http://localhost:8000"

# Test basic connection
if curl -s --connect-timeout 5 "$BACKEND_URL/api/health" > /dev/null 2>&1; then
    echo "✅ Backend is accessible at $BACKEND_URL"
    
    # Test health endpoint
    echo "2. Testing health endpoint..."
    HEALTH_RESPONSE=$(curl -s "$BACKEND_URL/api/health")
    if [ $? -eq 0 ] && [[ "$HEALTH_RESPONSE" != *"Internal Server Error"* ]]; then
        echo "✅ Health endpoint is working"
        echo "   Response: $HEALTH_RESPONSE"
    else
        echo "⚠️  Health endpoint is accessible but returning errors"
        echo "   Response: $HEALTH_RESPONSE"
    fi
    
    # Test agents status endpoint
    echo "3. Testing agents status endpoint..."
    AGENTS_RESPONSE=$(curl -s "$BACKEND_URL/api/agents/status")
    if [ $? -eq 0 ]; then
        echo "✅ Agents status endpoint is accessible"
        echo "   Response: $AGENTS_RESPONSE"
    else
        echo "❌ Agents status endpoint failed"
    fi
    
else
    echo "❌ Backend is NOT accessible at $BACKEND_URL"
    echo ""
    echo "📋 Troubleshooting steps:"
    echo "   1. Check if the backend is running:"
    echo "      python src/main.py"
    echo "   2. Or start with the API server:"
    echo "      python start_api.py"
    echo "   3. Check if port 8000 is already in use:"
    echo "      lsof -i :8000"
    echo "   4. Check backend logs for errors"
fi

echo ""
echo "4. Checking port availability..."
if lsof -i :8000 >/dev/null 2>&1; then
    echo "📍 Port 8000 is in use:"
    lsof -i :8000
else
    echo "⚠️  Port 8000 is not in use - backend may not be running"
fi

echo ""
echo "5. Checking frontend development server..."
if lsof -i :3000 >/dev/null 2>&1; then
    echo "✅ Frontend appears to be running on port 3000"
else
    echo "⚠️  Frontend may not be running on port 3000"
fi

echo ""
echo "🚀 Quick start commands:"
echo "   Backend: cd /Users/mukeshkapoor/projects/logbert_hadoop_rca && python start_api.py"
echo "   Frontend: cd /Users/mukeshkapoor/projects/logbert_hadoop_rca/frontend && npm start"
