import React, { useState, useCallback } from 'react';
import { Row, Col, Card, Button, Alert, Spinner, Badge, Form } from 'react-bootstrap';
import { useDropzone } from 'react-dropzone';
import { FaRobot, FaUpload, FaSearch, FaBrain, FaLightbulb, FaTools } from 'react-icons/fa';
import { toast } from 'react-toastify';
import { apiService } from '../services/apiService';

const RootCauseAnalysis = () => {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [rcaResult, setRcaResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analysisOptions, setAnalysisOptions] = useState({
    includeContext: true,
    detailedExplanation: true,
    suggestActions: true,
    correlateEvents: true
  });

  const onDrop = useCallback((acceptedFiles) => {
    setUploadedFiles(acceptedFiles);
    toast.success(`${acceptedFiles.length} file(s) ready for RCA`);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.log', '.txt'],
      'application/octet-stream': ['.log']
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024 // 50MB
  });

  const performRCA = async () => {
    if (uploadedFiles.length === 0) {
      toast.error('Please upload a log file first');
      return;
    }

    setLoading(true);
    try {
      const result = await apiService.performRCAFromFile(uploadedFiles[0], analysisOptions);
      setRcaResult(result);
      toast.success('Root cause analysis completed successfully');
    } catch (error) {
      toast.error(`RCA failed: ${error.message}`);
      console.error('RCA error:', error);
    } finally {
      setLoading(false);
    }
  };

  const RCAResults = ({ result }) => (
    <div>
      {/* Summary Card */}
      <Card className="mb-4">
        <Card.Header className="bg-primary text-white">
          <h5 className="mb-0">
            <FaBrain className="me-2" />
            Root Cause Analysis Summary
          </h5>
        </Card.Header>
        <Card.Body>
          <Row>
            <Col md={6}>
              <h6>Analysis Overview</h6>
              <ul className="list-unstyled">
                <li><strong>Issues Identified:</strong> {result.issues_count || 0}</li>
                <li><strong>Confidence Level:</strong> 
                  <Badge bg={result.confidence > 0.8 ? 'success' : result.confidence > 0.6 ? 'warning' : 'danger'} className="ms-2">
                    {result.confidence ? `${(result.confidence * 100).toFixed(1)}%` : 'N/A'}
                  </Badge>
                </li>
                <li><strong>Processing Time:</strong> {result.processing_time || 'N/A'}</li>
                <li><strong>Analysis Method:</strong> AI-Powered RCA</li>
              </ul>
            </Col>
            <Col md={6}>
              <h6>System Status</h6>
              <ul className="list-unstyled">
                <li><strong>Overall Health:</strong> 
                  <Badge bg={result.system_health === 'Good' ? 'success' : result.system_health === 'Warning' ? 'warning' : 'danger'} className="ms-2">
                    {result.system_health || 'Unknown'}
                  </Badge>
                </li>
                <li><strong>Critical Issues:</strong> {result.critical_issues || 0}</li>
                <li><strong>Warnings:</strong> {result.warnings || 0}</li>
                <li><strong>Recommendations:</strong> {result.recommendations?.length || 0}</li>
              </ul>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Root Causes */}
      {result.root_causes && result.root_causes.length > 0 && (
        <Card className="mb-4">
          <Card.Header>
            <h6 className="mb-0">
              <FaSearch className="me-2" />
              Identified Root Causes
            </h6>
          </Card.Header>
          <Card.Body>
            {result.root_causes.map((cause, index) => (
              <Card key={index} className="mb-3 border-start border-danger border-3">
                <Card.Body>
                  <Row>
                    <Col md={8}>
                      <h6 className="text-danger">{cause.title || `Root Cause ${index + 1}`}</h6>
                      <p className="mb-2">{cause.description}</p>
                      {cause.evidence && (
                        <div className="mb-2">
                          <small className="text-muted">Evidence:</small>
                          <div className="log-viewer mt-1" style={{ fontSize: '12px', maxHeight: '100px' }}>
                            {cause.evidence}
                          </div>
                        </div>
                      )}
                    </Col>
                    <Col md={4}>
                      <div className="text-end">
                        <Badge bg={cause.severity === 'High' ? 'danger' : cause.severity === 'Medium' ? 'warning' : 'info'}>
                          {cause.severity || 'Medium'} Impact
                        </Badge>
                        {cause.confidence && (
                          <div className="mt-2">
                            <small>Confidence: {(cause.confidence * 100).toFixed(1)}%</small>
                          </div>
                        )}
                      </div>
                    </Col>
                  </Row>
                  {cause.affected_components && (
                    <div className="mt-2">
                      <small className="text-muted">Affected Components: </small>
                      {cause.affected_components.map((component, idx) => (
                        <Badge key={idx} bg="secondary" className="me-1">
                          {component}
                        </Badge>
                      ))}
                    </div>
                  )}
                </Card.Body>
              </Card>
            ))}
          </Card.Body>
        </Card>
      )}

      {/* AI Explanation */}
      {result.explanation && (
        <Card className="mb-4">
          <Card.Header>
            <h6 className="mb-0">
              <FaLightbulb className="me-2" />
              AI Analysis Explanation
            </h6>
          </Card.Header>
          <Card.Body>
            <Alert variant="info">
              <div dangerouslySetInnerHTML={{ __html: result.explanation.replace(/\n/g, '<br>') }} />
            </Alert>
          </Card.Body>
        </Card>
      )}

      {/* Recommendations */}
      {result.recommendations && result.recommendations.length > 0 && (
        <Card className="mb-4">
          <Card.Header>
            <h6 className="mb-0">
              <FaTools className="me-2" />
              Recommended Actions
            </h6>
          </Card.Header>
          <Card.Body>
            {result.recommendations.map((rec, index) => (
              <Card key={index} className="mb-3 border-start border-success border-3">
                <Card.Body>
                  <Row>
                    <Col md={8}>
                      <h6 className="text-success">{rec.title || `Recommendation ${index + 1}`}</h6>
                      <p className="mb-2">{rec.description}</p>
                      {rec.steps && (
                        <div>
                          <small className="text-muted">Implementation Steps:</small>
                          <ol className="mt-1">
                            {rec.steps.map((step, stepIdx) => (
                              <li key={stepIdx} style={{ fontSize: '14px' }}>{step}</li>
                            ))}
                          </ol>
                        </div>
                      )}
                    </Col>
                    <Col md={4}>
                      <div className="text-end">
                        <Badge bg={rec.priority === 'High' ? 'danger' : rec.priority === 'Medium' ? 'warning' : 'success'}>
                          {rec.priority || 'Medium'} Priority
                        </Badge>
                        {rec.effort && (
                          <div className="mt-2">
                            <small>Effort: {rec.effort}</small>
                          </div>
                        )}
                      </div>
                    </Col>
                  </Row>
                </Card.Body>
              </Card>
            ))}
          </Card.Body>
        </Card>
      )}

      {/* Timeline */}
      {result.timeline && result.timeline.length > 0 && (
        <Card className="mb-4">
          <Card.Header>
            <h6 className="mb-0">
              <FaSearch className="me-2" />
              Event Timeline
            </h6>
          </Card.Header>
          <Card.Body>
            <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
              {result.timeline.map((event, index) => (
                <div key={index} className="d-flex mb-3 pb-2 border-bottom">
                  <div className="flex-shrink-0">
                    <div className={`status-indicator ${event.type === 'error' ? 'bg-danger' : event.type === 'warning' ? 'bg-warning' : 'bg-info'}`}></div>
                  </div>
                  <div className="flex-grow-1 ms-3">
                    <div className="d-flex justify-content-between">
                      <h6 className="mb-1">{event.title}</h6>
                      <small className="text-muted">{event.timestamp}</small>
                    </div>
                    <p className="mb-1" style={{ fontSize: '14px' }}>{event.description}</p>
                    {event.impact && (
                      <Badge bg="secondary" size="sm">{event.impact}</Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Card.Body>
        </Card>
      )}
    </div>
  );

  return (
    <div>
      <Row className="mb-4">
        <Col>
          <h2>
            <FaRobot className="me-2" />
            Root Cause Analysis
          </h2>
          <p className="text-muted">
            Upload log files for AI-powered root cause analysis using advanced NLP and machine learning models.
          </p>
        </Col>
      </Row>

      {!rcaResult ? (
        <Row>
          <Col lg={8}>
            <Card>
              <Card.Header>
                <h5 className="mb-0">
                  <FaUpload className="me-2" />
                  Upload Logs for Analysis
                </h5>
              </Card.Header>
              <Card.Body>
                <div {...getRootProps()} className={`upload-area ${isDragActive ? 'active' : ''}`}>
                  <input {...getInputProps()} />
                  <FaUpload size={48} className="text-muted mb-3" />
                  <h5>Drop log files here for root cause analysis</h5>
                  <p className="text-muted">
                    Supports .log and .txt files up to 50MB<br/>
                    The AI will analyze patterns, correlate events, and identify root causes
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
                    onClick={performRCA}
                    disabled={loading || uploadedFiles.length === 0}
                  >
                    {loading ? (
                      <>
                        <Spinner animation="border" size="sm" className="me-2" />
                        Analyzing Root Causes...
                      </>
                    ) : (
                      <>
                        <FaBrain className="me-2" />
                        Start Root Cause Analysis
                      </>
                    )}
                  </Button>
                </div>
              </Card.Body>
            </Card>
          </Col>

          <Col lg={4}>
            <Card>
              <Card.Header>
                <h6 className="mb-0">Analysis Options</h6>
              </Card.Header>
              <Card.Body>
                <Form>
                  <Form.Group className="mb-3">
                    <Form.Check
                      type="checkbox"
                      label="Include contextual information"
                      checked={analysisOptions.includeContext}
                      onChange={(e) => setAnalysisOptions(prev => ({ 
                        ...prev, 
                        includeContext: e.target.checked 
                      }))}
                    />
                  </Form.Group>

                  <Form.Group className="mb-3">
                    <Form.Check
                      type="checkbox"
                      label="Provide detailed explanations"
                      checked={analysisOptions.detailedExplanation}
                      onChange={(e) => setAnalysisOptions(prev => ({ 
                        ...prev, 
                        detailedExplanation: e.target.checked 
                      }))}
                    />
                  </Form.Group>

                  <Form.Group className="mb-3">
                    <Form.Check
                      type="checkbox"
                      label="Suggest remediation actions"
                      checked={analysisOptions.suggestActions}
                      onChange={(e) => setAnalysisOptions(prev => ({ 
                        ...prev, 
                        suggestActions: e.target.checked 
                      }))}
                    />
                  </Form.Group>

                  <Form.Group className="mb-3">
                    <Form.Check
                      type="checkbox"
                      label="Correlate related events"
                      checked={analysisOptions.correlateEvents}
                      onChange={(e) => setAnalysisOptions(prev => ({ 
                        ...prev, 
                        correlateEvents: e.target.checked 
                      }))}
                    />
                  </Form.Group>
                </Form>

                <Alert variant="info" className="mt-3">
                  <small>
                    <strong>AI-Powered Analysis:</strong> Our system uses LogBERT and advanced NLP 
                    to understand log patterns, identify anomalies, and provide intelligent 
                    root cause explanations.
                  </small>
                </Alert>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      ) : (
        <div>
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h4>Analysis Results</h4>
            <Button 
              variant="outline-primary" 
              onClick={() => {
                setRcaResult(null);
                setUploadedFiles([]);
              }}
            >
              New Analysis
            </Button>
          </div>
          <RCAResults result={rcaResult} />
        </div>
      )}
    </div>
  );
};

export default RootCauseAnalysis;
