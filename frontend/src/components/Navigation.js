import React from 'react';
import { Navbar, Nav, Container, Badge, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { LinkContainer } from 'react-router-bootstrap';
import { FaRobot, FaChartLine, FaCogs, FaStream, FaServer, FaHome } from 'react-icons/fa';

const Navigation = ({ isConnected = false, agentsStatus = {} }) => {
  const getAgentCount = (status) => {
    if (!agentsStatus || !agentsStatus.agents) return 0;
    return Object.values(agentsStatus.agents).filter(agent => agent.status === status).length;
  };

  const activeAgents = getAgentCount('active');
  const totalAgents = Object.keys(agentsStatus.agents || {}).length;

  const renderTooltip = (text) => (
    <Tooltip id="tooltip">{text}</Tooltip>
  );

  return (
    <Navbar bg="dark" variant="dark" expand="lg" sticky="top">
      <Container>
        <LinkContainer to="/">
          <Navbar.Brand>
            <FaRobot className="me-2" />
            LogBERT AI Agents
            <Badge 
              bg={isConnected ? "success" : "danger"} 
              className="ms-2"
            >
              {isConnected ? "Online" : "Offline"}
            </Badge>
            {totalAgents > 0 && (
              <Badge 
                bg={activeAgents === totalAgents ? "success" : activeAgents > 0 ? "warning" : "danger"} 
                className="ms-1"
              >
                {activeAgents}/{totalAgents} Agents
              </Badge>
            )}
          </Navbar.Brand>
        </LinkContainer>
        
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="ms-auto">
            <OverlayTrigger placement="bottom" overlay={renderTooltip("Dashboard - Real-time agent monitoring")}>
              <LinkContainer to="/">
                <Nav.Link>
                  <FaHome className="me-1" />
                  Dashboard
                </Nav.Link>
              </LinkContainer>
            </OverlayTrigger>
            
            <OverlayTrigger placement="bottom" overlay={renderTooltip("Log Analysis - AI-powered log processing")}>
              <LinkContainer to="/analyze">
                <Nav.Link>
                  <FaChartLine className="me-1" />
                  Log Analysis
                </Nav.Link>
              </LinkContainer>
            </OverlayTrigger>
            
            <OverlayTrigger placement="bottom" overlay={renderTooltip("Agents Management - Control AI agents")}>
              <LinkContainer to="/agents">
                <Nav.Link>
                  <FaCogs className="me-1" />
                  AI Agents
                  {totalAgents > 0 && (
                    <Badge bg="secondary" className="ms-1" style={{ fontSize: '0.7em' }}>
                      {activeAgents}
                    </Badge>
                  )}
                </Nav.Link>
              </LinkContainer>
            </OverlayTrigger>
            
            <OverlayTrigger placement="bottom" overlay={renderTooltip("Real-time Stream - Live log processing")}>
              <LinkContainer to="/stream">
                <Nav.Link>
                  <FaStream className="me-1" />
                  Live Stream
                  {isConnected && (
                    <span className="status-indicator status-online ms-1"></span>
                  )}
                </Nav.Link>
              </LinkContainer>
            </OverlayTrigger>
            
            <OverlayTrigger placement="bottom" overlay={renderTooltip("System Health - Monitor system status")}>
              <LinkContainer to="/health">
                <Nav.Link>
                  <FaServer className="me-1" />
                  System Health
                </Nav.Link>
              </LinkContainer>
            </OverlayTrigger>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default Navigation;
