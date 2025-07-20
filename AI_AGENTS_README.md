# AI Agent-Based LogBERT Hadoop RCA API

## Overview

This project has been converted from a traditional API architecture to an **AI Agent-based system** that provides intelligent, autonomous log analysis capabilities. The new architecture uses specialized AI agents that work together to deliver comprehensive log analysis, anomaly detection, and root cause analysis.

## 🤖 AI Agent Architecture

### Core Agents

The system is built around five specialized AI agents:

1. **🎯 Coordinator Agent** (`CoordinatorAgent`)
   - Orchestrates the entire analysis pipeline
   - Manages agent communication and workflow
   - Provides unified error handling and result aggregation
   - Handles retry logic and timeout management

2. **📝 Log Parser Agent** (`LogParserAgent`)
   - Parses raw log text into structured format
   - Supports multiple log formats (Hadoop, HDFS, YARN, Generic)
   - Extracts timestamps, components, log levels, and metadata
   - Performs intelligent format detection

3. **🔍 Anomaly Detection Agent** (`AnomalyDetectionAgent`)
   - Detects anomalies using LogBERT deep learning models
   - Provides confidence scores and severity classification
   - Handles model loading and inference
   - Calculates anomaly scores and patterns

4. **🔬 Root Cause Agent** (`RootCauseAgent`)
   - Analyzes anomalies for potential root causes
   - Uses pattern matching and historical data
   - Groups related anomalies for better analysis
   - Provides evidence and recommendations

5. **💬 Explanation Agent** (`ExplanationAgent`)
   - Generates human-readable explanations
   - Supports multiple explanation styles (technical, management, brief)
   - Creates actionable recommendations
   - Provides system health insights

### Agent Communication

Agents communicate through a message-passing system with:
- Asynchronous execution
- Error handling and recovery
- Retry mechanisms
- Performance monitoring
- Status tracking

## 🚀 Key Features

### Intelligent Orchestration
- **Pipeline Coordination**: Automatic workflow management
- **Parallel Processing**: Concurrent agent execution where possible
- **Error Recovery**: Automatic retry with exponential backoff
- **Resource Management**: Efficient agent lifecycle management

### Advanced Analytics
- **Multi-Model Support**: Different models for different log types
- **Context-Aware Analysis**: Considers log context for better accuracy
- **Confidence Scoring**: Provides confidence levels for all predictions
- **Historical Learning**: Uses past patterns for improved analysis

### Flexible Explanations
- **Multiple Styles**: Technical, management, and brief explanations
- **Actionable Insights**: Specific recommendations for remediation
- **System Health Scoring**: Overall system health assessment
- **Trend Analysis**: Identifies patterns and trends in log data

## 📡 API Endpoints

### Core Analysis Endpoints

#### Complete Analysis
```http
POST /api/analyze
```
Orchestrates all agents for complete log analysis including parsing, anomaly detection, RCA, and explanations.

#### Anomaly Detection Only
```http
POST /api/detect-anomalies
```
Uses only the anomaly detection agent for fast anomaly identification.

#### Root Cause Analysis
```http
POST /api/rca
```
Performs RCA on provided anomalies using the root cause agent.

### Specialized Agent Endpoints

#### Log Parsing
```http
POST /api/parse
```
Parse raw logs into structured format using the parser agent.

#### Generate Explanations
```http
POST /api/explain
```
Generate human-readable explanations using the explanation agent.

### Agent Management

#### Agent Status
```http
GET /api/agents/status
```
Get status of all AI agents in the system.

#### Configure Agents
```http
POST /api/agents/configure
```
Update agent configurations dynamically.

#### Health Check
```http
GET /api/health
```
Check overall system and agent health.

## 💡 Usage Examples

### Python Client Example

```python
import asyncio
from examples.ai_agent_client_demo import LogBERTAIAgentClient

async def analyze_logs():
    async with LogBERTAIAgentClient() as client:
        # Complete analysis with all agents
        result = await client.analyze_logs(
            log_text="2023-07-19 10:00:01 ERROR Connection timeout...",
            threshold=0.6,
            include_rca=True
        )
        
        print(f"Analysis ID: {result['analysis_id']}")
        print(f"Anomalies: {result['anomaly_detection']['total_anomalies']}")
        print(f"Root Causes: {result['root_cause_analysis']['total_root_causes']}")

asyncio.run(analyze_logs())
```

### cURL Example

```bash
# Complete analysis
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "log_text": "2023-07-19 10:00:01 ERROR Connection timeout to namenode",
    "threshold": 0.6,
    "model_name": "logbert_hadoop",
    "include_rca": true
  }'

# Check agent status
curl -X GET "http://localhost:8000/api/agents/status"
```

## 🔧 Configuration

### Agent Configuration

Agents can be configured through the API or configuration files:

```json
{
  "coordinator": {
    "enable_parallel_processing": true,
    "max_retries": 3,
    "timeout_seconds": 300
  },
  "anomaly_detection": {
    "threshold": 0.5,
    "model_name": "logbert_hadoop"
  },
  "root_cause_analysis": {
    "context_window": 10,
    "min_confidence": 0.6
  },
  "explanation": {
    "explanation_style": "technical",
    "language_model": "mistral-7b"
  }
}
```

## 🎯 Benefits of AI Agent Architecture

### 1. **Modularity**
- Each agent has a single responsibility
- Easy to update or replace individual agents
- Independent scaling of different capabilities

### 2. **Scalability**
- Agents can run in parallel
- Horizontal scaling of agent instances
- Load balancing across agent pools

### 3. **Reliability**
- Fault isolation between agents
- Automatic retry and recovery
- Graceful degradation on agent failure

### 4. **Extensibility**
- Easy to add new agent types
- Plugin architecture for new capabilities
- Custom agent development framework

### 5. **Observability**
- Detailed agent performance metrics
- Agent-level logging and monitoring
- Pipeline execution tracking

## 🚦 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the API Server
```bash
python src/api/main.py
```

### 3. Run the Demo
```bash
python examples/ai_agent_client_demo.py
```

### 4. Explore the API
Visit `http://localhost:8000/docs` for interactive API documentation.

## 🔍 Monitoring and Debugging

### Agent Status Monitoring
```python
# Check agent health
status = await client.get_agent_status()
print(f"Coordinator: {status['coordinator_status']}")
print(f"Sub-agents: {status['sub_agents']}")
```

### Performance Metrics
Each API response includes detailed timing and performance metrics:
- Agent execution times
- Pipeline step durations
- Resource utilization
- Error rates and recovery statistics

## 🛠️ Development

### Adding New Agents

1. Create agent class inheriting from `BaseAgent`
2. Implement the `process()` method
3. Add agent to coordinator configuration
4. Update API endpoints as needed

### Custom Agent Example
```python
class CustomAnalysisAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(
            capabilities=[AgentCapability.CUSTOM_ANALYSIS],
            **kwargs
        )
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        # Custom processing logic
        result = await self.custom_analysis(input_data)
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status=AgentStatus.COMPLETED,
            result=result,
            processing_time_ms=self.get_processing_time()
        )
```

## 📈 Performance Characteristics

- **Latency**: Sub-second response for small log files
- **Throughput**: Handles concurrent requests through agent parallelization
- **Scalability**: Linear scaling with agent instances
- **Reliability**: 99.9% uptime with proper agent health monitoring

## 🔮 Future Enhancements

- **Distributed Agents**: Agents running across multiple nodes
- **Machine Learning Pipeline**: Continuous learning from analysis results
- **Real-time Streaming**: Live log analysis with streaming agents
- **Custom Agent Marketplace**: Community-contributed specialized agents

## 📚 Documentation

- **API Reference**: `/docs` endpoint for OpenAPI specification
- **Agent Documentation**: Individual agent capabilities and configurations
- **Examples**: Complete usage examples in `/examples` directory
- **Performance Guide**: Optimization tips and best practices
