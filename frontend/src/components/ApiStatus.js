import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Badge, Button, Alert, Table } from 'react-bootstrap';
import { FaServer, FaCheckCircle, FaTimesCircle, FaSync, FaExternalLinkAlt } from 'react-icons/fa';
import { apiService } from '../services/apiService';

const ApiStatus = ({ apiHealth }) => {
  const [rootInfo, setRootInfo] = useState(null);
  const [lastChecked, setLastChecked] = useState(new Date());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchRootInfo();
  }, []);

  const fetchRootInfo = async () => {
    setLoading(true);
    try {
      const info = await apiService.getRootInfo();
      setRootInfo(info);
      setLastChecked(new Date());
    } catch (error) {
      console.error('Failed to fetch root info:', error);
    } finally {
      setLoading(false);
    }
  };

  const endpoints = [
    { name: 'Health Check', path: '/health', method: 'GET', description: 'System health status' },
    { name: 'Log Analysis (Text)', path: '/analyze', method: 'POST', description: 'Analyze log text content' },
    { name: 'Log Analysis (File)', path: '/batch-analyze', method: 'POST', description: 'Analyze uploaded log files' },
    { name: 'Sample Analysis', path: '/analyze/sample', method: 'POST', description: 'Analyze sample log data' },
    { name: 'Agent Status', path: '/agents/status', method: 'GET', description: 'Get AI agents status' },
    { name: 'Model Information', path: '/models', method: 'GET', description: 'Get model details and status' },
    { name: 'Metrics Summary', path: '/metrics/summary', method: 'GET', description: 'Get system metrics' },
  ];

  const StatusIndicator = ({ status }) => {
    const isOnline = status === 'operational' || status === 'online' || status === true;
    return (
      <div className="d-flex align-items-center">
        {isOnline ? (
          <>
            <FaCheckCircle className="text-success me-2" />
            <span className="text-success">Online</span>
          </>
        ) : (
          <>
            <FaTimesCircle className="text-danger me-2" />
            <span className="text-danger">Offline</span>
          </>
        )}
      </div>
    );
  };

  return (
    <div>
      <Row className="mb-4">
        <Col>
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <h2>
                <FaServer className="me-2" />
                API Status
              </h2>
              <p className="text-muted">
                Monitor the health and status of all API endpoints and services.
              </p>
            </div>
            <Button variant="outline-primary" onClick={fetchRootInfo} disabled={loading}>
              <FaSync className={`me-2 ${loading ? 'fa-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </Col>
      </Row>

      {/* Overall Status */}
      <Row className="mb-4">
        <Col md={6}>
          <Card>
            <Card.Header>
              <h6 className="mb-0">Overall System Status</h6>
            </Card.Header>
            <Card.Body>
              <div className="text-center py-3">
                <StatusIndicator status={apiHealth?.status || rootInfo?.status} />
                <div className="mt-2">
                  <small className="text-muted">
                    Last checked: {lastChecked.toLocaleTimeString()}
                  </small>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
        <Col md={6}>
          <Card>
            <Card.Header>
              <h6 className="mb-0">Quick Info</h6>
            </Card.Header>
            <Card.Body>
              <ul className="list-unstyled mb-0">
                <li><strong>Version:</strong> {rootInfo?.version || apiHealth?.version || 'N/A'}</li>
                <li><strong>API Base:</strong> {process.env.REACT_APP_API_URL || 'http://localhost:8000'}</li>
                <li><strong>Environment:</strong> Development</li>
                <li><strong>Uptime:</strong> {apiHealth?.uptime || 'N/A'}</li>
              </ul>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* API Endpoints */}
      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Header>
              <h6 className="mb-0">API Endpoints</h6>
            </Card.Header>
            <Card.Body>
              <Table striped responsive>
                <thead>
                  <tr>
                    <th>Endpoint</th>
                    <th>Method</th>
                    <th>Status</th>
                    <th>Description</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {endpoints.map((endpoint, index) => (
                    <tr key={index}>
                      <td>
                        <code>{endpoint.path}</code>
                      </td>
                      <td>
                        <Badge bg={endpoint.method === 'GET' ? 'success' : 'primary'}>
                          {endpoint.method}
                        </Badge>
                      </td>
                      <td>
                        <StatusIndicator status={true} />
                      </td>
                      <td>{endpoint.description}</td>
                      <td>
                        <Button
                          variant="outline-secondary"
                          size="sm"
                          onClick={() => window.open(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/docs`, '_blank')}
                        >
                          <FaExternalLinkAlt />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* System Information */}
      {(apiHealth || rootInfo) && (
        <Row className="mb-4">
          <Col>
            <Card>
              <Card.Header>
                <h6 className="mb-0">System Information</h6>
              </Card.Header>
              <Card.Body>
                <Row>
                  <Col md={6}>
                    <h6>API Details</h6>
                    <ul className="list-unstyled">
                      <li><strong>Name:</strong> {rootInfo?.name || 'LogBERT Hadoop RCA'}</li>
                      <li><strong>Description:</strong> {rootInfo?.description || 'AI Agent System'}</li>
                      <li><strong>Version:</strong> {rootInfo?.version || 'N/A'}</li>
                      <li><strong>Status:</strong> 
                        <Badge bg="success" className="ms-2">
                          {rootInfo?.status || 'Operational'}
                        </Badge>
                      </li>
                    </ul>
                  </Col>
                  <Col md={6}>
                    <h6>Available Resources</h6>
                    <ul className="list-unstyled">
                      <li>
                        <strong>API Documentation:</strong> 
                        <a href={`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/docs`} target="_blank" rel="noopener noreferrer" className="ms-2">
                          /docs <FaExternalLinkAlt size={12} />
                        </a>
                      </li>
                      <li>
                        <strong>ReDoc:</strong> 
                        <a href={`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/redoc`} target="_blank" rel="noopener noreferrer" className="ms-2">
                          /redoc <FaExternalLinkAlt size={12} />
                        </a>
                      </li>
                      <li>
                        <strong>Health Endpoint:</strong> 
                        <a href={`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/health`} target="_blank" rel="noopener noreferrer" className="ms-2">
                          /health <FaExternalLinkAlt size={12} />
                        </a>
                      </li>
                    </ul>
                  </Col>
                </Row>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Real-time Features */}
      {rootInfo?.socketio && (
        <Row className="mb-4">
          <Col>
            <Alert variant="info">
              <h6>Real-time Features</h6>
              <p className="mb-0">
                Socket.IO is {rootInfo.socketio.enabled ? 'enabled' : 'disabled'} for real-time communication.
                {rootInfo.socketio.enabled && (
                  <span> Connect to <code>{rootInfo.socketio.endpoint}</code> for live updates.</span>
                )}
              </p>
            </Alert>
          </Col>
        </Row>
      )}

      {/* Notes */}
      {rootInfo?.notes && (
        <Row>
          <Col>
            <Alert variant="warning">
              <h6>System Notes</h6>
              <p className="mb-0">{rootInfo.notes}</p>
            </Alert>
          </Col>
        </Row>
      )}
    </div>
  );
};

export default ApiStatus;
