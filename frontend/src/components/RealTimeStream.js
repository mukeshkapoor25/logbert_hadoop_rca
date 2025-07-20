import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Row, Col, Card, Button, Alert, Form, Badge } from 'react-bootstrap';
import { FaStream, FaPlay, FaStop, FaTrash, FaDownload } from 'react-icons/fa';
import { toast } from 'react-toastify';
import { apiService } from '../services/apiService';

const RealTimeStream = ({ socket, isConnected }) => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamData, setStreamData] = useState([]);
  const [streamStats, setStreamStats] = useState({
    totalProcessed: 0,
    anomaliesDetected: 0,
    avgProcessingTime: 0,
    startTime: null
  });
  const [streamOptions, setStreamOptions] = useState({
    autoScroll: true,
    showTimestamps: true,
    maxLines: 1000,
    filterLevel: 'ALL'
  });
  const streamContainerRef = useRef(null);

  // Define callback functions first
  const handleStreamProgress = useCallback((data) => {
    setStreamStats(prev => ({
      ...prev,
      totalProcessed: data.totalProcessed || prev.totalProcessed,
      anomaliesDetected: data.anomaliesDetected || prev.anomaliesDetected,
      avgProcessingTime: data.avgProcessingTime || prev.avgProcessingTime
    }));
  }, []);

  const handleStreamComplete = useCallback((data) => {
    toast.success('Stream analysis completed');
    setIsStreaming(false);
    console.log('Stream complete:', data);
  }, []);

  const handleStreamError = useCallback((error) => {
    toast.error(`Stream error: ${error.message}`);
    setIsStreaming(false);
    console.error('Stream error:', error);
  }, []);

  const handleStreamData = useCallback((data) => {
    const newEntry = {
      id: Date.now() + Math.random(),
      timestamp: new Date().toISOString(),
      type: data.type || 'info',
      message: data.message,
      agent: data.agent,
      processingTime: data.processingTime,
      confidence: data.confidence,
      anomaly: data.anomaly
    };

    setStreamData(prev => {
      const updated = [...prev, newEntry];
      // Keep only the last maxLines entries
      if (updated.length > streamOptions.maxLines) {
        return updated.slice(-streamOptions.maxLines);
      }
      return updated;
    });
  }, [streamOptions.maxLines]);

  useEffect(() => {
    if (socket && isConnected) {
      // Subscribe to stream updates
      socket.on('stream_progress', handleStreamProgress);
      socket.on('stream_complete', handleStreamComplete);
      socket.on('stream_error', handleStreamError);
      socket.on('stream_data', handleStreamData);

      return () => {
        socket.off('stream_progress');
        socket.off('stream_complete');
        socket.off('stream_error');
        socket.off('stream_data');
      };
    }
  }, [socket, isConnected, handleStreamData, handleStreamProgress, handleStreamComplete, handleStreamError]);

  useEffect(() => {
    if (streamOptions.autoScroll && streamContainerRef.current) {
      streamContainerRef.current.scrollTop = streamContainerRef.current.scrollHeight;
    }
  }, [streamData, streamOptions.autoScroll]);

  const startStreaming = () => {
    if (!socket || !isConnected) {
      toast.error('WebSocket connection not available');
      return;
    }

    setIsStreaming(true);
    setStreamStats({
      totalProcessed: 0,
      anomaliesDetected: 0,
      avgProcessingTime: 0,
      startTime: new Date()
    });
    
    apiService.startStreamAnalysis(
      handleStreamProgress,
      handleStreamComplete,
      handleStreamError
    );
    
    toast.info('Started real-time stream analysis');
  };

  const stopStreaming = () => {
    setIsStreaming(false);
    apiService.stopStreamAnalysis();
    toast.info('Stopped real-time stream analysis');
  };

  const clearStream = () => {
    setStreamData([]);
    setStreamStats({
      totalProcessed: 0,
      anomaliesDetected: 0,
      avgProcessingTime: 0,
      startTime: null
    });
  };

  const exportStreamData = () => {
    const dataStr = JSON.stringify(streamData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `stream_data_${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const getEntryColor = (type) => {
    switch (type) {
      case 'anomaly': return 'danger';
      case 'warning': return 'warning';
      case 'error': return 'danger';
      case 'success': return 'success';
      default: return 'info';
    }
  };

  const filteredStreamData = streamData.filter(entry => {
    if (streamOptions.filterLevel === 'ALL') return true;
    return entry.type === streamOptions.filterLevel.toLowerCase();
  });

  return (
    <div>
      <Row className="mb-4">
        <Col>
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <h2>
                <FaStream className="me-2" />
                Real-Time Stream Analysis
              </h2>
              <p className="text-muted">
                Live log processing with AI agents pipeline
              </p>
            </div>
            <div>
              {!isStreaming ? (
                <Button
                  variant="success"
                  onClick={startStreaming}
                  disabled={!isConnected}
                >
                  <FaPlay className="me-2" />
                  Start Stream
                </Button>
              ) : (
                <Button
                  variant="danger"
                  onClick={stopStreaming}
                >
                  <FaStop className="me-2" />
                  Stop Stream
                </Button>
              )}
            </div>
          </div>
        </Col>
      </Row>

      {!isConnected && (
        <Alert variant="warning" className="mb-4">
          <strong>WebSocket Disconnected:</strong> Real-time streaming requires an active WebSocket connection.
          Please check your connection and refresh the page.
        </Alert>
      )}

      {/* Stream Statistics */}
      <Row className="mb-4">
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <h4 className="text-primary">{streamStats.totalProcessed}</h4>
              <small className="text-muted">Logs Processed</small>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <h4 className="text-warning">{streamStats.anomaliesDetected}</h4>
              <small className="text-muted">Anomalies Found</small>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <h4 className="text-info">{streamStats.avgProcessingTime}ms</h4>
              <small className="text-muted">Avg Processing Time</small>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <h4 className="text-success">
                {isStreaming ? (
                  <Badge bg="success" className="pulse">LIVE</Badge>
                ) : (
                  <Badge bg="secondary">STOPPED</Badge>
                )}
              </h4>
              <small className="text-muted">Stream Status</small>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row>
        {/* Stream Controls */}
        <Col lg={3}>
          <Card className="mb-4">
            <Card.Header>
              <h6 className="mb-0">Stream Controls</h6>
            </Card.Header>
            <Card.Body>
              <Form>
                <Form.Group className="mb-3">
                  <Form.Check
                    type="checkbox"
                    label="Auto-scroll"
                    checked={streamOptions.autoScroll}
                    onChange={(e) => setStreamOptions(prev => ({ 
                      ...prev, 
                      autoScroll: e.target.checked 
                    }))}
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Check
                    type="checkbox"
                    label="Show timestamps"
                    checked={streamOptions.showTimestamps}
                    onChange={(e) => setStreamOptions(prev => ({ 
                      ...prev, 
                      showTimestamps: e.target.checked 
                    }))}
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Filter Level</Form.Label>
                  <Form.Select
                    value={streamOptions.filterLevel}
                    onChange={(e) => setStreamOptions(prev => ({ 
                      ...prev, 
                      filterLevel: e.target.value 
                    }))}
                  >
                    <option value="ALL">All Messages</option>
                    <option value="ANOMALY">Anomalies Only</option>
                    <option value="ERROR">Errors Only</option>
                    <option value="WARNING">Warnings Only</option>
                    <option value="INFO">Info Only</option>
                  </Form.Select>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Max Lines</Form.Label>
                  <Form.Control
                    type="number"
                    value={streamOptions.maxLines}
                    onChange={(e) => setStreamOptions(prev => ({ 
                      ...prev, 
                      maxLines: parseInt(e.target.value) || 1000 
                    }))}
                    min="100"
                    max="5000"
                  />
                </Form.Group>
              </Form>

              <div className="d-grid gap-2">
                <Button
                  variant="outline-secondary"
                  size="sm"
                  onClick={clearStream}
                >
                  <FaTrash className="me-1" />
                  Clear Stream
                </Button>
                <Button
                  variant="outline-primary"
                  size="sm"
                  onClick={exportStreamData}
                  disabled={streamData.length === 0}
                >
                  <FaDownload className="me-1" />
                  Export Data
                </Button>
              </div>
            </Card.Body>
          </Card>
        </Col>

        {/* Stream Output */}
        <Col lg={9}>
          <Card>
            <Card.Header className="d-flex justify-content-between align-items-center">
              <h6 className="mb-0">
                Live Stream Output
                {isStreaming && <span className="status-indicator status-online ms-2"></span>}
              </h6>
              <Badge bg="secondary">
                {filteredStreamData.length} / {streamData.length} entries
              </Badge>
            </Card.Header>
            <Card.Body className="p-0">
              <div 
                ref={streamContainerRef}
                className="stream-container"
                style={{ 
                  height: '500px', 
                  overflowY: 'auto',
                  backgroundColor: '#1e1e1e',
                  color: '#d4d4d4',
                  fontFamily: 'monospace',
                  fontSize: '13px'
                }}
              >
                {filteredStreamData.length === 0 ? (
                  <div className="p-4 text-center text-muted">
                    {isStreaming ? 'Waiting for stream data...' : 'No stream data available. Start streaming to see live analysis.'}
                  </div>
                ) : (
                  <div className="p-2">
                    {filteredStreamData.map((entry) => (
                      <div key={entry.id} className="stream-entry mb-1 p-2 border-bottom border-dark">
                        <div className="d-flex justify-content-between align-items-start">
                          <div className="flex-grow-1">
                            {streamOptions.showTimestamps && (
                              <span className="text-muted me-2">
                                [{new Date(entry.timestamp).toLocaleTimeString()}]
                              </span>
                            )}
                            <Badge bg={getEntryColor(entry.type)} className="me-2">
                              {entry.type.toUpperCase()}
                            </Badge>
                            {entry.agent && (
                              <Badge bg="secondary" className="me-2">
                                {entry.agent}
                              </Badge>
                            )}
                            <span>{entry.message}</span>
                          </div>
                          <div className="text-end">
                            {entry.processingTime && (
                              <small className="text-muted">{entry.processingTime}ms</small>
                            )}
                            {entry.confidence && (
                              <div>
                                <small className="text-muted">
                                  Conf: {(entry.confidence * 100).toFixed(1)}%
                                </small>
                              </div>
                            )}
                          </div>
                        </div>
                        {entry.anomaly && (
                          <div className="mt-1 ps-3 border-start border-danger">
                            <small className="text-warning">
                              Anomaly: {entry.anomaly.description}
                            </small>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default RealTimeStream;
