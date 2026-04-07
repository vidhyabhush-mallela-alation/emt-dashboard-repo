# EMT Dashboard - Claude-Powered Test Intelligence

A comprehensive dashboard for monitoring Alation EMT (Engineering, Methodology & Testing) tickets with intelligent analysis powered by Claude skills.

## 🎯 Core Skills Integration

This repository is built around two powerful Claude skills:

### 1. 🧪 Regression Testing Skill
**Purpose**: Automated triggering and monitoring of Alation lineage certification test suites

**Capabilities**:
- Trigger all 6 lineage certification test suites
- Monitor Jenkins builds via MCP integration
- Handle different clusters (qa-enterprise-use1, qa-enterprise-use2)
- Manage manifest versions and parameters
- Parse test results and failure patterns

**Test Suites Managed**:
- Selenium QLI (Gauge framework)
- Tavern API Tests (Static & Provisioned DS)
- Playwright Connectors (Snowflake & Databricks)
- GitHub Actions E2E

### 2. 🔍 Atlassian Context Enricher Skill
**Purpose**: Systematic multi-dimensional analysis of Alation customer issues via Jira & Confluence

**Analysis Framework**:
- **7-dimensional search methodology** across Alation's Atlassian instance
- **Technical term expansion** for comprehensive issue investigation
- **Cross-platform deep dive** (Jira + Confluence integration)
- **Temporal pattern analysis** for issue evolution tracking
- **People network analysis** for expertise mapping
- **Customer impact assessment** for business priority
- **System layer correlation** for technical interconnections
- **Pattern recognition** for systemic vs isolated issues

## 🏗 Architecture

```
emt-dashboard-repo/
├── src/
│   ├── dashboard/          # Web dashboard (Python + HTML/JS)
│   ├── skills/             # Skill implementations
│   ├── integrations/       # MCP and external API integrations
│   └── analytics/          # Claude-powered analysis engine
├── skills/
│   ├── regression-testing/ # Regression testing skill
│   └── atlassian-context/  # Atlassian analysis skill
├── config/
│   ├── jenkins.yaml        # Jenkins job configurations
│   ├── atlassian.yaml      # Atlassian connection settings
│   └── dashboard.yaml      # Dashboard configuration
├── static/
│   ├── css/               # Dashboard styling
│   ├── js/                # Frontend JavaScript
│   └── assets/            # Images, icons, etc.
├── docs/
│   ├── skills/            # Skill documentation
│   ├── api/               # API documentation
│   └── deployment/        # Deployment guides
└── tests/
    ├── unit/              # Unit tests
    ├── integration/       # Integration tests
    └── e2e/               # End-to-end tests
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Claude MCP server access
- Jenkins API access (jenkins.alation-labs.com)
- Atlassian API access (alationcorp.atlassian.net)

### Installation
```bash
# Clone and setup
git clone <repo-url> emt-dashboard
cd emt-dashboard

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp config/example.env .env
# Edit .env with your credentials

# Start dashboard
python src/dashboard/app.py
```

### Access
- **Dashboard**: http://localhost:8080
- **API**: http://localhost:8080/api/v1/
- **WebSocket**: ws://localhost:8080/ws

## 🎛 Dashboard Features

### Real-Time Monitoring
- Live test status updates via WebSocket
- Interactive timeline with filterable events
- Progress tracking with visual indicators
- Connection status and health monitoring

### Intelligent Analysis
- **Regression Analysis**: Claude-powered test failure investigation
- **Issue Context**: Deep Atlassian analysis for customer escalations
- **Pattern Detection**: Cross-system failure correlation
- **Root Cause Analysis**: Multi-dimensional problem investigation

### Interactive Controls
- One-click test retriggering
- Cluster switching for performance testing
- Custom manifest deployment
- Real-time log streaming

### Comprehensive Reporting
- Test certification summaries
- Failure trend analysis
- Customer impact assessment
- Actionable recommendations

## 🔧 Configuration

### Environment Variables
```bash
# Jenkins Integration
JENKINS_URL=https://jenkins.alation-labs.com
JENKINS_USER=your.email@alation.com
JENKINS_API_TOKEN=your_jenkins_token

# Atlassian Integration
ATLASSIAN_URL=https://alationcorp.atlassian.net
ATLASSIAN_USER=your.email@alation.com
ATLASSIAN_API_TOKEN=your_atlassian_token

# Claude MCP
CLAUDE_MCP_SERVER=localhost:3001
CLAUDE_API_KEY=your_claude_key

# Dashboard
DASHBOARD_PORT=8080
DATABASE_URL=sqlite:///data/dashboard.db
LOG_LEVEL=INFO
```

### Skill Configuration
Skills are configured via YAML files in the `config/` directory:

```yaml
# config/regression-testing.yaml
clusters:
  - qa-enterprise-use1
  - qa-enterprise-use2
  
test_suites:
  selenium_qli:
    job_path: "alation_selenium/master/test_selenium_zeus"
    expected_tests: 4
    timeout_minutes: 120
  
  playwright_snowflake:
    job_path: "datasources/master/playwright_connector/zeus/test_release_zeus_static_ds"
    expected_tests: 127
    timeout_minutes: 180
```

## 📊 API Documentation

### Test Management
```http
GET    /api/v1/tests                    # List all tests
POST   /api/v1/tests/{suite}/trigger    # Trigger test suite
GET    /api/v1/tests/{id}/status        # Get test status
GET    /api/v1/tests/{id}/results       # Get test results
POST   /api/v1/tests/{id}/analyze       # Analyze failures
```

### Issue Analysis
```http
POST   /api/v1/analyze/issue            # Analyze Atlassian issue
GET    /api/v1/analyze/{id}/report      # Get analysis report
POST   /api/v1/analyze/correlation      # Cross-issue correlation
GET    /api/v1/analyze/patterns         # Pattern detection
```

### Dashboard Data
```http
GET    /api/v1/dashboard/overview       # Dashboard overview
GET    /api/v1/dashboard/timeline       # Event timeline
WS     /ws/updates                      # Real-time updates
```

## 🧠 Claude Skills Integration

### Skill Execution Flow

1. **Trigger Event** → Dashboard receives test failure or issue escalation
2. **Skill Selection** → Appropriate skill chosen based on context
3. **Analysis Execution** → Claude executes skill with MCP tools
4. **Result Processing** → Results parsed and integrated into dashboard
5. **Action Generation** → Actionable recommendations surfaced to user

### Skill Interfaces

```python
# Regression Testing Skill Interface
class RegressionTestingSkill:
    async def trigger_certification_suite(self, manifest: str, cluster: str) -> TestRun
    async def analyze_failure_patterns(self, test_results: List[TestResult]) -> Analysis
    async def recommend_actions(self, failures: List[Failure]) -> List[Action]

# Atlassian Context Enricher Interface  
class AtlassianContextSkill:
    async def analyze_issue(self, issue_key: str) -> IssueAnalysis
    async def search_related_content(self, search_terms: List[str]) -> SearchResults
    async def map_customer_impact(self, issue: Issue) -> CustomerImpact
```

## 🔍 Use Cases

### EMT Ticket Monitoring
```bash
# Monitor EMT-224570 lineage certification
curl -X POST /api/v1/tests/lineage-certification/trigger \
  -d '{"manifest": "26.4.0.0-alation-1.87.1-...", "cluster": "qa-enterprise-use2"}'

# Get real-time status
wscat -c ws://localhost:8080/ws
```

### Customer Escalation Analysis
```bash
# Deep analysis of customer issue
curl -X POST /api/v1/analyze/issue \
  -d '{"issue_key": "SUPPORT-12345", "analysis_depth": "comprehensive"}'

# Get cross-system correlation
curl /api/v1/analyze/correlation?issues=SUPPORT-12345,AL-98765
```

## 🚦 Monitoring & Alerting

### Health Checks
- `/health` - Basic health check
- `/health/detailed` - Comprehensive system status
- `/metrics` - Prometheus metrics endpoint

### Alerting Rules
- Test failure rate > 20%
- Analysis response time > 30s
- MCP connection failures
- Critical customer escalations

## 🔐 Security

### Authentication
- JWT-based API authentication
- Role-based access control (RBAC)
- Atlassian OAuth integration
- Jenkins API token management

### Data Protection
- Sensitive data encryption at rest
- Secure credential storage
- Audit logging for all actions
- Rate limiting and request validation

## 📈 Metrics & Analytics

### Key Metrics
- Test success rates by suite and cluster
- Mean time to failure resolution (MTTR)
- Customer issue resolution time
- Skill execution performance
- System resource utilization

### Dashboards
- Executive summary (high-level KPIs)
- Engineering metrics (detailed test data)
- Customer success (escalation trends)
- System health (infrastructure metrics)

## 🛠 Development

### Setup Development Environment
```bash
# Clone repository
git clone <repo-url> emt-dashboard
cd emt-dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install

# Run tests
pytest

# Start development server
python src/dashboard/app.py --debug
```

### Contributing
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📚 Documentation

- [Skill Documentation](docs/skills/) - Detailed skill capabilities and usage
- [API Reference](docs/api/) - Complete API documentation
- [Deployment Guide](docs/deployment/) - Production deployment instructions
- [Architecture Guide](docs/architecture/) - System design and components

## 🤝 Support

### Getting Help
- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for questions and ideas
- **Documentation**: Comprehensive docs in `/docs` directory
- **Examples**: Sample configurations and usage patterns

### Contributing
We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

**Built with ❤️ by the Alation Engineering Team**

*Powered by Claude Skills for intelligent automation and analysis*