import React, { useState, useCallback } from 'react';
import { Row, Col, Card, Form, Button, Alert, Spinner, Badge, Tabs, Tab } from 'react-bootstrap';
import { useDropzone } from 'react-dropzone';
import { FaUpload, FaSearch, FaFileAlt, FaCog } from 'react-icons/fa';
import { toast } from 'react-toastify';
import { apiService } from '../services/apiService';

const LogAnalysis = () => {
  const [activeTab, setActiveTab] = useState('text');
  const [logText, setLogText] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  
  // Analysis options
  const [options, setOptions] = useState({
    includeTimestamp: true,
    parseLevel: 'INFO',
    maxLines: 1000,
    enablePreprocessing: true,
  });

  const onDrop = useCallback((acceptedFiles) => {
    setUploadedFiles(acceptedFiles);
    toast.success(`${acceptedFiles.length} file(s) uploaded successfully`);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.log', '.txt'],
      'application/octet-stream': ['.log']
    },
    maxFiles: 5,
    maxSize: 10 * 1024 * 1024 // 10MB
  });

  const analyzeText = async () => {
    if (!logText.trim()) {
      toast.error('Please enter some log content to analyze');
      return;
    }

    setLoading(true);
    try {
      const result = await apiService.analyzeLogText(logText, options);
      // Map mock/development response to UI expected structure if needed
      let mappedResult = result;
      if (result && result.anomaly_detection && result.root_cause_analysis) {
        mappedResult = {
          total_logs: result.anomaly_detection.statistics?.total_lines || 0,
          warnings: 0, // Not available in mock, set to 0 or count from anomalies if needed
          errors: result.anomaly_detection.total_anomalies || 0,
          processing_time: result.anomaly_detection.processing_time_ms + ' ms',
          parsed_logs: result.anomaly_detection.anomalies?.map(a => ({
            ...a,
            level: a.anomaly_type?.toUpperCase() || 'ERROR',
            message: a.log_entry,
            timestamp: a.timestamp,
          })) || [],
          summary: result.root_cause_analysis.analysis_summary || result.root_cause_analysis.root_causes?.[0]?.description,
          patterns: result.anomaly_detection.anomalies?.map(a => a.anomaly_type).filter((v, i, arr) => arr.indexOf(v) === i) || [],
          root_cause: result.root_cause_analysis.root_causes?.[0]?.title,
          recommended_actions: result.root_cause_analysis.root_causes?.[0]?.recommended_actions,
          mock_mode: result.anomaly_detection.statistics?.mock_mode,
        };
      }
      setAnalysisResult(mappedResult);
      toast.success('Log analysis completed successfully');
    } catch (error) {
      toast.error(`Analysis failed: ${error.message}`);
      console.error('Analysis error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Map backend response to UI format expected by AnalysisResults
  const mapAnalysisResult = (apiResult) => {
    if (!apiResult || !apiResult.results || !Array.isArray(apiResult.results) || apiResult.results.length === 0) {
      return {};
    }
    const fileResult = apiResult.results[0];
    return {
      total_logs: fileResult.size || 0,
      warnings: fileResult.anomalies_detected || 0,
      errors: fileResult.anomalies_detected || 0,
      processing_time: fileResult.analysis_time || apiResult.analysis_time || 'N/A',
      summary: fileResult.root_causes && fileResult.root_causes.length > 0
        ? `Root causes: ${fileResult.root_causes.join(', ')}`
        : 'No root causes detected.',
      patterns: fileResult.root_causes || [],
      parsed_logs: [], // Not available in backend response
    };
  };

  const analyzeFile = async () => {
    if (uploadedFiles.length === 0) {
      toast.error('Please upload a log file first');
      return;
    }

    setLoading(true);
    try {
      const result = await apiService.analyzeLogFile(uploadedFiles[0], options);
      const mappedResult = mapAnalysisResult(result);
      setAnalysisResult(mappedResult);
      toast.success('File analysis completed successfully');
    } catch (error) {
      toast.error(`File analysis failed: ${error.message}`);
      console.error('File analysis error:', error);
    } finally {
      setLoading(false);
    }
  };

  const LogViewer = ({ logs }) => (
    <div className="log-viewer">
      {logs.map((log, index) => (
        <div key={index} className={`log-line ${log.level?.toLowerCase() || ''}`}>
          {log.timestamp && <span className="text-muted">[{log.timestamp}] </span>}
          {log.level && <span className={`badge bg-${getLevelColor(log.level)} me-2`}>{log.level}</span>}
          <span>{log.message}</span>
        </div>
      ))}
    </div>
  );

  const getLevelColor = (level) => {
    switch (level?.toUpperCase()) {
      case 'ERROR': return 'danger';
      case 'WARN': case 'WARNING': return 'warning';
      case 'INFO': return 'info';
      case 'DEBUG': return 'secondary';
      default: return 'light';
    }
  };

  const AnalysisResults = ({ result }) => (
    <Card className="mt-4">
      <Card.Header>
        <h5 className="mb-0">
          <FaSearch className="me-2" />
          Analysis Results
        </h5>
      </Card.Header>
      <Card.Body>
        <Row className="mb-3">
          <Col md={3}>
            <Card className="text-center">
              <Card.Body>
                <h4 className="text-primary">{result.total_logs || 0}</h4>
                <small className="text-muted">Total Log Entries</small>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3}>
            <Card className="text-center">
              <Card.Body>
                <h4 className="text-warning">{result.warnings || 0}</h4>
                <small className="text-muted">Warnings</small>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3}>
            <Card className="text-center">
              <Card.Body>
                <h4 className="text-danger">{result.errors || 0}</h4>
                <small className="text-muted">Errors</small>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3}>
            <Card className="text-center">
              <Card.Body>
                <h4 className="text-success">{result.processing_time || 'N/A'}</h4>
                <small className="text-muted">Processing Time</small>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {result.parsed_logs && (
          <div>
            <h6>Parsed Log Entries:</h6>
            <LogViewer logs={result.parsed_logs.slice(0, 50)} />
            {result.parsed_logs.length > 50 && (
              <Alert variant="info" className="mt-2">
                Showing first 50 entries. Total: {result.parsed_logs.length} entries.
              </Alert>
            )}
          </div>
        )}

        {result.summary && (
          <div className="mt-4">
            <h6>Analysis Summary:</h6>
            <Alert variant="info">
              {result.summary}
            </Alert>
          </div>
        )}

        {result.patterns && result.patterns.length > 0 && (
          <div className="mt-4">
            <h6>Detected Patterns:</h6>
            {result.patterns.map((pattern, index) => (
              <Badge key={index} bg="secondary" className="me-2 mb-1">
                {pattern}
              </Badge>
            ))}
          </div>
        )}
      </Card.Body>
    </Card>
  );

  return (
    <div>
      <Row className="mb-4">
        <Col>
          <h2>
            <FaSearch className="me-2" />
            Log Analysis
          </h2>
          <p className="text-muted">
            Upload log files or paste log content for intelligent analysis using LogBERT AI models.
          </p>
        </Col>
      </Row>

      <Row>
        <Col lg={8}>
          <Card>
            <Card.Header>
              <Tabs activeKey={activeTab} onSelect={setActiveTab}>
                <Tab eventKey="text" title={<><FaFileAlt className="me-1" />Text Input</>} />
                <Tab eventKey="file" title={<><FaUpload className="me-1" />File Upload</>} />
              </Tabs>
            </Card.Header>
            <Card.Body>
              {activeTab === 'text' && (
                <div>
                  <Form.Group className="mb-3">
                    <Form.Label>Log Content</Form.Label>
                    <Form.Control
                      as="textarea"
                      rows={15}
                      placeholder="Paste your log content here..."
                      value={logText}
                      onChange={(e) => setLogText(e.target.value)}
                      style={{ fontFamily: 'monospace', fontSize: '14px' }}
                    />
                  </Form.Group>
                  <Button 
                    variant="primary" 
                    onClick={analyzeText}
                    disabled={loading || !logText.trim()}
                  >
                    {loading ? (
                      <>
                        <Spinner animation="border" size="sm" className="me-2" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <FaSearch className="me-2" />
                        Analyze Text
                      </>
                    )}
                  </Button>
                </div>
              )}

              {activeTab === 'file' && (
                <div>
                  <div {...getRootProps()} className={`upload-area ${isDragActive ? 'active' : ''}`}>
                    <input {...getInputProps()} />
                    <FaUpload size={48} className="text-muted mb-3" />
                    <h5>Drop log files here, or click to select</h5>
                    <p className="text-muted">
                      Supports .log and .txt files up to 10MB each
                    </p>
                    {uploadedFiles.length > 0 && (
                      <Alert variant="success" className="mt-3">
                        <strong>Files ready for analysis:</strong>
                        <ul className="mb-0 mt-2">
                          {uploadedFiles.map((file, index) => (
                            <li key={index}>{file.name} ({(file.size / 1024).toFixed(1)} KB)</li>
                          ))}
                        </ul>
                      </Alert>
                    )}
                  </div>
                  
                  <Button 
                    variant="primary" 
                    onClick={analyzeFile}
                    disabled={loading || uploadedFiles.length === 0}
                    className="mt-3"
                  >
                    {loading ? (
                      <>
                        <Spinner animation="border" size="sm" className="me-2" />
                        Processing File...
                      </>
                    ) : (
                      <>
                        <FaSearch className="me-2" />
                        Analyze File
                      </>
                    )}
                  </Button>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>

        <Col lg={4}>
          <Card>
            <Card.Header>
              <h6 className="mb-0">
                <FaCog className="me-2" />
                Analysis Options
              </h6>
            </Card.Header>
            <Card.Body>
              <Form>
                <Form.Group className="mb-3">
                  <Form.Check
                    type="checkbox"
                    label="Include timestamp parsing"
                    checked={options.includeTimestamp}
                    onChange={(e) => setOptions(prev => ({ ...prev, includeTimestamp: e.target.checked }))}
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Check
                    type="checkbox"
                    label="Enable preprocessing"
                    checked={options.enablePreprocessing}
                    onChange={(e) => setOptions(prev => ({ ...prev, enablePreprocessing: e.target.checked }))}
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Log Level Filter</Form.Label>
                  <Form.Select
                    value={options.parseLevel}
                    onChange={(e) => setOptions(prev => ({ ...prev, parseLevel: e.target.value }))}
                  >
                    <option value="DEBUG">DEBUG and above</option>
                    <option value="INFO">INFO and above</option>
                    <option value="WARN">WARN and above</option>
                    <option value="ERROR">ERROR only</option>
                  </Form.Select>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Max Lines to Process</Form.Label>
                  <Form.Control
                    type="number"
                    value={options.maxLines}
                    onChange={(e) => setOptions(prev => ({ ...prev, maxLines: parseInt(e.target.value) || 1000 }))}
                    min="100"
                    max="10000"
                  />
                </Form.Group>
              </Form>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {analysisResult && <AnalysisResults result={analysisResult} />}
    </div>
  );
};

export default LogAnalysis;
