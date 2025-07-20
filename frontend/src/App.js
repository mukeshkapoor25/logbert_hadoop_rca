import React, { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Container } from 'react-bootstrap';

// Components
import Navigation from './components/Navigation';
import Dashboard from './components/Dashboard';
import LogAnalysis from './components/LogAnalysis';
import AgentsManagement from './components/AgentsManagement';
import RealTimeStream from './components/RealTimeStream';
import SystemHealth from './components/SystemHealth';

// Services
import { apiService, initializeSocket } from './services/apiService';

function App() {
  const [apiHealth, setApiHealth] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [agentsStatus, setAgentsStatus] = useState({});
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    // Initialize socket connection
    const socketInstance = initializeSocket();
    setSocket(socketInstance);

    // Set up socket event listeners
    socketInstance.on('connect', () => {
      console.log('Connected to server');
      setIsConnected(true);
    });

    socketInstance.on('disconnect', () => {
      console.log('Disconnected from server');
      setIsConnected(false);
    });

    // Subscribe to real-time updates
    apiService.subscribeToDashboard((data) => {
      console.log('Dashboard update:', data);
    });

    apiService.subscribeToAgents((data) => {
      console.log('Agents update:', data);
      setAgentsStatus(data);
    });

    // Initial data fetch
    checkApiHealth();
    fetchAgentsStatus();

    // Set up periodic checks
    const healthInterval = setInterval(checkApiHealth, 30000);
    const agentsInterval = setInterval(fetchAgentsStatus, 10000);

    return () => {
      clearInterval(healthInterval);
      clearInterval(agentsInterval);
      if (socketInstance) {
        socketInstance.disconnect();
      }
    };
  }, []);

  const checkApiHealth = async () => {
    try {
      const health = await apiService.healthCheck();
      setApiHealth(health);
      setIsConnected(true);
    } catch (error) {
      console.error('API health check failed:', error);
      setIsConnected(false);
      setApiHealth(null);
    }
  };

  const fetchAgentsStatus = async () => {
    try {
      const status = await apiService.getAgentsStatus();
      setAgentsStatus(status);
    } catch (error) {
      console.error('Failed to fetch agents status:', error);
    }
  };

  return (
    <div className="App">
      <Navigation isConnected={isConnected} agentsStatus={agentsStatus} />
      <Container fluid className="py-4">
        <Routes>
          <Route 
            path="/" 
            element={
              <Dashboard 
                apiHealth={apiHealth} 
                isConnected={isConnected}
                agentsStatus={agentsStatus}
                socket={socket}
              />
            } 
          />
          <Route 
            path="/analyze" 
            element={
              <LogAnalysis 
                agentsStatus={agentsStatus}
                socket={socket}
              />
            } 
          />
          <Route 
            path="/agents" 
            element={
              <AgentsManagement 
                agentsStatus={agentsStatus}
                onRefresh={fetchAgentsStatus}
              />
            } 
          />
          <Route 
            path="/stream" 
            element={
              <RealTimeStream 
                socket={socket}
                isConnected={isConnected}
              />
            } 
          />
          <Route 
            path="/health" 
            element={
              <SystemHealth 
                socket={socket}
                isConnected={isConnected}
                apiHealth={apiHealth}
                agentsStatus={agentsStatus}
              />
            } 
          />
        </Routes>
      </Container>
    </div>
  );
}

export default App;
