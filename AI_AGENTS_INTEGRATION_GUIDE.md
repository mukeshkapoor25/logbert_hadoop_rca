# LogBERT AI Agents - Complete Integration Guide

## 🤖 Overview

This project has been successfully converted from a traditional API interface to a sophisticated **AI Agents-based architecture** for log analysis and root cause analysis using LogBERT models. The system now features:

- **5 Specialized AI Agents** working in coordination
- **Real-time Web Interface** with WebSocket communication
- **Interactive Dashboard** for monitoring agent performance
- **RESTful API** with agent-based endpoints
- **Live Log Analysis** with streaming capabilities

## 🏗️ Architecture

### AI Agents System
```
┌─────────────────┐
│  Coordinator    │ ←── Orchestrates entire pipeline
│     Agent       │
└─────────────────┘
         │
         ▼
┌─────────────────┬─────────────────┐
│   Log Parser    │  Anomaly Det.   │ ←── Parallel processing
│     Agent       │     Agent       │
└─────────────────┴─────────────────┘
         │                 │
         ▼                 ▼
┌─────────────────┬─────────────────┐
│  Root Cause     │  Explanation    │ ←── Analysis & insights
│     Agent       │     Agent       │
└─────────────────┴─────────────────┘
```

### System Components
- **Frontend**: Bootstrap 5 + Vanilla JavaScript
- **Backend**: FastAPI with async/await
- **AI Models**: PyTorch + Transformers (LogBERT)
- **Communication**: WebSocket + REST API
- **UI**: Responsive web interface with real-time updates

## 🚀 Quick Start

### 1. Installation
```bash
# Clone and navigate to project
cd logbert_hadoop_rca

# Install dependencies
pip install -r requirements.txt

# Or use the startup script with auto-install
python start_ai_agents.py --install-deps
```

### 2. Start the Application
```bash
# Development mode (with auto-reload)
python start_ai_agents.py --dev

# Production mode
python start_ai_agents.py --host 0.0.0.0 --port 8000 --workers 4

# Custom configuration
python start_ai_agents.py --host localhost --port 8080 --reload
```

### 3. Access the Interface
- **Main Dashboard**: http://localhost:8000
- **Log Analysis**: http://localhost:8000/analyze
- **Agents Management**: http://localhost:8000/agents
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🎛️ Web Interface Features

### 1. Dashboard (`/`)
- **Real-time Agent Status**: Live monitoring of all 5 AI agents
- **System Metrics**: Total analyses, anomalies detected, system health
- **Quick Actions**: Sample analysis, system metrics, agent management
- **Recent Activity**: Live feed of system activities
- **WebSocket Updates**: Real-time status updates without page refresh

### 2. Log Analysis (`/analyze`)
- **Multiple Input Methods**:
  - File Upload (drag & drop support)
  - Text Paste (direct log entry)
  - Live Stream (WebSocket streaming)
- **Analysis Options**:
  - Log format detection (Hadoop, Apache, Nginx, Custom)
  - Sensitivity levels (Low, Medium, High)
  - Selective analysis types (Anomaly, RCA, Parsing)
- **Real-time Progress**: Step-by-step analysis visualization
- **Interactive Results**: Anomaly details, root causes, explanations
- **Export Functionality**: JSON export of analysis results

### 3. Agents Management (`/agents`)
- **Agent Status Cards**: Health, performance metrics for each agent
- **Agent Controls**: Test, restart, view logs for individual agents
- **Communication Flow**: Visual representation of agent interactions
- **Performance Metrics**: Success rates, task completion, system health
- **Bulk Operations**: Start all agents, refresh all statuses

## 🔧 API Endpoints

### Core Analysis
```http
POST /api/analyze/files     # File-based analysis
POST /api/analyze/text      # Text-based analysis
POST /api/analyze/sample    # Sample analysis
```

### Agent Management
```http
GET  /api/agents/status           # All agent statuses
POST /api/agents/{agent}/test     # Test specific agent
POST /api/agents/{agent}/restart  # Restart agent
GET  /api/agents/{agent}/logs     # Agent logs
POST /api/agents/start-all        # Start all agents
```

### System Monitoring
```http
GET /api/health              # System health check
GET /api/metrics/summary     # System metrics
GET /api/activity/recent     # Recent activities
```

### WebSocket Endpoints
```http
WS /ws/dashboard    # Dashboard real-time updates
WS /ws/agents       # Agent status updates
WS /ws/stream       # Live log streaming
```

## 📊 Agent Specifications

### 1. Coordinator Agent
- **Purpose**: Orchestrates the entire analysis pipeline
- **Responsibilities**: Task distribution, result aggregation, error handling
- **Status Monitoring**: Total executions, success rate

### 2. Anomaly Detection Agent
- **Purpose**: LogBERT-based anomaly detection
- **Model**: Pre-trained BERT for log analysis
- **Metrics**: Anomalies found, model accuracy

### 3. Root Cause Agent
- **Purpose**: Identifies root causes of detected anomalies
- **Analysis**: Pattern matching, correlation analysis
- **Metrics**: Root causes found, resolution rate

### 4. Log Parser Agent
- **Purpose**: Parses and structures raw log data
- **Formats**: Hadoop, Apache, Nginx, custom formats
- **Metrics**: Logs parsed, parse success rate

### 5. Explanation Agent
- **Purpose**: Generates human-readable explanations
- **Output**: Natural language insights and recommendations
- **Metrics**: Explanations generated, clarity score

## 🎨 UI Features

### Real-time Updates
- WebSocket connections for live status updates
- Auto-refreshing agent health indicators
- Live activity feed
- Real-time progress tracking

### Interactive Elements
- Drag & drop file upload
- Click-to-copy results
- Expandable result cards
- Modal dialogs for detailed views

### Responsive Design
- Mobile-friendly interface
- Bootstrap 5 responsive grid
- Touch-friendly controls
- Adaptive layouts

## 🔒 Configuration

### Environment Variables
```bash
LOGBERT_ENV=development          # Environment mode
LOGBERT_LOG_LEVEL=INFO          # Logging level
LOGBERT_MODEL_PATH=/path/models # Model directory
LOGBERT_MAX_FILE_SIZE=100MB     # Upload limit
```

### Agent Configuration
Each agent can be configured via the `src/agents/config/` directory:
- Model parameters
- Performance thresholds
- Timeout settings
- Resource limits

## 🧪 Testing

### Manual Testing
1. **Dashboard**: Visit `/` and verify all agents show status
2. **File Analysis**: Upload a log file in `/analyze`
3. **Text Analysis**: Paste log text and run analysis
4. **Agent Management**: Test individual agents in `/agents`

### API Testing
```bash
# Health check
curl http://localhost:8000/health

# Agent status
curl http://localhost:8000/api/agents/status

# Sample analysis
curl -X POST http://localhost:8000/api/analyze/sample \
  -H "Content-Type: application/json" \
  -d '{"sample_type": "hadoop_error_logs"}'
```

## 🚨 Troubleshooting

### Common Issues

1. **Agents Not Starting**
   - Check Python path configuration
   - Verify all dependencies installed
   - Check log files for errors

2. **WebSocket Connection Failed**
   - Verify server is running
   - Check firewall settings
   - Ensure port is accessible

3. **File Upload Errors**
   - Check file size limits
   - Verify file format support
   - Check disk space

4. **Model Loading Issues**
   - Verify PyTorch installation
   - Check model file paths
   - Ensure sufficient memory

### Debug Mode
```bash
# Start with debug logging
LOGBERT_LOG_LEVEL=DEBUG python start_ai_agents.py --dev
```

## 📈 Performance

### System Requirements
- **CPU**: 4+ cores recommended
- **Memory**: 8GB+ RAM (for LogBERT models)
- **Storage**: 10GB+ free space
- **Python**: 3.8+

### Optimization Tips
- Use multiple workers for production
- Enable GPU acceleration for models
- Configure appropriate timeouts
- Monitor memory usage

## 🔄 Updates & Maintenance

### Regular Tasks
- Monitor agent health via dashboard
- Review system logs periodically
- Update models as needed
- Check for dependency updates

### Scaling
- Increase worker processes for higher load
- Configure load balancing if needed
- Monitor resource usage
- Optimize model inference

## 📝 Development

### Adding New Agents
1. Create agent class inheriting from `BaseAgent`
2. Implement required methods
3. Add to coordinator workflow
4. Update UI components

### Extending API
1. Add new endpoints in `src/api/routes.py`
2. Update agent interfaces
3. Add corresponding UI elements
4. Test integration

## 📞 Support

For issues, questions, or contributions:
- Check the logs first: `/api/agents/{agent}/logs`
- Review the dashboard for system status
- Test individual agents: `/agents`
- Check API documentation: `/docs`

## ✅ Success Indicators

The system is working correctly when:
- ✅ All 5 agents show "Active" status on dashboard
- ✅ File uploads process successfully
- ✅ WebSocket connections establish (real-time updates work)
- ✅ Sample analysis completes without errors
- ✅ Agent tests pass when triggered manually

## 🎯 Next Steps

The AI agents system is now fully operational! You can:
1. Upload your Hadoop logs for analysis
2. Monitor agent performance in real-time
3. Customize agent configurations as needed
4. Integrate with external monitoring systems
5. Scale the system for production workloads

---

**🚀 Your LogBERT AI Agents system is ready for log analysis!**
