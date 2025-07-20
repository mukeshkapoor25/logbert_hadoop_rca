#!/usr/bin/env python3
"""
LogBERT AI Agents - System Integration Test
Tests the complete AI agents system including UI and API endpoints.
"""

import asyncio
import sys
import os
from pathlib import Path
import httpx
import json
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

class AIAgentsSystemTest:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = None
        self.test_results = []
        
    async def setup(self):
        """Setup test environment."""
        self.client = httpx.AsyncClient(timeout=30.0)
        print("🧪 LogBERT AI Agents - System Integration Test")
        print("=" * 50)
        
    async def teardown(self):
        """Cleanup test environment."""
        if self.client:
            await self.client.aclose()
    
    async def test_health_check(self):
        """Test system health endpoint."""
        print("1️⃣  Testing system health...")
        try:
            response = await self.client.get(f"{self.base_url}/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            print("   ✅ Health check passed")
            return True
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            return False
    
    async def test_ui_endpoints(self):
        """Test UI page endpoints."""
        print("2️⃣  Testing UI endpoints...")
        ui_pages = [
            "/",
            "/analyze", 
            "/agents",
            "/results"
        ]
        
        success_count = 0
        for page in ui_pages:
            try:
                response = await self.client.get(f"{self.base_url}{page}")
                if response.status_code == 200:
                    print(f"   ✅ {page} - OK")
                    success_count += 1
                else:
                    print(f"   ❌ {page} - Status {response.status_code}")
            except Exception as e:
                print(f"   ❌ {page} - Error: {e}")
        
        return success_count == len(ui_pages)
    
    async def test_agents_status(self):
        """Test agents status endpoint."""
        print("3️⃣  Testing agents status...")
        try:
            response = await self.client.get(f"{self.base_url}/api/agents/status")
            assert response.status_code == 200
            data = response.json()
            
            expected_agents = [
                "coordinator",
                "anomaly_detection", 
                "root_cause",
                "log_parser",
                "explanation"
            ]
            
            for agent in expected_agents:
                if agent in data:
                    status = data[agent].get("status", "unknown")
                    print(f"   📊 {agent}: {status}")
                else:
                    print(f"   ⚠️  {agent}: not found")
            
            print("   ✅ Agents status check passed")
            return True
            
        except Exception as e:
            print(f"   ❌ Agents status failed: {e}")
            return False
    
    async def test_sample_analysis(self):
        """Test sample analysis endpoint."""
        print("4️⃣  Testing sample analysis...")
        try:
            payload = {
                "sample_type": "hadoop_error_logs",
                "options": {
                    "anomaly_detection": True,
                    "root_cause_analysis": True,
                    "log_parsing": True
                }
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/analyze/sample",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   📈 Analysis completed")
                print(f"   📊 Status: {data.get('status', 'unknown')}")
                print(f"   🔍 Anomalies: {len(data.get('anomalies', []))}")
                print(f"   🎯 Root causes: {len(data.get('root_causes', []))}")
                print("   ✅ Sample analysis passed")
                return True
            else:
                print(f"   ❌ Sample analysis failed: Status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Sample analysis error: {e}")
            return False
    
    async def test_text_analysis(self):
        """Test text-based analysis."""
        print("5️⃣  Testing text analysis...")
        try:
            sample_logs = """
2024-01-15 10:30:42,123 INFO [main] org.apache.hadoop.hdfs.server.datanode.DataNode: Starting DataNode
2024-01-15 10:30:43,456 ERROR [main] org.apache.hadoop.hdfs.server.datanode.DataNode: Failed to connect to NameNode
2024-01-15 10:30:44,789 WARN [main] org.apache.hadoop.hdfs.server.datanode.DataNode: Retrying connection to NameNode
2024-01-15 10:30:45,012 ERROR [main] org.apache.hadoop.hdfs.server.datanode.DataNode: Connection timeout after 3 attempts
            """.strip()
            
            payload = {
                "log_data": sample_logs,
                "log_format": "hadoop",
                "sensitivity": "medium",
                "options": {
                    "anomaly_detection": True,
                    "root_cause_analysis": True,
                    "log_parsing": True
                }
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/analyze/text",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   📝 Text analysis completed")
                print(f"   📊 Status: {data.get('status', 'unknown')}")
                print("   ✅ Text analysis passed")
                return True
            else:
                print(f"   ❌ Text analysis failed: Status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Text analysis error: {e}")
            return False
    
    async def test_agent_operations(self):
        """Test individual agent operations."""
        print("6️⃣  Testing agent operations...")
        
        # Test one agent (coordinator) as representative
        agent_name = "coordinator"
        success_count = 0
        
        # Test agent test endpoint
        try:
            response = await self.client.post(f"{self.base_url}/api/agents/{agent_name}/test")
            if response.status_code == 200:
                print(f"   ✅ {agent_name} test - OK")
                success_count += 1
            else:
                print(f"   ⚠️  {agent_name} test - Status {response.status_code}")
        except Exception as e:
            print(f"   ❌ {agent_name} test error: {e}")
        
        # Test agent logs endpoint
        try:
            response = await self.client.get(f"{self.base_url}/api/agents/{agent_name}/logs")
            if response.status_code == 200:
                print(f"   ✅ {agent_name} logs - OK")
                success_count += 1
            else:
                print(f"   ⚠️  {agent_name} logs - Status {response.status_code}")
        except Exception as e:
            print(f"   ❌ {agent_name} logs error: {e}")
        
        return success_count >= 1
    
    async def test_api_documentation(self):
        """Test API documentation endpoint."""
        print("7️⃣  Testing API documentation...")
        try:
            response = await self.client.get(f"{self.base_url}/docs")
            if response.status_code == 200:
                print("   ✅ API documentation accessible")
                return True
            else:
                print(f"   ❌ API docs failed: Status {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ API docs error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all system tests."""
        await self.setup()
        
        tests = [
            ("Health Check", self.test_health_check),
            ("UI Endpoints", self.test_ui_endpoints),
            ("Agents Status", self.test_agents_status),
            ("Sample Analysis", self.test_sample_analysis),
            ("Text Analysis", self.test_text_analysis),
            ("Agent Operations", self.test_agent_operations),
            ("API Documentation", self.test_api_documentation),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                if result:
                    passed += 1
                    self.test_results.append((test_name, "PASS"))
                else:
                    self.test_results.append((test_name, "FAIL"))
            except Exception as e:
                print(f"   ❌ {test_name} - Unexpected error: {e}")
                self.test_results.append((test_name, "ERROR"))
        
        await self.teardown()
        
        # Print summary
        print("\n" + "=" * 50)
        print("🎯 TEST SUMMARY")
        print("=" * 50)
        
        for test_name, status in self.test_results:
            icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            print(f"{icon} {test_name}: {status}")
        
        print(f"\n📊 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Your AI Agents system is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Please check the system configuration.")
            return False

async def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LogBERT AI Agents System Test")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL to test")
    parser.add_argument("--wait", type=int, default=5, help="Seconds to wait before starting tests")
    
    args = parser.parse_args()
    
    print(f"🔍 Testing system at: {args.url}")
    
    if args.wait > 0:
        print(f"⏳ Waiting {args.wait} seconds for system to start...")
        await asyncio.sleep(args.wait)
    
    tester = AIAgentsSystemTest(args.url)
    success = await tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
