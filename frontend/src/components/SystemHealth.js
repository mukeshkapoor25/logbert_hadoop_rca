import React, { useState, useEffect, useCallback } from 'react';
import { Row, Col, Card, Button, Alert, ProgressBar, Badge, Table } from 'react-bootstrap';
import { 
  FaHeartbeat, FaServer, FaMemory, FaMicrochip, FaHdd, FaWifi, 
  FaExclamationTriangle, FaCheckCircle, FaTimesCircle, FaSync 
} from 'react-icons/fa';
import { toast } from 'react-toastify';
import { apiService } from '../services/apiService';

const SystemHealth = ({ socket, isConnected }) => {
  const [systemMetrics, setSystemMetrics] = useState({
    cpu: 0,
    memory: 0,
    disk: 0,
    network: 0,
    uptime: 0,
    lastUpdate: null
  });

  const [agentHealth, setAgentHealth] = useState({
    coordinator: { status: 'unknown', responseTime: 0, load: 0 },
    anomaly_detection: { status: 'unknown', responseTime: 0, load: 0 },
    root_cause: { status: 'unknown', responseTime: 0, load: 0 },
    log_parser: { status: 'unknown', responseTime: 0, load: 0 },
    explanation: { status: 'unknown', responseTime: 0, load: 0 }
  });

  const [systemAlerts, setSystemAlerts] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSystemMetricsUpdate = useCallback((data) => {
    setSystemMetrics({
      cpu: data.cpu || 0,
      memory: data.memory || 0,
      disk: data.disk || 0,
      network: data.network || 0,
      uptime: data.uptime || 0,
      lastUpdate: new Date()
    });
  }, []);

  const handleAgentHealthUpdate = useCallback((data) => {
    setAgentHealth(prev => ({
      ...prev,
      [data.agentId]: {
        status: data.status || 'unknown',
        responseTime: data.responseTime || 0,
        load: data.load || 0,
        lastHeartbeat: new Date()
      }
    }));
  }, []);

  const handleSystemAlert = useCallback((alert) => {
    setSystemAlerts(prev => [
      {
        id: Date.now(),
        timestamp: new Date(),
        ...alert
      },
      ...prev.slice(0, 9) // Keep only last 10 alerts
    ]);

    // Show toast for critical alerts
    if (alert.level === 'critical' || alert.level === 'error') {
      toast.error(`System Alert: ${alert.message}`);
    } else if (alert.level === 'warning') {
      toast.warn(`System Warning: ${alert.message}`);
    }
  }, []);

  useEffect(() => {
    if (socket && isConnected) {
      socket.on('system_metrics', handleSystemMetricsUpdate);
      socket.on('agent_health', handleAgentHealthUpdate);
      socket.on('system_alert', handleSystemAlert);

      return () => {
        socket.off('system_metrics');
        socket.off('agent_health');
        socket.off('system_alert');
      };
    }
  }, [socket, isConnected, handleSystemMetricsUpdate, handleAgentHealthUpdate, handleSystemAlert]);

  const refreshSystemHealth = async () => {
    setIsLoading(true);
    try {
      const healthData = await apiService.getSystemHealth();
      
      if (healthData.metrics) {
        setSystemMetrics({
          ...healthData.metrics,
          lastUpdate: new Date()
        });
      }

      if (healthData.agents) {
        setAgentHealth(healthData.agents);
      }

      if (healthData.alerts) {
        setSystemAlerts(healthData.alerts.slice(0, 10));
      }

      toast.success('System health refreshed');
    } catch (error) {
      toast.error(`Failed to refresh system health: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const getMetricColor = (value) => {
    if (value >= 90) return 'danger';
    if (value >= 75) return 'warning';
    if (value >= 50) return 'info';
    return 'success';
  };

  const getAgentStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
      case 'running':
        return <FaCheckCircle className="text-success" />;
      case 'warning':
        return <FaExclamationTriangle className="text-warning" />;
      case 'error':
      case 'failed':
        return <FaTimesCircle className="text-danger" />;
      default:
        return <FaServer className="text-muted" />;
    }
  };

  const getAgentStatusBadge = (status) => {
    switch (status) {
      case 'healthy':
      case 'running':
        return <Badge bg="success">Healthy</Badge>;
      case 'warning':
        return <Badge bg="warning">Warning</Badge>;
      case 'error':
      case 'failed':
        return <Badge bg="danger">Error</Badge>;
      default:
        return <Badge bg="secondary">Unknown</Badge>;
    }
  };

  const getAlertVariant = (level) => {
    switch (level) {
      case 'critical':
      case 'error':
        return 'danger';
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
      default:
        return 'secondary';
    }
  };

  const formatUptime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  return (
    <div>
      <Row className="mb-4">
        <Col>
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <h2>
                <FaHeartbeat className="me-2" />
                System Health Monitor
              </h2>
              <p className="text-muted">
                Real-time system metrics and AI agents health monitoring
              </p>
            </div>
            <div>
              <Button
                variant="outline-primary"
                onClick={refreshSystemHealth}
                disabled={isLoading}
              >
                <FaSync className={`me-2 ${isLoading ? 'fa-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </Col>
      </Row>

      {!isConnected && (
        <Alert variant="warning" className="mb-4">
          <strong>WebSocket Disconnected:</strong> Real-time health monitoring requires an active WebSocket connection.
          Health data may not be current.
        </Alert>
      )}

      {/* System Metrics */}
      <Row className="mb-4">
        <Col lg={3} md={6} className="mb-3">
          <Card>
            <Card.Body>
              <div className="d-flex align-items-center">
                <FaMicrochip className="text-primary me-3" size={24} />
                <div className="flex-grow-1">
                  <h6 className="mb-1">CPU Usage</h6>
                  <ProgressBar 
                    variant={getMetricColor(systemMetrics.cpu)} 
                    now={systemMetrics.cpu} 
                    label={`${systemMetrics.cpu}%`}
                  />
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col lg={3} md={6} className="mb-3">
          <Card>
            <Card.Body>
              <div className="d-flex align-items-center">
                <FaMemory className="text-success me-3" size={24} />
                <div className="flex-grow-1">
                  <h6 className="mb-1">Memory Usage</h6>
                  <ProgressBar 
                    variant={getMetricColor(systemMetrics.memory)} 
                    now={systemMetrics.memory} 
                    label={`${systemMetrics.memory}%`}
                  />
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col lg={3} md={6} className="mb-3">
          <Card>
            <Card.Body>
              <div className="d-flex align-items-center">
                <FaHdd className="text-warning me-3" size={24} />
                <div className="flex-grow-1">
                  <h6 className="mb-1">Disk Usage</h6>
                  <ProgressBar 
                    variant={getMetricColor(systemMetrics.disk)} 
                    now={systemMetrics.disk} 
                    label={`${systemMetrics.disk}%`}
                  />
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col lg={3} md={6} className="mb-3">
          <Card>
            <Card.Body>
              <div className="d-flex align-items-center">
                <FaWifi className="text-info me-3" size={24} />
                <div className="flex-grow-1">
                  <h6 className="mb-1">Network I/O</h6>
                  <ProgressBar 
                    variant={getMetricColor(systemMetrics.network)} 
                    now={systemMetrics.network} 
                    label={`${systemMetrics.network}%`}
                  />
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row className="mb-4">
        {/* Agent Health Status */}
        <Col lg={8}>
          <Card>
            <Card.Header>
              <h6 className="mb-0">AI Agents Health Status</h6>
            </Card.Header>
            <Card.Body>
              <Table responsive className="mb-0">
                <thead>
                  <tr>
                    <th>Agent</th>
                    <th>Status</th>
                    <th>Response Time</th>
                    <th>Load</th>
                    <th>Last Heartbeat</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(agentHealth).map(([agentId, health]) => (
                    <tr key={agentId}>
                      <td>
                        <div className="d-flex align-items-center">
                          {getAgentStatusIcon(health.status)}
                          <span className="ms-2 text-capitalize">
                            {agentId.replace('_', ' ')}
                          </span>
                        </div>
                      </td>
                      <td>
                        {getAgentStatusBadge(health.status)}
                      </td>
                      <td>
                        <span className={health.responseTime > 1000 ? 'text-warning' : 'text-success'}>
                          {health.responseTime}ms
                        </span>
                      </td>
                      <td>
                        <ProgressBar 
                          variant={getMetricColor(health.load)} 
                          now={health.load} 
                          style={{ width: '100px' }}
                        />
                      </td>
                      <td>
                        <small className="text-muted">
                          {health.lastHeartbeat ? 
                            health.lastHeartbeat.toLocaleTimeString() : 
                            'Never'
                          }
                        </small>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>

        {/* System Summary */}
        <Col lg={4}>
          <Card>
            <Card.Header>
              <h6 className="mb-0">System Summary</h6>
            </Card.Header>
            <Card.Body>
              <div className="mb-3">
                <div className="d-flex justify-content-between">
                  <span>System Uptime:</span>
                  <span className="text-success">
                    {formatUptime(systemMetrics.uptime)}
                  </span>
                </div>
              </div>

              <div className="mb-3">
                <div className="d-flex justify-content-between">
                  <span>WebSocket Status:</span>
                  <Badge bg={isConnected ? 'success' : 'danger'}>
                    {isConnected ? 'Connected' : 'Disconnected'}
                  </Badge>
                </div>
              </div>

              <div className="mb-3">
                <div className="d-flex justify-content-between">
                  <span>Active Agents:</span>
                  <span className="text-info">
                    {Object.values(agentHealth).filter(h => h.status === 'healthy' || h.status === 'running').length}/5
                  </span>
                </div>
              </div>

              <div className="mb-3">
                <div className="d-flex justify-content-between">
                  <span>System Load:</span>
                  <span className={`text-${getMetricColor((systemMetrics.cpu + systemMetrics.memory) / 2)}`}>
                    {((systemMetrics.cpu + systemMetrics.memory) / 2).toFixed(1)}%
                  </span>
                </div>
              </div>

              {systemMetrics.lastUpdate && (
                <div>
                  <small className="text-muted">
                    Last updated: {systemMetrics.lastUpdate.toLocaleTimeString()}
                  </small>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* System Alerts */}
      <Row>
        <Col>
          <Card>
            <Card.Header>
              <h6 className="mb-0">Recent System Alerts</h6>
            </Card.Header>
            <Card.Body>
              {systemAlerts.length === 0 ? (
                <div className="text-center text-muted py-3">
                  <FaCheckCircle className="me-2" />
                  No recent alerts. System is running normally.
                </div>
              ) : (
                <div className="alerts-container" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                  {systemAlerts.map((alert) => (
                    <Alert key={alert.id} variant={getAlertVariant(alert.level)} className="mb-2">
                      <div className="d-flex justify-content-between align-items-start">
                        <div>
                          <strong>{alert.title || 'System Alert'}</strong>
                          <div>{alert.message}</div>
                          {alert.source && (
                            <small className="text-muted">Source: {alert.source}</small>
                          )}
                        </div>
                        <small className="text-muted">
                          {alert.timestamp.toLocaleTimeString()}
                        </small>
                      </div>
                    </Alert>
                  ))}
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default SystemHealth;
