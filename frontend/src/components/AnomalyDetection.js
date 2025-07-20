import React, { useState, useCallback } from 'react';
import { Row, Col, Card, Button, Alert, Spinner, Badge, ProgressBar, Tabs, Tab } from 'react-bootstrap';
import { useDropzone } from 'react-dropzone';
import { FaExclamationTriangle, FaUpload, FaSearch, FaChartLine, FaEye } from 'react-icons/fa';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { toast } from 'react-toastify';
import { apiService } from '../services/apiService';

const AnomalyDetection = () => {
  const [activeTab, setActiveTab] = useState('upload');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [detectionResult, setDetectionResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    setUploadedFiles(acceptedFiles);
    toast.success(`${acceptedFiles.length} file(s) ready for anomaly detection`);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.log', '.txt'],
      'application/octet-stream': ['.log']
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024 // 50MB for anomaly detection
  });

  const detectAnomalies = async () => {
    if (uploadedFiles.length === 0) {
      toast.error('Please upload a log file first');
      return;
    }

    setLoading(true);
    try {
      const result = await apiService.detectAnomaliesFromFile(uploadedFiles[0]);
      setDetectionResult(result);
      toast.success(`Anomaly detection completed. Found ${result.anomalies?.length || 0} anomalies`);
    } catch (error) {
      toast.error(`Anomaly detection failed: ${error.message}`);
      console.error('Anomaly detection error:', error);
    } finally {
      setLoading(false);
    }
  };

  const COLORS = ['#28a745', '#dc3545', '#ffc107', '#17a2b8'];

  const AnomalyOverview = ({ result }) => {
    const anomalyData = [
      { name: 'Normal', value: result.normal_count || 0, color: '#28a745' },
      { name: 'Anomalous', value: result.anomaly_count || 0, color: '#dc3545' },
    ];

    const severityData = result.anomalies ? 
      result.anomalies.reduce((acc, anomaly) => {
        const severity = anomaly.severity || 'Medium';
        acc[severity] = (acc[severity] || 0) + 1;
        return acc;
      }, {}) : {};

    const severityChartData = Object.entries(severityData).map(([severity, count]) => ({
      name: severity,
      value: count,
      color: severity === 'High' ? '#dc3545' : severity === 'Medium' ? '#ffc107' : '#28a745'
    }));

    return (
      <Row className="mb-4">
        <Col md={6}>
          <Card>
            <Card.Header>
              <h6 className="mb-0">Detection Overview</h6>
            </Card.Header>
            <Card.Body>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={anomalyData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {anomalyData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Card.Body>
          </Card>
        </Col>
        <Col md={6}>
          <Card>
            <Card.Header>
              <h6 className="mb-0">Severity Distribution</h6>
            </Card.Header>
            <Card.Body>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={severityChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#8884d8">
                    {severityChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    );
  };

  const AnomalyList = ({ anomalies }) => (
    <Card>
      <Card.Header>
        <h6 className="mb-0">
          <FaExclamationTriangle className="me-2" />
          Detected Anomalies ({anomalies.length})
        </h6>
      </Card.Header>
      <Card.Body>
        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {anomalies.map((anomaly, index) => (
            <Card key={index} className="mb-3 border-start border-danger border-3">
              <Card.Body className="py-2">
                <Row className="align-items-center">
                  <Col md={8}>
                    <div className="d-flex align-items-center mb-2">
                      <Badge 
                        bg={anomaly.severity === 'High' ? 'danger' : anomaly.severity === 'Medium' ? 'warning' : 'info'}
                        className="me-2"
                      >
                        {anomaly.severity || 'Medium'}
                      </Badge>
                      <small className="text-muted">
                        {anomaly.timestamp || `Line ${anomaly.line_number || index + 1}`}
                      </small>
                    </div>
                    <div className="log-line" style={{ fontSize: '13px', maxHeight: '60px', overflow: 'hidden' }}>
                      {anomaly.log_content || anomaly.message}
                    </div>
                    {anomaly.confidence && (
                      <div className="mt-2">
                        <small className="text-muted">Confidence: </small>
                        <ProgressBar 
                          now={anomaly.confidence * 100} 
                          style={{ height: '8px', width: '100px', display: 'inline-block' }}
                          variant={anomaly.confidence > 0.8 ? 'danger' : anomaly.confidence > 0.6 ? 'warning' : 'info'}
                        />
                        <small className="ms-2">{(anomaly.confidence * 100).toFixed(1)}%</small>
                      </div>
                    )}
                  </Col>
                  <Col md={4} className="text-end">
                    <Button
                      variant="outline-primary"
                      size="sm"
                      onClick={() => setSelectedAnomaly(anomaly)}
                    >
                      <FaEye className="me-1" />
                      Details
                    </Button>
                  </Col>
                </Row>
              </Card.Body>
            </Card>
          ))}
        </div>
      </Card.Body>
    </Card>
  );

  const AnomalyDetails = ({ anomaly, onClose }) => (
    <Card className="mt-3">
      <Card.Header className="d-flex justify-content-between align-items-center">
        <h6 className="mb-0">Anomaly Details</h6>
        <Button variant="outline-secondary" size="sm" onClick={onClose}>
          ×
        </Button>
      </Card.Header>
      <Card.Body>
        <Row>
          <Col md={6}>
            <h6>Basic Information</h6>
            <ul className="list-unstyled">
              <li><strong>Severity:</strong> 
                <Badge bg={anomaly.severity === 'High' ? 'danger' : anomaly.severity === 'Medium' ? 'warning' : 'info'} className="ms-2">
                  {anomaly.severity || 'Medium'}
                </Badge>
              </li>
              <li><strong>Timestamp:</strong> {anomaly.timestamp || 'N/A'}</li>
              <li><strong>Line Number:</strong> {anomaly.line_number || 'N/A'}</li>
              {anomaly.confidence && (
                <li><strong>Confidence:</strong> {(anomaly.confidence * 100).toFixed(1)}%</li>
              )}
            </ul>
          </Col>
          <Col md={6}>
            <h6>Detection Details</h6>
            <ul className="list-unstyled">
              <li><strong>Type:</strong> {anomaly.anomaly_type || 'General'}</li>
              <li><strong>Category:</strong> {anomaly.category || 'System'}</li>
              {anomaly.component && (
                <li><strong>Component:</strong> {anomaly.component}</li>
              )}
            </ul>
          </Col>
        </Row>
        
        <h6 className="mt-3">Log Content</h6>
        <div className="log-viewer" style={{ maxHeight: '150px' }}>
          {anomaly.log_content || anomaly.message}
        </div>
        
        {anomaly.context && (
          <>
            <h6 className="mt-3">Context</h6>
            <Alert variant="info">
              {anomaly.context}
            </Alert>
          </>
        )}
        
        {anomaly.suggested_actions && (
          <>
            <h6 className="mt-3">Suggested Actions</h6>
            <ul>
              {anomaly.suggested_actions.map((action, index) => (
                <li key={index}>{action}</li>
              ))}
            </ul>
          </>
        )}
      </Card.Body>
    </Card>
  );

  return (
    <div>
      <Row className="mb-4">
        <Col>
          <h2>
            <FaExclamationTriangle className="me-2" />
            Anomaly Detection
          </h2>
          <p className="text-muted">
            Upload log files to detect anomalous patterns using Deep SVDD and LogBERT models.
          </p>
        </Col>
      </Row>

      <Card className="mb-4">
        <Card.Header>
          <Tabs activeKey={activeTab} onSelect={setActiveTab}>
            <Tab eventKey="upload" title={<><FaUpload className="me-1" />Upload & Detect</>} />
            {detectionResult && (
              <Tab eventKey="results" title={<><FaChartLine className="me-1" />Results</>} />
            )}
          </Tabs>
        </Card.Header>
        <Card.Body>
          {activeTab === 'upload' && (
            <div>
              <div {...getRootProps()} className={`upload-area ${isDragActive ? 'active' : ''}`}>
                <input {...getInputProps()} />
                <FaUpload size={48} className="text-muted mb-3" />
                <h5>Drop log files here for anomaly detection</h5>
                <p className="text-muted">
                  Supports .log and .txt files up to 50MB
                </p>
                {uploadedFiles.length > 0 && (
                  <Alert variant="success" className="mt-3">
                    <strong>File ready for analysis:</strong>
                    <div className="mt-2">
                      {uploadedFiles[0].name} ({(uploadedFiles[0].size / 1024 / 1024).toFixed(1)} MB)
                    </div>
                  </Alert>
                )}
              </div>
              
              <div className="text-center mt-4">
                <Button 
                  variant="primary" 
                  size="lg"
                  onClick={detectAnomalies}
                  disabled={loading || uploadedFiles.length === 0}
                >
                  {loading ? (
                    <>
                      <Spinner animation="border" size="sm" className="me-2" />
                      Detecting Anomalies...
                    </>
                  ) : (
                    <>
                      <FaSearch className="me-2" />
                      Start Anomaly Detection
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}

          {activeTab === 'results' && detectionResult && (
            <div>
              <AnomalyOverview result={detectionResult} />
              {detectionResult.anomalies && detectionResult.anomalies.length > 0 ? (
                <AnomalyList anomalies={detectionResult.anomalies} />
              ) : (
                <Alert variant="success">
                  <FaExclamationTriangle className="me-2" />
                  No anomalies detected in the analyzed logs. The system appears to be operating normally.
                </Alert>
              )}
            </div>
          )}
        </Card.Body>
      </Card>

      {selectedAnomaly && (
        <AnomalyDetails 
          anomaly={selectedAnomaly} 
          onClose={() => setSelectedAnomaly(null)} 
        />
      )}
    </div>
  );
};

export default AnomalyDetection;
