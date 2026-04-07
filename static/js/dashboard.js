/**
 * EMT Dashboard JavaScript
 * Frontend for Claude Skills-powered EMT monitoring
 */

class EMTDashboard {
    constructor(config) {
        this.apiBase = config.apiBase || '';
        this.wsUrl = config.wsUrl;
        this.autoRefreshInterval = config.autoRefreshInterval || 30000;

        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;

        this.data = {
            testRuns: [],
            analyses: [],
            timeline: [],
            overview: {}
        };

        this.init();
    }

    init() {
        console.log('Initializing EMT Dashboard');

        this.setupEventListeners();
        this.connectWebSocket();
        this.loadInitialData();

        // Start auto-refresh fallback
        setInterval(() => {
            if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
                this.loadInitialData();
            }
        }, this.autoRefreshInterval);
    }

    setupEventListeners() {
        // Modal close events
        window.addEventListener('click', (event) => {
            if (event.target.classList.contains('modal')) {
                this.closeModal(event.target.id);
            }
        });

        // Form submit events
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                this.closeAllModals();
            }
        });
    }

    // WebSocket Management
    connectWebSocket() {
        if (!this.wsUrl) {
            console.warn('WebSocket URL not configured, using polling only');
            return;
        }

        this.updateConnectionStatus('connecting', '🔌 Connecting...');

        try {
            this.ws = new WebSocket(this.wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus('connected', '🟢 Live');
                this.reconnectAttempts = 0;

                // Subscribe to updates
                this.ws.send(JSON.stringify({
                    type: 'subscribe_updates'
                }));
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (e) {
                    console.error('Failed to parse WebSocket message:', e);
                }
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus('disconnected', '🔴 Disconnected');

                // Attempt to reconnect
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    setTimeout(() => {
                        this.reconnectAttempts++;
                        this.connectWebSocket();
                    }, 5000 + (this.reconnectAttempts * 2000)); // Exponential backoff
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('disconnected', '🔴 Error');
            };

        } catch (e) {
            console.error('Failed to create WebSocket:', e);
            this.updateConnectionStatus('disconnected', '🔴 Failed');
        }
    }

    updateConnectionStatus(status, text) {
        const statusEl = document.getElementById('connectionStatus');
        if (statusEl) {
            statusEl.className = `connection-status ${status}`;
            statusEl.textContent = text;
        }
    }

    handleWebSocketMessage(data) {
        console.log('WebSocket message:', data);

        switch (data.type) {
            case 'status_update':
                this.data.testRuns = data.test_runs || this.data.testRuns;
                this.data.overview = data.overview || this.data.overview;
                this.renderAll();
                break;

            case 'test_suite_triggered':
                this.showToast('success', 'Tests Triggered', `${data.suite_count} test suites started`);
                this.loadTestData();
                break;

            case 'analysis_completed':
                this.showToast('success', 'Analysis Complete',
                    `Issue ${data.issue_key} analyzed with ${(data.confidence * 100).toFixed(0)}% confidence`);
                this.loadAnalysisData();
                break;

            case 'periodic_update':
                this.updateOverviewCards(data.status);
                this.updateLastUpdateTime();
                break;

            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }

    // Data Loading
    async loadInitialData() {
        try {
            await Promise.all([
                this.loadOverviewData(),
                this.loadTestData(),
                this.loadAnalysisData(),
                this.loadTimelineData()
            ]);

            this.renderAll();
            this.updateLastUpdateTime();

        } catch (e) {
            console.error('Failed to load initial data:', e);
            this.showToast('error', 'Loading Error', 'Failed to load dashboard data');
        }
    }

    async loadOverviewData() {
        try {
            const response = await fetch(`${this.apiBase}/api/v1/dashboard/overview`);
            if (response.ok) {
                this.data.overview = await response.json();
            }
        } catch (e) {
            console.error('Failed to load overview:', e);
        }
    }

    async loadTestData() {
        try {
            const response = await fetch(`${this.apiBase}/api/v1/tests`);
            if (response.ok) {
                this.data.testRuns = await response.json();
            }
        } catch (e) {
            console.error('Failed to load test data:', e);
        }
    }

    async loadAnalysisData() {
        try {
            // This would load issue analyses - placeholder for now
            this.data.analyses = [];
        } catch (e) {
            console.error('Failed to load analysis data:', e);
        }
    }

    async loadTimelineData() {
        try {
            const response = await fetch(`${this.apiBase}/api/v1/dashboard/timeline?limit=20`);
            if (response.ok) {
                this.data.timeline = await response.json();
            }
        } catch (e) {
            console.error('Failed to load timeline:', e);
        }
    }

    // Rendering Methods
    renderAll() {
        this.renderOverviewCards();
        this.renderTestSuites();
        this.renderIssueAnalyses();
        this.renderTimeline();
    }

    renderOverviewCards() {
        if (!this.data.overview.test_summary) return;

        const testSummary = this.data.overview.test_summary;
        const analysisSummary = this.data.overview.analysis_summary || {};

        document.getElementById('activeTestsCount').textContent =
            testSummary.active_runs || 0;

        document.getElementById('activeAnalysesCount').textContent =
            analysisSummary.active_analyses || 0;

        // Calculate success rate
        const statusBreakdown = testSummary.status_breakdown || {};
        const totalTests = testSummary.total_runs || 1;
        const successTests = statusBreakdown.success || 0;
        const successRate = Math.round((successTests / totalTests) * 100);

        const successRateEl = document.getElementById('successRate');
        successRateEl.textContent = `${successRate}%`;
        successRateEl.className = successRate >= 80 ? 'card-number success' :
                                 successRate >= 60 ? 'card-number warning' : 'card-number error';

        // Confidence score
        const confidenceScore = Math.round((analysisSummary.average_confidence || 0) * 100);
        const confidenceEl = document.getElementById('confidenceScore');
        confidenceEl.textContent = `${confidenceScore}%`;
        confidenceEl.className = confidenceScore >= 80 ? 'card-number success' :
                                confidenceScore >= 60 ? 'card-number warning' : 'card-number error';
    }

    renderTestSuites() {
        const container = document.getElementById('testSuitesList');
        if (!container) return;

        if (!this.data.testRuns || this.data.testRuns.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🧪</div>
                    <div class="empty-title">No Active Test Runs</div>
                    <div class="empty-description">Trigger a certification suite to begin monitoring</div>
                </div>
            `;
            return;
        }

        const testSuitesHtml = this.data.testRuns.map(test => {
            const progressPercent = test.total > 0 ? ((test.passed + test.failed) / test.total * 100) : 0;
            const statusClass = this.getStatusClass(test.status);

            return `
                <div class="test-suite ${statusClass}">
                    <div class="test-suite-header">
                        <div class="test-suite-name">${test.suite_id.replace(/_/g, ' ').toUpperCase()}</div>
                        <div class="test-suite-status ${statusClass}">${test.status}</div>
                    </div>

                    <div class="test-suite-meta">
                        Build #${test.build_number} | ${test.cluster} | Started: ${this.formatTime(test.started_at)}
                    </div>

                    <div class="test-suite-progress">
                        <div class="progress-bar">
                            <div class="progress-fill ${statusClass}" style="width: ${progressPercent}%"></div>
                        </div>
                    </div>

                    <div class="test-suite-stats">
                        <div class="stat-item">
                            <div class="stat-number success">${test.passed}</div>
                            <div class="stat-label">Passed</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number error">${test.failed}</div>
                            <div class="stat-label">Failed</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">${test.skipped}</div>
                            <div class="stat-label">Skipped</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">${test.total}</div>
                            <div class="stat-label">Total</div>
                        </div>
                    </div>

                    <div class="test-suite-actions">
                        <a href="${test.url}" target="_blank" class="action-link">🔗 View Build</a>
                        <button class="action-link analyze" onclick="analyzeTestFailures('${test.id}')">
                            🔍 Analyze
                        </button>
                        <button class="action-link retrigger" onclick="retriggerTest('${test.suite_id}')">
                            🔄 Retrigger
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = testSuitesHtml;
    }

    renderIssueAnalyses() {
        const container = document.getElementById('issueAnalysesList');
        if (!container) return;

        if (!this.data.analyses || this.data.analyses.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🔍</div>
                    <div class="empty-title">No Issue Analyses</div>
                    <div class="empty-description">Start an EMT issue analysis to see results</div>
                </div>
            `;
            return;
        }

        const analysesHtml = this.data.analyses.map(analysis => {
            const confidenceClass = this.getConfidenceClass(analysis.confidence_score);

            return `
                <div class="issue-analysis">
                    <div class="analysis-header">
                        <div>
                            <div class="analysis-title">${analysis.issue_key}</div>
                            <div class="analysis-meta">
                                ${analysis.issue_type} | Priority: ${analysis.priority}
                            </div>
                        </div>
                        <div class="confidence-badge ${confidenceClass}">
                            ${Math.round(analysis.confidence_score * 100)}%
                        </div>
                    </div>

                    <div class="analysis-summary">
                        ${analysis.analysis_summary.substring(0, 200)}...
                    </div>

                    <div class="test-suite-actions">
                        <button class="action-link" onclick="viewAnalysisReport('${analysis.id}')">
                            📊 Full Report
                        </button>
                        <button class="action-link analyze" onclick="viewRecommendations('${analysis.id}')">
                            💡 Recommendations
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = analysesHtml;
    }

    renderTimeline() {
        const container = document.getElementById('timelineContainer');
        if (!container) return;

        if (!this.data.timeline || this.data.timeline.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📊</div>
                    <div class="empty-title">No Timeline Events</div>
                    <div class="empty-description">Activity will appear here as tests run and analyses complete</div>
                </div>
            `;
            return;
        }

        const timelineHtml = this.data.timeline.map((event, index) => {
            const iconClass = this.getEventIconClass(event.event_type);

            return `
                <div class="timeline-item ${index === 0 ? 'new' : ''}">
                    <div class="timeline-time">${this.formatTime(event.timestamp)}</div>
                    <div class="timeline-icon ${iconClass}"></div>
                    <div class="timeline-content">
                        <div class="timeline-title">${event.title}</div>
                        <div class="timeline-description">${event.description}</div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = timelineHtml;
    }

    // Action Methods
    async triggerCertificationSuite() {
        const modal = document.getElementById('triggerModal');
        modal.style.display = 'block';
    }

    async submitTriggerForm() {
        const manifest = document.getElementById('manifestInput').value;
        const cluster = document.getElementById('clusterSelect').value;
        const jiraKey = document.getElementById('jiraKeyInput').value;

        // Get selected suites
        const selectedSuites = Array.from(document.querySelectorAll('#triggerForm input[type="checkbox"]:checked'))
            .map(cb => cb.value);

        if (!manifest) {
            this.showToast('error', 'Validation Error', 'Manifest version is required');
            return;
        }

        try {
            this.closeTriggerModal();
            this.showToast('info', 'Triggering Tests', 'Initiating certification suite...');

            const response = await fetch(`${this.apiBase}/api/v1/tests/certification/trigger`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    manifest,
                    cluster,
                    jira_key: jiraKey || null,
                    suites: selectedSuites.length > 0 ? selectedSuites : null
                })
            });

            const result = await response.json();

            if (response.ok) {
                this.showToast('success', 'Tests Triggered',
                    `${result.test_runs.length} test suites started successfully`);

                // Add triggered tests to display immediately
                this.loadTestData();
            } else {
                this.showToast('error', 'Trigger Failed', result.error || 'Unknown error');
            }

        } catch (e) {
            console.error('Failed to trigger tests:', e);
            this.showToast('error', 'Network Error', 'Failed to communicate with backend');
        }
    }

    async analyzeIssue() {
        const modal = document.getElementById('analyzeModal');
        modal.style.display = 'block';
    }

    async submitAnalyzeForm() {
        const issueKey = document.getElementById('issueKeyInput').value;
        const analysisDepth = document.getElementById('analysisDepthSelect').value;
        const focusAreas = document.getElementById('focusAreasInput').value;

        if (!issueKey) {
            this.showToast('error', 'Validation Error', 'Issue key is required');
            return;
        }

        try {
            this.closeAnalyzeModal();
            this.showToast('info', 'Starting Analysis',
                `Initiating ${analysisDepth} analysis of ${issueKey}...`);

            const response = await fetch(`${this.apiBase}/api/v1/analyze/issue`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    issue_key: issueKey,
                    analysis_depth: analysisDepth,
                    focus_areas: focusAreas ? focusAreas.split(',').map(s => s.trim()) : null
                })
            });

            const result = await response.json();

            if (response.ok) {
                this.showToast('success', 'Analysis Started',
                    `7-dimensional analysis of ${issueKey} in progress...`);

                // Would typically show progress or update UI
                setTimeout(() => this.loadAnalysisData(), 5000);
            } else {
                this.showToast('error', 'Analysis Failed', result.error || 'Unknown error');
            }

        } catch (e) {
            console.error('Failed to start analysis:', e);
            this.showToast('error', 'Network Error', 'Failed to communicate with backend');
        }
    }

    async analyzeTestFailures(testId) {
        try {
            this.showToast('info', 'Analyzing Failures', 'Claude is analyzing test failures...');

            const response = await fetch(`${this.apiBase}/api/v1/tests/${testId}/analyze`, {
                method: 'POST'
            });

            const result = await response.json();

            if (response.ok) {
                this.showAnalysisDetails('Test Failure Analysis', result);
            } else {
                this.showToast('error', 'Analysis Failed', result.error || 'Unknown error');
            }

        } catch (e) {
            console.error('Failed to analyze test failures:', e);
            this.showToast('error', 'Network Error', 'Failed to analyze failures');
        }
    }

    async retriggerTest(suiteId) {
        if (!confirm(`Retrigger ${suiteId} test suite?`)) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/api/v1/tests/${suiteId}/trigger`, {
                method: 'POST'
            });

            const result = await response.json();

            if (response.ok) {
                this.showToast('success', 'Test Triggered', `${suiteId} retriggered successfully`);
                this.loadTestData();
            } else {
                this.showToast('error', 'Retrigger Failed', result.error || 'Unknown error');
            }

        } catch (e) {
            console.error('Failed to retrigger test:', e);
            this.showToast('error', 'Network Error', 'Failed to retrigger test');
        }
    }

    // UI Helper Methods
    getStatusClass(status) {
        const mapping = {
            'success': 'success',
            'unstable': 'warning',
            'failed': 'error',
            'running': 'info',
            'queued': 'info'
        };
        return mapping[status] || 'info';
    }

    getConfidenceClass(confidence) {
        if (confidence >= 0.8) return 'confidence-high';
        if (confidence >= 0.6) return 'confidence-medium';
        return 'confidence-low';
    }

    getEventIconClass(eventType) {
        const mapping = {
            'test_suite_triggered': 'info',
            'issue_analysis_completed': 'success',
            'certification_completed': 'success',
            'failure_detected': 'error',
            'system_alert': 'warning'
        };
        return mapping[eventType] || 'info';
    }

    formatTime(timestamp) {
        try {
            const date = new Date(timestamp);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } catch {
            return timestamp;
        }
    }

    updateLastUpdateTime() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString();
        document.getElementById('lastUpdate').textContent = `Last updated: ${timeStr}`;
    }

    // Modal Management
    closeTriggerModal() {
        this.closeModal('triggerModal');
        // Reset form
        document.getElementById('triggerForm').reset();
    }

    closeAnalyzeModal() {
        this.closeModal('analyzeModal');
        // Reset form
        document.getElementById('analyzeForm').reset();
    }

    closeDetailsModal() {
        this.closeModal('detailsModal');
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }

    closeAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
        });
    }

    showAnalysisDetails(title, data) {
        document.getElementById('detailsTitle').textContent = title;

        let content = `
            <div class="analysis-details">
                <h4>Failure Analysis</h4>
                <div class="detail-item">
                    <strong>Type:</strong> ${data.analysis.failure_type}
                </div>
                <div class="detail-item">
                    <strong>Root Cause:</strong> ${data.analysis.root_cause}
                </div>
                <div class="detail-item">
                    <strong>Severity:</strong>
                    <span class="severity-${data.analysis.severity}">${data.analysis.severity.toUpperCase()}</span>
                </div>
                <div class="detail-item">
                    <strong>Customer Impact:</strong> ${data.analysis.customer_impact}
                </div>

                <h4>Recommendations</h4>
                <div class="recommendations">
                    ${data.recommendations.map(rec => `
                        <div class="recommendation">
                            <div class="rec-priority priority-${rec.priority}">${rec.priority.toUpperCase()}</div>
                            <div class="rec-content">
                                <div class="rec-title">${rec.title}</div>
                                <div class="rec-description">${rec.description}</div>
                                <div class="rec-time">Est. time: ${rec.estimated_time}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        document.getElementById('detailsContent').innerHTML = content;
        document.getElementById('detailsModal').style.display = 'block';
    }

    // Toast Notifications
    showToast(type, title, message, duration = 5000) {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        `;

        container.appendChild(toast);

        // Auto remove after duration
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease forwards';
            setTimeout(() => {
                if (container.contains(toast)) {
                    container.removeChild(toast);
                }
            }, 300);
        }, duration);
    }

    // System Health
    async viewSystemHealth() {
        try {
            const response = await fetch(`${this.apiBase}/health/detailed`);
            const health = await response.json();

            let content = `
                <div class="health-overview">
                    <h4>System Health: ${health.status.toUpperCase()}</h4>

                    <div class="health-components">
                        ${Object.entries(health.components || {}).map(([component, status]) => `
                            <div class="health-item">
                                <span class="component-name">${component.replace(/_/g, ' ').toUpperCase()}</span>
                                <span class="health-status ${this.getStatusClass(status)}">${status}</span>
                            </div>
                        `).join('')}
                    </div>

                    <h4>Metrics</h4>
                    <div class="metrics">
                        ${Object.entries(health.metrics || {}).map(([metric, value]) => `
                            <div class="metric-item">
                                <span class="metric-name">${metric.replace(/_/g, ' ')}</span>
                                <span class="metric-value">${value}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;

            this.showDetailsModal('System Health', content);

        } catch (e) {
            console.error('Failed to get system health:', e);
            this.showToast('error', 'Health Check Failed', 'Unable to retrieve system status');
        }
    }

    showDetailsModal(title, content) {
        document.getElementById('detailsTitle').textContent = title;
        document.getElementById('detailsContent').innerHTML = content;
        document.getElementById('detailsModal').style.display = 'block';
    }
}

// Global functions for HTML event handlers
function triggerCertificationSuite() {
    window.emtDashboard.triggerCertificationSuite();
}

function analyzeIssue() {
    window.emtDashboard.analyzeIssue();
}

function viewSystemHealth() {
    window.emtDashboard.viewSystemHealth();
}

function closeTriggerModal() {
    window.emtDashboard.closeTriggerModal();
}

function closeAnalyzeModal() {
    window.emtDashboard.closeAnalyzeModal();
}

function closeDetailsModal() {
    window.emtDashboard.closeDetailsModal();
}

function submitTriggerForm() {
    window.emtDashboard.submitTriggerForm();
}

function submitAnalyzeForm() {
    window.emtDashboard.submitAnalyzeForm();
}

function analyzeTestFailures(testId) {
    window.emtDashboard.analyzeTestFailures(testId);
}

function retriggerTest(suiteId) {
    window.emtDashboard.retriggerTest(suiteId);
}

function refreshTests() {
    window.emtDashboard.loadTestData();
    window.emtDashboard.showToast('info', 'Refreshing', 'Loading latest test data...');
}

function refreshAnalyses() {
    window.emtDashboard.loadAnalysisData();
    window.emtDashboard.showToast('info', 'Refreshing', 'Loading latest analyses...');
}

function filterTimeline() {
    const filter = document.getElementById('timelineFilter').value;
    // Implementation would filter timeline based on selection
    window.emtDashboard.showToast('info', 'Filter Applied', `Filtering timeline: ${filter || 'All events'}`);
}

// Add CSS animations for slideOutRight
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }

    .empty-state {
        text-align: center;
        padding: 40px 20px;
        color: var(--text-secondary);
    }

    .empty-icon {
        font-size: 3rem;
        margin-bottom: 15px;
        opacity: 0.6;
    }

    .empty-title {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 8px;
        color: var(--secondary-color);
    }

    .empty-description {
        font-size: 0.9rem;
    }

    .analysis-details {
        font-size: 0.9rem;
    }

    .analysis-details h4 {
        color: var(--secondary-color);
        margin: 20px 0 15px;
        font-size: 1.1rem;
    }

    .detail-item {
        margin-bottom: 10px;
        line-height: 1.6;
    }

    .severity-high { color: var(--error-color); font-weight: bold; }
    .severity-medium { color: var(--warning-color); font-weight: bold; }
    .severity-low { color: var(--success-color); font-weight: bold; }

    .recommendations {
        space: 15px 0;
    }

    .recommendation {
        display: flex;
        gap: 15px;
        padding: 15px;
        border-radius: var(--radius-md);
        background: var(--bg-secondary);
        margin-bottom: 15px;
    }

    .rec-priority {
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: bold;
        color: white;
        text-align: center;
        min-width: 60px;
    }

    .priority-critical { background: var(--error-color); }
    .priority-high { background: var(--warning-color); }
    .priority-medium { background: var(--info-color); }
    .priority-low { background: var(--text-muted); }

    .rec-content {
        flex: 1;
    }

    .rec-title {
        font-weight: 600;
        color: var(--secondary-color);
        margin-bottom: 5px;
    }

    .rec-description {
        color: var(--text-secondary);
        margin-bottom: 5px;
    }

    .rec-time {
        font-size: 0.8rem;
        color: var(--text-muted);
    }

    .health-components, .metrics {
        display: grid;
        gap: 10px;
        margin: 15px 0;
    }

    .health-item, .metric-item {
        display: flex;
        justify-content: space-between;
        padding: 10px;
        background: var(--bg-secondary);
        border-radius: var(--radius-sm);
    }

    .component-name, .metric-name {
        font-weight: 500;
    }

    .health-status {
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.8rem;
        color: white;
    }

    .health-status.success { background: var(--success-color); }
    .health-status.error { background: var(--error-color); }
    .health-status.warning { background: var(--warning-color); }
`;

document.head.appendChild(style);