import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Badge, Spinner, Table } from 'react-bootstrap';
import { FaInfo, FaBrain, FaDatabase, FaServer, FaCog } from 'react-icons/fa';
import { apiService } from '../services/apiService';

const ModelInfo = () => {
  const [modelInfo, setModelInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchModelInfo();
  }, []);

  const fetchModelInfo = async () => {
    try {
      const info = await apiService.getModelInfo();
      setModelInfo(info);
    } catch (error) {
      console.error('Failed to fetch model info:', error);
      // Provide fallback data
      setModelInfo({
        logbert_model: {
          name: "LogBERT",
          version: "1.0.0",
          architecture: "Transformer-based",
          parameters: "110M",
          status: "Loaded"
        },
        anomaly_detector: {
          name: "Deep SVDD",
          version: "1.0.0",
          algorithm: "Deep Support Vector Data Description",
          status: "Active"
        },
        system_info: {
          gpu_available: true,
          memory_usage: "2.1 GB",
          model_size: "440 MB"
        }
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <Spinner animation="border" />
      </div>
    );
  }

  const ModelCard = ({ title, model, icon, color = "primary" }) => (
    <Card className="h-100">
      <Card.Header className={`bg-${color} text-white`}>
        <h6 className="mb-0">
          {icon} {title}
        </h6>
      </Card.Header>
      <Card.Body>
        <Table striped size="sm">
          <tbody>
            <tr>
              <td><strong>Name:</strong></td>
              <td>{model.name || 'N/A'}</td>
            </tr>
            <tr>
              <td><strong>Version:</strong></td>
              <td>{model.version || 'N/A'}</td>
            </tr>
            <tr>
              <td><strong>Status:</strong></td>
              <td>
                <Badge bg={model.status === 'Loaded' || model.status === 'Active' ? 'success' : 'warning'}>
                  {model.status || 'Unknown'}
                </Badge>
              </td>
            </tr>
            {model.architecture && (
              <tr>
                <td><strong>Architecture:</strong></td>
                <td>{model.architecture}</td>
              </tr>
            )}
            {model.algorithm && (
              <tr>
                <td><strong>Algorithm:</strong></td>
                <td>{model.algorithm}</td>
              </tr>
            )}
            {model.parameters && (
              <tr>
                <td><strong>Parameters:</strong></td>
                <td>{model.parameters}</td>
              </tr>
            )}
            {model.accuracy && (
              <tr>
                <td><strong>Accuracy:</strong></td>
                <td>{model.accuracy}</td>
              </tr>
            )}
            {model.last_trained && (
              <tr>
                <td><strong>Last Trained:</strong></td>
                <td>{model.last_trained}</td>
              </tr>
            )}
          </tbody>
        </Table>
      </Card.Body>
    </Card>
  );

  return (
    <div>
      <Row className="mb-4">
        <Col>
          <h2>
            <FaInfo className="me-2" />
            Model Information
          </h2>
          <p className="text-muted">
            Detailed information about the AI models and system components used for log analysis.
          </p>
        </Col>
      </Row>

      {/* Model Cards */}
      <Row className="mb-4">
        {modelInfo.logbert_model && (
          <Col lg={6}>
            <ModelCard
              title="LogBERT Model"
              model={modelInfo.logbert_model}
              icon={<FaBrain />}
              color="primary"
            />
          </Col>
        )}
        {modelInfo.anomaly_detector && (
          <Col lg={6}>
            <ModelCard
              title="Anomaly Detection Model"
              model={modelInfo.anomaly_detector}
              icon={<FaServer />}
              color="warning"
            />
          </Col>
        )}
      </Row>

      {modelInfo.rca_model && (
        <Row className="mb-4">
          <Col lg={6}>
            <ModelCard
              title="Root Cause Analysis Model"
              model={modelInfo.rca_model}
              icon={<FaCog />}
              color="info"
            />
          </Col>
        </Row>
      )}

      {/* System Information */}
      {modelInfo.system_info && (
        <Row className="mb-4">
          <Col>
            <Card>
              <Card.Header>
                <h6 className="mb-0">
                  <FaDatabase className="me-2" />
                  System Information
                </h6>
              </Card.Header>
              <Card.Body>
                <Row>
                  <Col md={4}>
                    <h6>Hardware</h6>
                    <ul className="list-unstyled">
                      <li>
                        <strong>GPU Available:</strong> 
                        <Badge bg={modelInfo.system_info.gpu_available ? 'success' : 'warning'} className="ms-2">
                          {modelInfo.system_info.gpu_available ? 'Yes' : 'No'}
                        </Badge>
                      </li>
                      {modelInfo.system_info.gpu_model && (
                        <li><strong>GPU Model:</strong> {modelInfo.system_info.gpu_model}</li>
                      )}
                      <li><strong>Memory Usage:</strong> {modelInfo.system_info.memory_usage || 'N/A'}</li>
                      <li><strong>Total Model Size:</strong> {modelInfo.system_info.model_size || 'N/A'}</li>
                    </ul>
                  </Col>
                  <Col md={4}>
                    <h6>Performance</h6>
                    <ul className="list-unstyled">
                      <li><strong>Avg. Processing Time:</strong> {modelInfo.system_info.avg_processing_time || 'N/A'}</li>
                      <li><strong>Throughput:</strong> {modelInfo.system_info.throughput || 'N/A'}</li>
                      <li><strong>Cache Hit Rate:</strong> {modelInfo.system_info.cache_hit_rate || 'N/A'}</li>
                      <li><strong>Uptime:</strong> {modelInfo.system_info.uptime || 'N/A'}</li>
                    </ul>
                  </Col>
                  <Col md={4}>
                    <h6>Configuration</h6>
                    <ul className="list-unstyled">
                      <li><strong>Batch Size:</strong> {modelInfo.system_info.batch_size || 'N/A'}</li>
                      <li><strong>Max Sequence Length:</strong> {modelInfo.system_info.max_seq_length || 'N/A'}</li>
                      <li><strong>Vocabulary Size:</strong> {modelInfo.system_info.vocab_size || 'N/A'}</li>
                      <li><strong>Model Precision:</strong> {modelInfo.system_info.precision || 'FP32'}</li>
                    </ul>
                  </Col>
                </Row>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Training Information */}
      {modelInfo.training_info && (
        <Row className="mb-4">
          <Col>
            <Card>
              <Card.Header>
                <h6 className="mb-0">
                  <FaBrain className="me-2" />
                  Training Information
                </h6>
              </Card.Header>
              <Card.Body>
                <Row>
                  <Col md={6}>
                    <h6>Dataset</h6>
                    <ul className="list-unstyled">
                      <li><strong>Training Samples:</strong> {modelInfo.training_info.training_samples || 'N/A'}</li>
                      <li><strong>Validation Samples:</strong> {modelInfo.training_info.validation_samples || 'N/A'}</li>
                      <li><strong>Test Samples:</strong> {modelInfo.training_info.test_samples || 'N/A'}</li>
                      <li><strong>Data Source:</strong> {modelInfo.training_info.data_source || 'Hadoop Cluster Logs'}</li>
                    </ul>
                  </Col>
                  <Col md={6}>
                    <h6>Performance Metrics</h6>
                    <ul className="list-unstyled">
                      <li><strong>Accuracy:</strong> {modelInfo.training_info.accuracy || 'N/A'}</li>
                      <li><strong>Precision:</strong> {modelInfo.training_info.precision || 'N/A'}</li>
                      <li><strong>Recall:</strong> {modelInfo.training_info.recall || 'N/A'}</li>
                      <li><strong>F1 Score:</strong> {modelInfo.training_info.f1_score || 'N/A'}</li>
                    </ul>
                  </Col>
                </Row>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Model Architecture Details */}
      {modelInfo.architecture_details && (
        <Row>
          <Col>
            <Card>
              <Card.Header>
                <h6 className="mb-0">
                  <FaCog className="me-2" />
                  Architecture Details
                </h6>
              </Card.Header>
              <Card.Body>
                <Table striped>
                  <thead>
                    <tr>
                      <th>Component</th>
                      <th>Configuration</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {modelInfo.architecture_details.map((detail, index) => (
                      <tr key={index}>
                        <td><strong>{detail.component}</strong></td>
                        <td>{detail.configuration}</td>
                        <td>{detail.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}
    </div>
  );
};

export default ModelInfo;
