import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Badge, Alert, Button } from 'react-bootstrap';
import { FaRobot, FaChartLine, FaExclamationTriangle, FaServer, FaClock, FaMemory } from 'react-icons/fa';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { apiService } from '../services/apiService';

const Dashboard = ({ apiHealth, isConnected }) => {
  const [systemStats, setSystemStats] = useState({
    totalAnalyzed: 0,
    anomaliesDetected: 0,
    rcaPerformed: 0,
    uptime: '0:00:00'
  });

  const [recentActivity, setRecentActivity] = useState([
    { time: '10:30 AM', action: 'Log Analysis', status: 'completed', duration: '2.3s' },
    { time: '10:28 AM', action: 'Anomaly Detection', status: 'completed', duration: '1.8s' },
    { time: '10:25 AM', action: 'RCA Analysis', status: 'completed', duration: '4.1s' },
    { time: '10:20 AM', action: 'Log Upload', status: 'completed', duration: '0.5s' },
  ]);

  const [performanceData] = useState([
    { name: '10:00', responses: 145, errors: 2 },
    { name: '10:15', responses: 158, errors: 1 },
    { name: '10:30', responses: 162, errors: 0 },
    { name: '10:45', responses: 149, errors: 3 },
    { name: '11:00', responses: 171, errors: 1 },
  ]);

  useEffect(() => {
    // Simulate updating stats
    const interval = setInterval(() => {
      setSystemStats(prev => ({
        ...prev,
        totalAnalyzed: prev.totalAnalyzed + Math.floor(Math.random() * 3),
        anomaliesDetected: prev.anomaliesDetected + Math.floor(Math.random() * 2),
      }));
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const MetricCard = ({ title, value, icon, color = "primary", subtitle }) => (
    <Card className="card-hover h-100">
      <Card.Body className="text-center">
        <div className={`text-${color} mb-3`} style={{ fontSize: '2rem' }}>
          {icon}
        </div>
        <h3 className="mb-1">{value}</h3>
        <h6 className="text-muted">{title}</h6>
        {subtitle && <small className="text-muted">{subtitle}</small>}
      </Card.Body>
    </Card>
  );

  return (
    <div>
      {/* Status Alert */}
      {isConnected ? (
        <Alert variant="success" className="mb-4">
          <div className="d-flex align-items-center">
            <div className="status-indicator status-online"></div>
            <strong>System Operational</strong> - All AI agents are running normally
          </div>
        </Alert>
      ) : (
        <Alert variant="danger" className="mb-4">
          <div className="d-flex align-items-center">
            <div className="status-indicator status-offline"></div>
            <strong>System Offline</strong> - Unable to connect to the API backend
          </div>
        </Alert>
      )}

      {/* Main Metrics */}
      <Row className="mb-4">
        <Col md={3}>
          <MetricCard
            title="Logs Analyzed"
            value={systemStats.totalAnalyzed.toLocaleString()}
            icon={<FaChartLine />}
            color="success"
            subtitle="Total processed"
          />
        </Col>
        <Col md={3}>
          <MetricCard
            title="Anomalies Detected"
            value={systemStats.anomaliesDetected.toLocaleString()}
            icon={<FaExclamationTriangle />}
            color="warning"
            subtitle="Potential issues found"
          />
        </Col>
        <Col md={3}>
          <MetricCard
            title="RCA Performed"
            value={systemStats.rcaPerformed.toLocaleString()}
            icon={<FaRobot />}
            color="info"
            subtitle="Root cause analyses"
          />
        </Col>
        <Col md={3}>
          <MetricCard
            title="System Uptime"
            value={apiHealth?.uptime || "N/A"}
            icon={<FaClock />}
            color="primary"
            subtitle="Current session"
          />
        </Col>
      </Row>

      {/* Charts and Activity */}
      <Row className="mb-4">
        <Col lg={8}>
          <Card className="h-100">
            <Card.Header>
              <h5 className="mb-0">
                <FaChartLine className="me-2" />
                System Performance
              </h5>
            </Card.Header>
            <Card.Body>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="responses" 
                    stroke="#28a745" 
                    strokeWidth={2}
                    name="Successful Responses"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="errors" 
                    stroke="#dc3545" 
                    strokeWidth={2}
                    name="Errors"
                  />
                </LineChart>
              </ResponsiveContainer>
            </Card.Body>
          </Card>
        </Col>
        
        <Col lg={4}>
          <Card className="h-100">
            <Card.Header>
              <h5 className="mb-0">
                <FaClock className="me-2" />
                Recent Activity
              </h5>
            </Card.Header>
            <Card.Body>
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                {recentActivity.map((activity, index) => (
                  <div key={index} className="d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom">
                    <div>
                      <div className="fw-semibold">{activity.action}</div>
                      <small className="text-muted">{activity.time}</small>
                    </div>
                    <div className="text-end">
                      <Badge bg={activity.status === 'completed' ? 'success' : 'warning'}>
                        {activity.status}
                      </Badge>
                      <div>
                        <small className="text-muted">{activity.duration}</small>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* API Health Details */}
      {apiHealth && (
        <Row>
          <Col>
            <Card>
              <Card.Header>
                <h5 className="mb-0">
                  <FaServer className="me-2" />
                  API Health Status
                </h5>
              </Card.Header>
              <Card.Body>
                <Row>
                  <Col md={6}>
                    <h6>System Information</h6>
                    <ul className="list-unstyled">
                      <li><strong>Version:</strong> {apiHealth.version || 'N/A'}</li>
                      <li><strong>Status:</strong> <Badge bg="success">{apiHealth.status || 'Unknown'}</Badge></li>
                      <li><strong>Database:</strong> <Badge bg={apiHealth.database ? 'success' : 'warning'}>
                        {apiHealth.database ? 'Connected' : 'Not Available'}
                      </Badge></li>
                    </ul>
                  </Col>
                  <Col md={6}>
                    <h6>AI Agents Status</h6>
                    <ul className="list-unstyled">
                      <li>
                        <FaRobot className="me-2" />
                        <strong>LogBERT Model:</strong> 
                        <Badge bg="success" className="ms-2">Active</Badge>
                      </li>
                      <li>
                        <FaExclamationTriangle className="me-2" />
                        <strong>Anomaly Detector:</strong> 
                        <Badge bg="success" className="ms-2">Active</Badge>
                      </li>
                      <li>
                        <FaChartLine className="me-2" />
                        <strong>RCA Agent:</strong> 
                        <Badge bg="success" className="ms-2">Active</Badge>
                      </li>
                    </ul>
                  </Col>
                </Row>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}
    </div>
  );
};

export default Dashboard;
