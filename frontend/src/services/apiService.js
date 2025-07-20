import axios from 'axios';
import io from 'socket.io-client';

// Create axios instances for different services
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const fileUploadClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 120000, // Longer timeout for file uploads
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

// Socket.IO client for real-time communication
let socket = null;

export const initializeSocket = () => {
  if (!socket) {
    socket = io(process.env.REACT_APP_API_URL || 'http://localhost:8000', {
      transports: ['websocket', 'polling'],
      upgrade: true,
      rememberUpgrade: true
    });
  }
  return socket;
};

export const getSocket = () => socket;

// Request interceptors
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptors
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const apiService = {
  // Health check
  healthCheck: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },

  // Root endpoint info
  getRootInfo: async () => {
    const response = await apiClient.get('/');
    return response.data;
  },

  // AI Agents Management
  getAgentsStatus: async () => {
    const response = await apiClient.get('/agents/status');
    return response.data;
  },

  testAgent: async (agentName) => {
    const response = await apiClient.post(`/agents/${agentName}/test`);
    return response.data;
  },

  restartAgent: async (agentName) => {
    const response = await apiClient.post(`/agents/${agentName}/restart`);
    return response.data;
  },

  getAgentLogs: async (agentName) => {
    const response = await apiClient.get(`/agents/${agentName}/logs`);
    return response.data;
  },

  startAllAgents: async () => {
    const response = await apiClient.post('/agents/start-all');
    return response.data;
  },

  // Analysis endpoints (agent-based)
  analyzeLogFile: async (file, options = {}) => {
    const formData = new FormData();
    formData.append('files', file);
    
    // Add options to form data if needed
    Object.keys(options).forEach(key => {
      formData.append(key, options[key]);
    });

    const response = await fileUploadClient.post('/batch-analyze', formData);
    return response.data;
  },

  analyzeLogText: async (logText, options = {}) => {
    const response = await apiClient.post('/analyze', {
      log_text: logText,
      ...options
    });
    return response.data;
  },

  analyzeSample: async (sampleType = 'hadoop_error_logs') => {
    const response = await apiClient.post('/analyze/sample', {
      sample_type: sampleType
    });
    return response.data;
  },

  // System monitoring
  getMetricsSummary: async () => {
    const response = await apiClient.get('/metrics/summary');
    return response.data;
  },

  getRecentActivity: async () => {
    const response = await apiClient.get('/activity/recent');
    return response.data;
  },

  // WebSocket real-time updates
  subscribeToDashboard: (callback) => {
    const socket = getSocket();
    if (socket) {
      socket.on('dashboard_update', callback);
      socket.emit('join_room', 'dashboard');
    }
  },

  subscribeToAgents: (callback) => {
    const socket = getSocket();
    if (socket) {
      socket.on('agent_status_update', callback);
      socket.emit('join_room', 'agents');
    }
  },

  subscribeToAnalysis: (callback) => {
    const socket = getSocket();
    if (socket) {
      socket.on('analysis_progress', callback);
      socket.on('analysis_complete', callback);
      socket.emit('join_room', 'analysis');
    }
  },

  unsubscribeFromRoom: (room) => {
    const socket = getSocket();
    if (socket) {
      socket.emit('leave_room', room);
    }
  },

  // Agent-specific operations (using generic agent endpoints)
  coordinatorAgent: {
    getStatus: () => apiClient.get('/agents/status').then(r => r.data),
    executeWorkflow: (data) => apiClient.post('/analyze', data).then(r => r.data),
  },

  anomalyAgent: {
    getStatus: () => apiClient.get('/agents/status').then(r => r.data),
    detectAnomalies: (data) => apiClient.post('/analyze', data).then(r => r.data),
  },

  rootCauseAgent: {
    getStatus: () => apiClient.get('/agents/status').then(r => r.data),
    analyzeRootCause: (data) => apiClient.post('/analyze', data).then(r => r.data),
  },

  logParserAgent: {
    getStatus: () => apiClient.get('/agents/status').then(r => r.data),
    parseLogs: (data) => apiClient.post('/analyze', data).then(r => r.data),
  },

  explanationAgent: {
    getStatus: () => apiClient.get('/agents/status').then(r => r.data),
    generateExplanation: (data) => apiClient.post('/analyze', data).then(r => r.data),
  },

  // Streaming analysis
  startStreamAnalysis: (onProgress, onComplete, onError) => {
    const socket = getSocket();
    if (socket) {
      socket.on('stream_progress', onProgress);
      socket.on('stream_complete', onComplete);
      socket.on('stream_error', onError);
      socket.emit('start_stream_analysis');
    }
  },

  stopStreamAnalysis: () => {
    const socket = getSocket();
    if (socket) {
      socket.emit('stop_stream_analysis');
    }
  },

  // System health monitoring
  getSystemHealth: () => apiClient.get('/health').then(r => r.data),
  
  // File upload for log analysis (uses batch-analyze endpoint)
  uploadLogFile: (file) => {
    const formData = new FormData();
    formData.append('files', file);
    return fileUploadClient.post('/batch-analyze', formData).then(r => r.data);
  },

  // Log analysis
  analyzeLogContent: (content) => apiClient.post('/analyze', { log_text: content }).then(r => r.data)
};

export default apiService;
