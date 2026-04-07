# EMT Dashboard - QLI & Parser Image Deployment Automation

## Overview

This repository provides automated deployment and regression testing capabilities for **Alation QLI (Query Log Ingestion) and Parser images**. The system integrates Claude-powered intelligence with automated testing workflows to ensure reliable deployments.

## Quick Start for QLI & Parser Image Deployment

When you start working with new QLI or parser images:

### 1. Launch the Dashboard
```bash
cd /Users/vidhyabhushanm/Desktop/emt-dashboard-repo
python src/dashboard/app.py
```
**Dashboard URL:** http://localhost:8080

### 2. QLI & Parser Image Workflow

The dashboard automatically assists with:

1. **Image Tag Analysis** - Extract release notes and metadata from image tags
2. **Regression Test Triggering** - Automated test suite execution for QLI/Parser changes
3. **Failure Analysis** - Intelligent analysis of test failures using Atlassian context
4. **Deployment Validation** - Comprehensive validation workflows

## QLI & Parser Specific Operations

### Image Tag Release Notes Extraction

Use the `/release-notes-from-image-tags` tooling to automatically:
- Parse Docker image tags for version information
- Extract release notes from Git commits and Jira tickets
- Generate deployment summaries
- Validate image readiness for testing

### Automated Regression Testing

**QLI Image Testing:**
- Tavern API tests for QLI endpoints
- Connector-specific ingestion validation
- Performance regression detection
- Data quality validation

**Parser Image Testing:**
- GSP parser validation across database types
- Metadata extraction accuracy tests
- SQL parsing regression tests
- Cross-connector compatibility validation

## Integration with Existing Skills

### 1. Regression Testing Skill
- **Location:** `skills/regression-testing/skill.py`
- **QLI Focus:** Specialized test suites for QLI regression
- **Parser Focus:** Parser-specific validation workflows

### 2. Atlassian Context Enricher
- **Location:** `skills/atlassian-context-enricher/skill.py`
- **QLI Analysis:** Deep analysis of QLI-related issues and patterns
- **Parser Analysis:** Parser failure pattern recognition and correlation

## Dashboard Features for QLI & Parser Operations

### Real-time Monitoring
- QLI ingestion rate monitoring
- Parser success/failure rates
- Performance trend analysis
- Alert generation for regressions

### Intelligent Analysis
- Automatic correlation of image changes to test failures
- Historical pattern recognition for QLI/Parser issues
- Cross-database compatibility analysis
- Performance regression identification

## Workflow Integration

### New QLI Image Deployment
1. **Image Analysis** - Extract release info from tags
2. **Pre-deployment Validation** - Static analysis and compatibility checks
3. **Regression Testing** - Comprehensive test suite execution
4. **Performance Validation** - Ingestion rate and latency testing
5. **Deployment Decision** - Automated go/no-go recommendation

### New Parser Image Deployment
1. **Parser Validation** - SQL parsing accuracy tests across database types
2. **Metadata Extraction** - Validation of metadata accuracy and completeness
3. **Cross-connector Testing** - Compatibility validation with all supported databases
4. **Performance Testing** - Parser performance regression detection
5. **Integration Testing** - End-to-end workflow validation

## Configuration

### Jenkins MCP Integration
Configure via dashboard UI:
- Jenkins server credentials
- Job templates for QLI/Parser testing
- Test result parsing and analysis

### Atlassian Integration
Configure via dashboard UI:
- Jira API credentials for issue analysis
- Confluence integration for documentation searches
- Automated ticket updates with test results

## Commands and Shortcuts

### Quick Actions via Dashboard
- **🚀 Deploy QLI Image** - Full deployment workflow
- **🔍 Analyze Parser Issue** - Deep issue investigation
- **⚡ Run QLI Regression** - Fast QLI validation
- **📊 Image Comparison** - Compare image performance

### CLI Integration
```bash
# Extract release notes from image tag
python release-notes-from-image-tags/extract.py <image_tag>

# Trigger QLI regression tests
python -c "from skills.regression_testing.skill import RegressionTestingSkill; RegressionTestingSkill().trigger_qli_regression('<image_tag>')"

# Analyze parser failures
python -c "from skills.atlassian_context_enricher.skill import AtlassianContextEnricher; AtlassianContextEnricher().analyze_parser_failures('<issue_key>')"
```

## Monitoring and Alerting

### Automated Monitoring
- Continuous QLI ingestion rate tracking
- Parser success rate monitoring
- Performance regression detection
- Cross-database compatibility monitoring

### Alert Generation
- Performance degradation alerts
- Test failure notifications
- Deployment readiness notifications
- Issue correlation alerts

## Best Practices

### QLI Image Deployment
1. Always validate ingestion rates before production deployment
2. Run cross-connector regression tests for major changes
3. Monitor performance for 24 hours post-deployment
4. Maintain rollback capability for critical issues

### Parser Image Deployment
1. Validate SQL parsing accuracy across all supported databases
2. Test metadata extraction completeness
3. Verify cross-connector compatibility
4. Monitor parser performance metrics

### Issue Investigation
1. Use Atlassian context enricher for comprehensive analysis
2. Correlate image changes with failure patterns
3. Check historical data for similar issues
4. Engage appropriate teams based on analysis results

## Dashboard Navigation

### Main Sections
- **🧪 Regression Testing** - QLI/Parser test management
- **🔍 Issue Analysis** - Intelligent failure investigation  
- **📊 Activity Timeline** - Historical view of deployments and tests
- **🚀 Quick Actions** - One-click deployment and testing workflows

### QLI & Parser Specific Views
- **Image Management** - Track image versions and deployment status
- **Performance Trends** - Monitor QLI/Parser performance over time
- **Failure Analysis** - Deep dive into test failures and patterns
- **Release Planning** - Coordinate image deployments with test schedules

## Getting Help

### Dashboard Help
- Built-in help system accessible via **?** button
- Contextual tooltips on all major features
- Quick reference guides in each section

### Troubleshooting
- Check `/logs/dashboard.log` for application issues
- Monitor WebSocket connections for real-time update issues
- Verify Jenkins MCP server connectivity
- Validate Atlassian API credentials

### Support Resources
- **README.md** - Complete repository documentation
- **config/** - All configuration file examples
- **skills/** - Detailed skill documentation
- GitHub Issues - Bug reports and feature requests

## Advanced Features

### Machine Learning Integration (Future)
- Predictive failure analysis based on image changes
- Automated test suite optimization
- Performance regression prediction
- Intelligent test case selection

### Cross-team Collaboration
- Shared dashboards for multiple teams
- Automated stakeholder notifications
- Integration with team communication tools
- Collaborative failure investigation workflows

---

**🎯 Goal:** Provide seamless, intelligent automation for QLI and Parser image deployments with comprehensive regression testing and failure analysis capabilities.

**🔧 Architecture:** Claude skills-powered backend with real-time web dashboard for optimal user experience and automated decision-making support.