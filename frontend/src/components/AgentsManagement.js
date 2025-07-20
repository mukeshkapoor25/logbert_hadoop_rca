import React, { useState } from 'react';
import { Row, Col, Card, Button, Badge, Alert, Spinner, Modal } from 'react-bootstrap';
import { FaRobot, FaPlay, FaSync, FaEye, FaCogs, FaCheckCircle, FaExclamationCircle, FaTimesCircle } from 'react-icons/fa';
import { toast } from 'react-toastify';
import { apiService } from '../services/apiService';

const AgentsManagement = ({ agentsStatus, onRefresh }) => {
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [showLogsModal, setShowLogsModal] = useState(false);
  const [agentLogs, setAgentLogs] = useState('');
  const [loadingActions, setLoadingActions] = useState({});
  const [testResults, setTestResults] = useState({});

  const agentDefinitions = {
    coordinator: {
      name: 'Coordinator Agent',
      description: 'Orchestrates the entire analysis pipeline',
      icon: <FaCogs />,
      color: 'primary',
      responsibilities: ['Task distribution', 'Result aggregation', 'Error handling', 'Workflow management']
    },
    anomaly: {
      name: 'Anomaly Detection Agent',
      description: 'LogBERT-based anomaly detection',
      icon: <FaExclamationCircle />,
      color: 'warning',
      responsibilities: ['Pattern analysis', 'Anomaly scoring', 'LogBERT inference', 'Threshold evaluation']
    },
    'root-cause': {
      name: 'Root Cause Agent',
      description: 'Identifies root causes of detected anomalies',
      icon: <FaCheckCircle />,
      color: 'danger',
      responsibilities: ['Pattern matching', 'Correlation analysis', 'Causality detection', 'Impact assessment']
    },
    'log-parser': {
      name: 'Log Parser Agent',
      description: 'Parses and structures raw log data',
      icon: <FaEye />,
      color: 'info',
      responsibilities: ['Format detection', 'Structure extraction', 'Timestamp parsing', 'Field normalization']
    },
    explanation: {
      name: 'Explanation Agent',
      description: 'Generates human-readable explanations',
      icon: <FaRobot />,
      color: 'success',
      responsibilities: ['Natural language generation', 'Insight summarization', 'Recommendation creation', 'Report formatting']
    }
  };

  const handleTestAgent = async (agentId) => {
    setLoadingActions(prev => ({ ...prev, [`test_${agentId}`]: true }));
    try {
      const result = await apiService.testAgent(agentId);
      setTestResults(prev => ({ ...prev, [agentId]: result }));
      toast.success(`${agentDefinitions[agentId]?.name} test completed successfully`);
    } catch (error) {
      toast.error(`Test failed for ${agentDefinitions[agentId]?.name}: ${error.message}`);
    } finally {
      setLoadingActions(prev => ({ ...prev, [`test_${agentId}`]: false }));
    }
  };

  const handleRestartAgent = async (agentId) => {
    setLoadingActions(prev => ({ ...prev, [`restart_${agentId}`]: true }));
    try {
      await apiService.restartAgent(agentId);
      toast.success(`${agentDefinitions[agentId]?.name} restarted successfully`);
      onRefresh();
    } catch (error) {
      toast.error(`Restart failed for ${agentDefinitions[agentId]?.name}: ${error.message}`);
    } finally {
      setLoadingActions(prev => ({ ...prev, [`restart_${agentId}`]: false }));
    }
  };

  const handleViewLogs = async (agentId) => {
    setSelectedAgent(agentId);
    setShowLogsModal(true);
    try {
      const logs = await apiService.getAgentLogs(agentId);
      setAgentLogs(logs.logs || 'No logs available');
    } catch (error) {
      setAgentLogs(`Error loading logs: ${error.message}`);
    }
  };

  const handleStartAllAgents = async () => {
    setLoadingActions(prev => ({ ...prev, start_all: true }));
    try {
      await apiService.startAllAgents();
      toast.success('All agents started successfully');
      onRefresh();
    } catch (error) {
      toast.error(`Failed to start all agents: ${error.message}`);
    } finally {
      setLoadingActions(prev => ({ ...prev, start_all: false }));
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <FaCheckCircle className="text-success" />;
      case 'inactive':
        return <FaTimesCircle className="text-danger" />;
      case 'error':
        return <FaExclamationCircle className="text-warning" />;
      default:
        return <FaTimesCircle className="text-muted" />;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'active':
        return <Badge bg="success">Active</Badge>;
      case 'inactive':
        return <Badge bg="danger">Inactive</Badge>;
      case 'error':
        return <Badge bg="warning">Error</Badge>;
      default:
        return <Badge bg="secondary">Unknown</Badge>;
    }
  };

  const AgentCard = ({ agentId, agentInfo, agentData }) => (
    <Card className="h-100 card-hover">
      <Card.Header className={`bg-${agentInfo.color} text-white`}>
        <div className="d-flex justify-content-between align-items-center">
          <div>
            {agentInfo.icon}
            <span className="ms-2">{agentInfo.name}</span>
          </div>
          {getStatusIcon(agentData?.status)}
        </div>
      </Card.Header>
      <Card.Body>
        <p className="text-muted mb-3">{agentInfo.description}</p>
        
        <div className="mb-3">
          <h6>Status: {getStatusBadge(agentData?.status)}</h6>
          {agentData?.last_activity && (
            <small className="text-muted">Last Activity: {agentData.last_activity}</small>
          )}
        </div>

        <div className="mb-3">
          <h6>Metrics:</h6>
          <Row className="text-center">
            <Col>
              <div className="metric-item">
                <div className="h5 mb-0">{agentData?.total_executions || 0}</div>
                <small className="text-muted">Executions</small>
              </div>
            </Col>
            <Col>
              <div className="metric-item">
                <div className="h5 mb-0">{agentData?.success_rate || 0}%</div>
                <small className="text-muted">Success Rate</small>
              </div>
            </Col>
          </Row>
        </div>

        <div className="mb-3">
          <h6>Responsibilities:</h6>
          <ul className="list-unstyled">
            {agentInfo.responsibilities.map((resp, index) => (
              <li key={index} className="small">
                <FaCheckCircle className="text-success me-1" size="0.8em" />
                {resp}
              </li>
            ))}
          </ul>
        </div>

        {testResults[agentId] && (
          <Alert variant={testResults[agentId].success ? 'success' : 'danger'} className="small">
            <strong>Test Result:</strong> {testResults[agentId].message}
          </Alert>
        )}
      </Card.Body>
      <Card.Footer>
        <div className="d-grid gap-2">
          <div className="btn-group">
            <Button
              variant="outline-primary"
              size="sm"
              onClick={() => handleTestAgent(agentId)}
              disabled={loadingActions[`test_${agentId}`]}
            >
              {loadingActions[`test_${agentId}`] ? (
                <Spinner animation="border" size="sm" />
              ) : (
                <>
                  <FaPlay className="me-1" />
                  Test
                </>
              )}
            </Button>
            <Button
              variant="outline-warning"
              size="sm"
              onClick={() => handleRestartAgent(agentId)}
              disabled={loadingActions[`restart_${agentId}`]}
            >
              {loadingActions[`restart_${agentId}`] ? (
                <Spinner animation="border" size="sm" />
              ) : (
                <>
                  <FaSync className="me-1" />
                  Restart
                </>
              )}
            </Button>
            <Button
              variant="outline-info"
              size="sm"
              onClick={() => handleViewLogs(agentId)}
            >
              <FaEye className="me-1" />
              Logs
            </Button>
          </div>
        </div>
      </Card.Footer>
    </Card>
  );

  return (
    <div>
      <Row className="mb-4">
        <Col>
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <h2>
                <FaCogs className="me-2" />
                AI Agents Management
              </h2>
              <p className="text-muted">
                Monitor and control the 5 specialized AI agents powering the LogBERT system
              </p>
            </div>
            <div>
              <Button
                variant="success"
                onClick={handleStartAllAgents}
                disabled={loadingActions.start_all}
                className="me-2"
              >
                {loadingActions.start_all ? (
                  <>
                    <Spinner animation="border" size="sm" className="me-2" />
                    Starting...
                  </>
                ) : (
                  <>
                    <FaPlay className="me-2" />
                    Start All Agents
                  </>
                )}
              </Button>
              <Button variant="outline-primary" onClick={onRefresh}>
                <FaSync className="me-2" />
                Refresh Status
              </Button>
            </div>
          </div>
        </Col>
      </Row>

      {/* Agents Overview */}
      {agentsStatus?.summary && (
        <Row className="mb-4">
          <Col md={3}>
            <Card className="text-center">
              <Card.Body>
                <h3 className="text-success">{agentsStatus.summary.active || 0}</h3>
                <small className="text-muted">Active Agents</small>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3}>
            <Card className="text-center">
              <Card.Body>
                <h3 className="text-primary">{agentsStatus.summary.total_executions || 0}</h3>
                <small className="text-muted">Total Executions</small>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3}>
            <Card className="text-center">
              <Card.Body>
                <h3 className="text-info">{agentsStatus.summary.avg_response_time || 0}ms</h3>
                <small className="text-muted">Avg Response Time</small>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3}>
            <Card className="text-center">
              <Card.Body>
                <h3 className="text-warning">{agentsStatus.summary.success_rate || 0}%</h3>
                <small className="text-muted">Overall Success Rate</small>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Agent Cards */}
      <Row>
        {Object.entries(agentDefinitions).map(([agentId, agentInfo]) => (
          <Col lg={6} xl={4} key={agentId} className="mb-4">
            <AgentCard
              agentId={agentId}
              agentInfo={agentInfo}
              agentData={agentsStatus?.agents?.[agentId]}
            />
          </Col>
        ))}
      </Row>

      {/* Communication Flow Visualization */}
      <Row className="mt-4">
        <Col>
          <Card>
            <Card.Header>
              <h5 className="mb-0">Agent Communication Flow</h5>
            </Card.Header>
            <Card.Body>
              <div className="text-center">
                <div className="d-flex justify-content-center align-items-center flex-wrap">
                  <Badge bg="primary" className="me-2 mb-2 p-2">
                    <FaCogs className="me-1" />
                    Coordinator
                  </Badge>
                  <span className="me-2">→</span>
                  <Badge bg="info" className="me-2 mb-2 p-2">
                    <FaEye className="me-1" />
                    Parser
                  </Badge>
                  <span className="me-2">→</span>
                  <Badge bg="warning" className="me-2 mb-2 p-2">
                    <FaExclamationCircle className="me-1" />
                    Anomaly
                  </Badge>
                  <span className="me-2">→</span>
                  <Badge bg="danger" className="me-2 mb-2 p-2">
                    <FaCheckCircle className="me-1" />
                    Root Cause
                  </Badge>
                  <span className="me-2">→</span>
                  <Badge bg="success" className="me-2 mb-2 p-2">
                    <FaRobot className="me-1" />
                    Explanation
                  </Badge>
                </div>
                <small className="text-muted mt-2 d-block">
                  Data flows through the agent pipeline for comprehensive log analysis
                </small>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Logs Modal */}
      <Modal show={showLogsModal} onHide={() => setShowLogsModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>
            {selectedAgent && agentDefinitions[selectedAgent]?.name} Logs
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="log-viewer" style={{ height: '400px', overflowY: 'auto' }}>
            <pre>{agentLogs}</pre>
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowLogsModal(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default AgentsManagement;
