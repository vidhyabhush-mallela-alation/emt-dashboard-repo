#!/usr/bin/env python3
"""
Atlassian Context Enricher Skill for Alation EMT Dashboard
Systematic multi-dimensional analysis of customer issues via Jira & Confluence
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
import re

logger = logging.getLogger(__name__)

class AnalysisPhase(Enum):
    TECHNICAL_EXPANSION = "technical_expansion"
    CROSS_PLATFORM = "cross_platform"
    TEMPORAL = "temporal"
    PEOPLE_NETWORK = "people_network"
    CUSTOMER_IMPACT = "customer_impact"
    SYSTEM_LAYERS = "system_layers"
    PATTERN_RECOGNITION = "pattern_recognition"

class IssueType(Enum):
    CUSTOMER_ESCALATION = "customer_escalation"
    PLATFORM_ISSUE = "platform_issue"
    CONNECTOR_PROBLEM = "connector_problem"
    PERFORMANCE_ISSUE = "performance_issue"
    DATA_QUALITY = "data_quality"
    INTEGRATION_FAILURE = "integration_failure"

@dataclass
class SearchResult:
    """Individual search result"""
    id: str
    title: str
    url: str
    content_type: str  # jira_issue, confluence_page, comment
    project: str
    created: datetime
    updated: datetime
    author: str
    summary: str
    relevance_score: float

@dataclass
class AnalysisPhaseResult:
    """Results from a single analysis phase"""
    phase: AnalysisPhase
    search_count: int
    results_found: int
    key_findings: List[str]
    search_queries: List[str]
    related_items: List[SearchResult]
    patterns_identified: List[str]
    completion_time: datetime

@dataclass
class IssueAnalysis:
    """Comprehensive issue analysis result"""
    issue_key: str
    issue_type: IssueType
    priority: str
    customer_impact: str
    root_cause_hypothesis: str
    affected_components: List[str]
    related_issues: List[str]
    team_expertise: Dict[str, List[str]]
    timeline_events: List[Dict]
    phase_results: List[AnalysisPhaseResult]
    recommendations: List[str]
    systemic_patterns: List[str]
    customer_scope: Dict[str, Any]
    analysis_summary: str
    confidence_score: float

@dataclass
class CustomerImpact:
    """Customer impact assessment"""
    severity: str  # low, medium, high, critical
    affected_customers: List[str]
    business_functions: List[str]
    revenue_impact: str
    user_experience: str
    escalation_risk: str
    mitigation_urgency: str

class AtlassianContextEnricher:
    """
    Systematic multi-dimensional analysis framework for Alation customer issues

    Transforms surface-level customer issue investigation into comprehensive technical
    intelligence through 7-dimensional search methodology across Alation's Jira and Confluence.
    """

    def __init__(self, atlassian_client=None, claude_mcp_client=None):
        self.atlassian_client = atlassian_client
        self.mcp_client = claude_mcp_client

        # Alation-specific search patterns
        self.alation_components = [
            "lineage-service", "alation-analytics", "connectors", "query-log-ingestion",
            "metadata-extraction", "data-catalog", "stewardship", "governance",
            "compose", "articles", "lexicon", "dashboards", "reports"
        ]

        self.alation_databases = [
            "snowflake", "databricks", "bigquery", "redshift", "postgresql", "mysql",
            "oracle", "sql-server", "athena", "presto", "hive", "teradata"
        ]

        self.customer_indicators = [
            "customer-escalation", "support-escalation", "production-issue",
            "customer-impact", "sev-1", "sev-2", "critical", "urgent"
        ]

    async def analyze_issue(self,
                          issue_key: str,
                          analysis_depth: str = "comprehensive",
                          focus_areas: List[str] = None) -> IssueAnalysis:
        """
        Execute comprehensive 7-dimensional analysis of Alation customer issue

        Args:
            issue_key: JIRA issue key (e.g., "AL-123456", "EMT-224570")
            analysis_depth: "quick", "standard", or "comprehensive"
            focus_areas: Optional list of specific areas to focus on

        Returns:
            Complete issue analysis with multi-dimensional insights
        """
        logger.info(f"Starting comprehensive analysis of {issue_key}")

        # Get initial issue details
        initial_issue = await self._get_issue_details(issue_key)
        if not initial_issue:
            raise ValueError(f"Issue {issue_key} not found or inaccessible")

        # Determine issue type and configure analysis
        issue_type = self._classify_issue_type(initial_issue)
        search_config = self._get_search_configuration(analysis_depth, issue_type)

        # Execute all 7 analysis phases
        phase_results = []

        # Phase 1: Technical Term Expansion
        phase_1 = await self._execute_technical_expansion(initial_issue, search_config)
        phase_results.append(phase_1)

        # Phase 2: Cross-Platform Deep Dive
        phase_2 = await self._execute_cross_platform_analysis(initial_issue, phase_1, search_config)
        phase_results.append(phase_2)

        # Phase 3: Temporal Analysis
        phase_3 = await self._execute_temporal_analysis(initial_issue, phase_results, search_config)
        phase_results.append(phase_3)

        # Phase 4: People Network Analysis
        phase_4 = await self._execute_people_network_analysis(initial_issue, phase_results, search_config)
        phase_results.append(phase_4)

        # Phase 5: Customer Impact Assessment
        phase_5 = await self._execute_customer_impact_analysis(initial_issue, phase_results, search_config)
        phase_results.append(phase_5)

        # Phase 6: System Layer Correlation
        phase_6 = await self._execute_system_correlation_analysis(initial_issue, phase_results, search_config)
        phase_results.append(phase_6)

        # Phase 7: Pattern Recognition
        phase_7 = await self._execute_pattern_recognition_analysis(initial_issue, phase_results, search_config)
        phase_results.append(phase_7)

        # Synthesize comprehensive analysis
        analysis = await self._synthesize_analysis(issue_key, initial_issue, issue_type, phase_results)

        logger.info(f"Completed comprehensive analysis of {issue_key}: {analysis.confidence_score:.2f} confidence")
        return analysis

    async def _get_issue_details(self, issue_key: str) -> Dict[str, Any]:
        """Get initial issue details from JIRA"""
        if not self.atlassian_client:
            # Mock issue for development
            return {
                "key": issue_key,
                "summary": "Sample issue for analysis",
                "description": "This is a sample issue description for testing",
                "priority": "High",
                "labels": ["customer-escalation"],
                "components": ["lineage-service"],
                "created": "2026-04-06T10:00:00Z",
                "updated": "2026-04-07T15:30:00Z",
                "reporter": "customer.support@alation.com",
                "assignee": "engineering.team@alation.com"
            }

        try:
            # In production, this would use Atlassian REST API
            issue = await self.atlassian_client.get_issue(issue_key)
            return {
                "key": issue.key,
                "summary": issue.fields.summary,
                "description": issue.fields.description or "",
                "priority": issue.fields.priority.name if issue.fields.priority else "Medium",
                "labels": issue.fields.labels or [],
                "components": [c.name for c in issue.fields.components] if issue.fields.components else [],
                "created": issue.fields.created,
                "updated": issue.fields.updated,
                "reporter": issue.fields.reporter.emailAddress if issue.fields.reporter else "",
                "assignee": issue.fields.assignee.emailAddress if issue.fields.assignee else ""
            }
        except Exception as e:
            logger.error(f"Failed to get issue details for {issue_key}: {e}")
            return None

    def _classify_issue_type(self, issue: Dict[str, Any]) -> IssueType:
        """Classify issue type based on content analysis"""
        summary = issue.get("summary", "").lower()
        description = issue.get("description", "").lower()
        labels = [label.lower() for label in issue.get("labels", [])]
        combined_text = f"{summary} {description} {' '.join(labels)}"

        # Customer escalation indicators
        if any(indicator in combined_text for indicator in ["customer-escalation", "sev-1", "critical-customer"]):
            return IssueType.CUSTOMER_ESCALATION

        # Performance issue indicators
        if any(term in combined_text for term in ["timeout", "slow", "performance", "latency", "hang"]):
            return IssueType.PERFORMANCE_ISSUE

        # Connector problem indicators
        if any(db in combined_text for db in self.alation_databases) or "connector" in combined_text:
            return IssueType.CONNECTOR_PROBLEM

        # Data quality indicators
        if any(term in combined_text for term in ["data-quality", "metadata", "lineage", "profiling"]):
            return IssueType.DATA_QUALITY

        # Integration failure indicators
        if any(term in combined_text for term in ["api", "integration", "sync", "webhook"]):
            return IssueType.INTEGRATION_FAILURE

        # Default to platform issue
        return IssueType.PLATFORM_ISSUE

    def _get_search_configuration(self, depth: str, issue_type: IssueType) -> Dict[str, int]:
        """Get search configuration based on analysis depth and issue type"""
        base_config = {
            "quick": {"min_searches_per_phase": 3, "max_results_per_search": 10},
            "standard": {"min_searches_per_phase": 6, "max_results_per_search": 20},
            "comprehensive": {"min_searches_per_phase": 8, "max_results_per_search": 30}
        }

        config = base_config.get(depth, base_config["comprehensive"])

        # Adjust based on issue type
        if issue_type == IssueType.CUSTOMER_ESCALATION:
            config["min_searches_per_phase"] = max(config["min_searches_per_phase"], 8)
            config["customer_focus"] = True

        return config

    async def _execute_technical_expansion(self,
                                         issue: Dict[str, Any],
                                         config: Dict[str, int]) -> AnalysisPhaseResult:
        """
        Phase 1: Technical Term Expansion (MINIMUM 8 searches)

        Systematic term progression:
        Core issue → Adjacent terms → Error messages → Component names → System layers
        """
        logger.info("Phase 1: Technical Term Expansion")
        start_time = datetime.now()

        # Extract core technical terms from issue
        core_terms = self._extract_technical_terms(issue)
        search_queries = []
        all_results = []

        # 1. Core issue search
        core_query = f"text ~ \"{issue.get('summary', '')}\" AND project in (AL, EMT, SUPPORT)"
        jira_results = await self._search_jira(core_query)
        all_results.extend(jira_results)
        search_queries.append(core_query)

        # 2. Alation service/connector expansion
        for component in issue.get("components", []):
            if component in self.alation_components:
                query = f"component = \"{component}\" AND text ~ \"customer\""
                results = await self._search_jira(query)
                all_results.extend(results)
                search_queries.append(query)

        # 3. Error/failure pattern searches
        error_terms = self._extract_error_patterns(issue)
        for error_term in error_terms[:3]:
            query = f"text ~ \"{error_term}\" OR summary ~ \"{error_term}\""
            results = await self._search_jira(query)
            all_results.extend(results)
            search_queries.append(query)

        # 4. Database/connector specific searches
        for db in self.alation_databases:
            if db in issue.get("description", "").lower():
                query = f"text ~ \"{db}\" AND labels in (customer-escalation)"
                results = await self._search_jira(query)
                all_results.extend(results)
                search_queries.append(query)

        # Ensure minimum search count
        while len(search_queries) < config["min_searches_per_phase"]:
            # Add supplementary searches
            supplementary_terms = ["production", "customer-impact", "lineage", "metadata"]
            for term in supplementary_terms:
                if len(search_queries) >= config["min_searches_per_phase"]:
                    break
                query = f"text ~ \"{term}\" AND priority in (High, Critical)"
                results = await self._search_jira(query)
                all_results.extend(results)
                search_queries.append(query)

        # Confluence searches for technical documentation
        conf_queries = [
            f"{issue.get('summary', '')} architecture",
            f"troubleshooting {' '.join(core_terms[:2])}",
            f"known issues {' '.join(issue.get('components', [])[:2])}"
        ]

        for conf_query in conf_queries:
            results = await self._search_confluence(conf_query)
            all_results.extend(results)
            search_queries.append(f"Confluence: {conf_query}")

        # Analyze results for key findings
        key_findings = self._extract_key_findings(all_results, "technical")
        patterns = self._identify_technical_patterns(all_results)

        return AnalysisPhaseResult(
            phase=AnalysisPhase.TECHNICAL_EXPANSION,
            search_count=len(search_queries),
            results_found=len(all_results),
            key_findings=key_findings,
            search_queries=search_queries,
            related_items=all_results[:20],  # Limit for storage
            patterns_identified=patterns,
            completion_time=datetime.now()
        )

    async def _execute_cross_platform_analysis(self,
                                             issue: Dict[str, Any],
                                             phase_1: AnalysisPhaseResult,
                                             config: Dict[str, int]) -> AnalysisPhaseResult:
        """
        Phase 2: Cross-Platform Deep Dive (MINIMUM 12 searches - 6 Jira + 6 Confluence)

        MANDATORY: Must search BOTH platforms. Confluence searches are NOT optional.
        """
        logger.info("Phase 2: Cross-Platform Deep Dive")

        search_queries = []
        all_results = []

        # JIRA systematic areas (6 searches minimum)
        jira_searches = [
            # Component/Label analysis
            f"component in ({', '.join(issue.get('components', ['lineage-service']))}) ORDER BY updated DESC",

            # Workflow patterns
            f"project = AL AND status changed DURING (-30d) AND text ~ \"customer\"",

            # Cross-references and linked issues
            f"issueFunction in linkedIssuesOf(\"key = {issue.get('key')}\")",

            # Version correlations
            f"affectedVersion in latestReleasedVersion() AND priority >= High",

            # Priority/severity trends
            f"priority in (Critical, High) AND created >= -7d AND text ~ \"production\"",

            # Assignment patterns and expertise
            f"assignee in membersOf(\"alation-engineering\") AND text ~ \"lineage\""
        ]

        for query in jira_searches:
            results = await self._search_jira(query)
            all_results.extend(results)
            search_queries.append(f"JIRA: {query}")

        # Confluence systematic areas (6 searches minimum)
        confluence_searches = [
            # Team documentation and runbooks
            "lineage troubleshooting runbook",

            # Architecture decisions
            "lineage service architecture design",

            # Meeting records and planning
            "lineage team retrospective sprint notes",

            # Customer communication and support
            "customer lineage issues FAQ support",

            # Standards and best practices
            "lineage certification testing standards",

            # Incident history and resolutions
            "lineage outage incident post-mortem"
        ]

        for query in confluence_searches:
            results = await self._search_confluence(query)
            all_results.extend(results)
            search_queries.append(f"Confluence: {query}")

        # Extract cross-platform insights
        key_findings = self._extract_cross_platform_insights(all_results)
        patterns = self._identify_cross_platform_patterns(all_results)

        return AnalysisPhaseResult(
            phase=AnalysisPhase.CROSS_PLATFORM,
            search_count=len(search_queries),
            results_found=len(all_results),
            key_findings=key_findings,
            search_queries=search_queries,
            related_items=all_results[:25],
            patterns_identified=patterns,
            completion_time=datetime.now()
        )

    async def _execute_temporal_analysis(self,
                                       issue: Dict[str, Any],
                                       previous_phases: List[AnalysisPhaseResult],
                                       config: Dict[str, int]) -> AnalysisPhaseResult:
        """
        Phase 3: Temporal Analysis (MINIMUM 6 searches)

        Time-based pattern detection for issue evolution and correlation
        """
        logger.info("Phase 3: Temporal Analysis")

        search_queries = []
        all_results = []

        issue_created = datetime.fromisoformat(issue.get("created", "2026-04-01T00:00:00Z").replace("Z", "+00:00"))

        # Recent activity surge around issue timeframe
        recent_queries = [
            f"created >= -30d AND text ~ \"lineage\" ORDER BY created DESC",
            f"updated >= -7d AND priority >= High",
            f"created >= \"{(issue_created - timedelta(days=7)).strftime('%Y-%m-%d')}\" AND created <= \"{(issue_created + timedelta(days=7)).strftime('%Y-%m-%d')}\" AND text ~ \"customer\""
        ]

        for query in recent_queries:
            results = await self._search_jira(query)
            all_results.extend(results)
            search_queries.append(f"Recent: {query}")

        # Historical context and patterns
        historical_queries = [
            f"created >= -90d AND text ~ \"lineage\" AND labels in (customer-escalation) ORDER BY created",
            f"fixVersion in releasedVersions() AND text ~ \"performance\"",
            f"created >= -180d AND component in (lineage-service) ORDER BY priority DESC"
        ]

        for query in historical_queries:
            results = await self._search_jira(query)
            all_results.extend(results)
            search_queries.append(f"Historical: {query}")

        # Timeline correlation analysis
        timeline_events = self._build_temporal_timeline(all_results, issue_created)
        patterns = self._identify_temporal_patterns(timeline_events)

        key_findings = [
            f"Issue created during period with {len([r for r in all_results if abs((datetime.fromisoformat(r.created.replace('Z', '+00:00')) - issue_created).days) <= 7])} similar issues",
            f"Identified {len(patterns)} temporal patterns",
            f"Historical context spans {len([r for r in all_results if (datetime.now() - datetime.fromisoformat(r.created.replace('Z', '+00:00'))).days > 30])} related historical issues"
        ]

        return AnalysisPhaseResult(
            phase=AnalysisPhase.TEMPORAL,
            search_count=len(search_queries),
            results_found=len(all_results),
            key_findings=key_findings,
            search_queries=search_queries,
            related_items=all_results[:20],
            patterns_identified=patterns,
            completion_time=datetime.now()
        )

    async def _execute_people_network_analysis(self,
                                             issue: Dict[str, Any],
                                             previous_phases: List[AnalysisPhaseResult],
                                             config: Dict[str, int]) -> AnalysisPhaseResult:
        """
        Phase 4: People Network Analysis (MINIMUM 4 searches)

        Expertise and ownership mapping for efficient resolution
        """
        logger.info("Phase 4: People Network Analysis")

        search_queries = []
        all_results = []

        # Domain experts identification
        expert_queries = [
            f"assignee in (\"engineering.lineage@alation.com\") AND text ~ \"lineage\"",
            f"reporter in membersOf(\"customer-success\") AND component in (lineage-service)",
            f"project = AL AND component in (lineage-service) ORDER BY assignee",
            f"labels in (lineage-expertise) OR text ~ \"lineage-expert\""
        ]

        for query in expert_queries:
            results = await self._search_jira(query)
            all_results.extend(results)
            search_queries.append(f"Experts: {query}")

        # Confluence people expertise mapping
        confluence_people = await self._search_confluence("lineage team expertise contact")
        all_results.extend(confluence_people)
        search_queries.append("Confluence: lineage team expertise")

        # Analyze people networks
        people_network = self._analyze_people_network(all_results)
        expertise_mapping = self._map_expertise_areas(all_results, issue)

        key_findings = [
            f"Identified {len(people_network)} key people in issue domain",
            f"Found {len(expertise_mapping)} expertise areas relevant to issue",
            f"Mapped {len([r for r in all_results if r.author])} contributors to similar issues"
        ]

        return AnalysisPhaseResult(
            phase=AnalysisPhase.PEOPLE_NETWORK,
            search_count=len(search_queries),
            results_found=len(all_results),
            key_findings=key_findings,
            search_queries=search_queries,
            related_items=all_results[:15],
            patterns_identified=[f"Expert: {expert}" for expert in people_network[:5]],
            completion_time=datetime.now()
        )

    async def _execute_customer_impact_analysis(self,
                                              issue: Dict[str, Any],
                                              previous_phases: List[AnalysisPhaseResult],
                                              config: Dict[str, int]) -> AnalysisPhaseResult:
        """
        Phase 5: Customer Impact Assessment (MINIMUM 6 searches)

        Business impact and escalation analysis for prioritization
        """
        logger.info("Phase 5: Customer Impact Assessment")

        search_queries = []
        all_results = []

        # Customer escalation patterns
        escalation_queries = [
            f"labels in (customer-escalation) AND text ~ \"lineage\"",
            f"priority >= High AND text ~ \"customer\" AND component in (lineage-service)",
            f"issueType = \"Customer Escalation\" AND text ~ \"production\"",
            f"text ~ \"sev-1\" OR text ~ \"critical-customer\"",
            f"text ~ \"revenue-impact\" OR text ~ \"business-critical\"",
            f"summary ~ \"customer\" AND created >= -60d ORDER BY priority DESC"
        ]

        for query in escalation_queries:
            results = await self._search_jira(query)
            all_results.extend(results)
            search_queries.append(f"Impact: {query}")

        # Analyze customer impact
        impact_assessment = await self._assess_customer_impact(all_results, issue)
        business_implications = self._analyze_business_implications(all_results)

        key_findings = [
            f"Customer impact level: {impact_assessment.severity}",
            f"Affects {len(impact_assessment.affected_customers)} identified customers",
            f"Business functions impacted: {', '.join(impact_assessment.business_functions[:3])}",
            f"Escalation risk: {impact_assessment.escalation_risk}"
        ]

        patterns = [
            f"Severity: {impact_assessment.severity}",
            f"Revenue impact: {impact_assessment.revenue_impact}",
            f"User experience: {impact_assessment.user_experience}"
        ]

        return AnalysisPhaseResult(
            phase=AnalysisPhase.CUSTOMER_IMPACT,
            search_count=len(search_queries),
            results_found=len(all_results),
            key_findings=key_findings,
            search_queries=search_queries,
            related_items=all_results[:20],
            patterns_identified=patterns,
            completion_time=datetime.now()
        )

    async def _execute_system_correlation_analysis(self,
                                                 issue: Dict[str, Any],
                                                 previous_phases: List[AnalysisPhaseResult],
                                                 config: Dict[str, int]) -> AnalysisPhaseResult:
        """
        Phase 6: System Layer Correlation (MINIMUM 10 searches)

        Architectural dependency mapping for comprehensive understanding
        """
        logger.info("Phase 6: System Layer Correlation")

        search_queries = []
        all_results = []

        # Adjacent systems and integrations
        system_queries = [
            f"text ~ \"lineage-service\" AND text ~ \"analytics\"",
            f"component in (connectors) AND text ~ \"lineage\"",
            f"text ~ \"metadata-extraction\" AND text ~ \"lineage\"",
            f"text ~ \"query-log\" AND text ~ \"lineage\"",
            f"text ~ \"stewardship\" OR text ~ \"governance\"",
            f"text ~ \"compose\" AND text ~ \"lineage\"",
            f"text ~ \"api\" AND component in (lineage-service)",
            f"text ~ \"database\" AND text ~ \"performance\"",
            f"text ~ \"ui\" AND text ~ \"frontend\" AND component in (lineage-service)",
            f"text ~ \"infrastructure\" OR text ~ \"deployment\""
        ]

        for query in system_queries:
            results = await self._search_jira(query)
            all_results.extend(results)
            search_queries.append(f"System: {query}")

        # System architecture correlation
        system_map = self._build_system_correlation_map(all_results)
        dependency_analysis = self._analyze_system_dependencies(all_results, issue)

        key_findings = [
            f"Identified {len(system_map)} interconnected system components",
            f"Found {len(dependency_analysis)} critical system dependencies",
            f"Mapped {len([r for r in all_results if 'api' in r.summary.lower()])} API-related issues",
            f"Detected {len([r for r in all_results if 'performance' in r.summary.lower()])} performance correlations"
        ]

        return AnalysisPhaseResult(
            phase=AnalysisPhase.SYSTEM_LAYERS,
            search_count=len(search_queries),
            results_found=len(all_results),
            key_findings=key_findings,
            search_queries=search_queries,
            related_items=all_results[:25],
            patterns_identified=[f"System: {system}" for system in system_map[:7]],
            completion_time=datetime.now()
        )

    async def _execute_pattern_recognition_analysis(self,
                                                  issue: Dict[str, Any],
                                                  previous_phases: List[AnalysisPhaseResult],
                                                  config: Dict[str, int]) -> AnalysisPhaseResult:
        """
        Phase 7: Pattern Recognition (MINIMUM 12 searches)

        Cross-domain and systemic analysis for pattern identification
        """
        logger.info("Phase 7: Pattern Recognition")

        search_queries = []
        all_results = []

        # Cross-technology patterns
        tech_patterns = [
            f"text ~ \"snowflake\" AND text ~ \"lineage\"",
            f"text ~ \"databricks\" AND text ~ \"performance\"",
            f"text ~ \"bigquery\" AND text ~ \"timeout\"",
            f"text ~ \"redshift\" AND text ~ \"metadata\""
        ]

        # Cross-team patterns
        team_patterns = [
            f"project in (AL, EMT) AND text ~ \"lineage\"",
            f"component in (lineage-service, connectors) AND text ~ \"customer\"",
            f"assignee in membersOf(\"engineering\") AND text ~ \"escalation\"",
            f"reporter in membersOf(\"support\") AND priority >= High"
        ]

        # Cross-environment patterns
        env_patterns = [
            f"text ~ \"production\" AND text ~ \"performance\"",
            f"text ~ \"staging\" AND text ~ \"deployment\"",
            f"text ~ \"qa-enterprise\" AND text ~ \"testing\"",
            f"text ~ \"cluster\" AND text ~ \"timeout\""
        ]

        all_pattern_queries = tech_patterns + team_patterns + env_patterns

        for query in all_pattern_queries:
            results = await self._search_jira(query)
            all_results.extend(results)
            search_queries.append(f"Pattern: {query}")

        # Comprehensive pattern analysis
        systemic_patterns = self._identify_systemic_patterns(all_results, previous_phases)
        cross_domain_insights = self._analyze_cross_domain_patterns(all_results)

        key_findings = [
            f"Identified {len(systemic_patterns)} systemic patterns",
            f"Found {len(cross_domain_insights)} cross-domain insights",
            f"Detected {len([p for p in systemic_patterns if 'customer' in p.lower()])} customer-impacting patterns",
            f"Mapped {len([p for p in systemic_patterns if 'performance' in p.lower()])} performance patterns"
        ]

        return AnalysisPhaseResult(
            phase=AnalysisPhase.PATTERN_RECOGNITION,
            search_count=len(search_queries),
            results_found=len(all_results),
            key_findings=key_findings,
            search_queries=search_queries,
            related_items=all_results[:30],
            patterns_identified=systemic_patterns,
            completion_time=datetime.now()
        )

    async def _synthesize_analysis(self,
                                 issue_key: str,
                                 initial_issue: Dict[str, Any],
                                 issue_type: IssueType,
                                 phase_results: List[AnalysisPhaseResult]) -> IssueAnalysis:
        """
        Synthesize comprehensive analysis from all phases

        Combines insights from all 7 phases into actionable intelligence
        """
        logger.info("Synthesizing comprehensive analysis")

        # Aggregate all findings
        all_findings = []
        all_patterns = []
        all_related_items = []

        for phase in phase_results:
            all_findings.extend(phase.key_findings)
            all_patterns.extend(phase.patterns_identified)
            all_related_items.extend(phase.related_items)

        # Generate root cause hypothesis
        root_cause = self._generate_root_cause_hypothesis(initial_issue, phase_results)

        # Identify affected components
        affected_components = self._consolidate_affected_components(phase_results)

        # Extract related issues
        related_issues = self._extract_related_issues(all_related_items)

        # Map team expertise
        team_expertise = self._consolidate_team_expertise(phase_results)

        # Build timeline
        timeline_events = self._build_comprehensive_timeline(phase_results)

        # Generate recommendations
        recommendations = await self._generate_recommendations(initial_issue, phase_results, issue_type)

        # Assess customer impact
        customer_impact = await self._synthesize_customer_impact(phase_results)

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(phase_results)

        # Generate analysis summary
        analysis_summary = self._generate_analysis_summary(
            initial_issue, issue_type, phase_results, confidence_score
        )

        return IssueAnalysis(
            issue_key=issue_key,
            issue_type=issue_type,
            priority=initial_issue.get("priority", "Medium"),
            customer_impact=customer_impact.severity,
            root_cause_hypothesis=root_cause,
            affected_components=affected_components,
            related_issues=related_issues,
            team_expertise=team_expertise,
            timeline_events=timeline_events,
            phase_results=phase_results,
            recommendations=recommendations,
            systemic_patterns=all_patterns,
            customer_scope=asdict(customer_impact),
            analysis_summary=analysis_summary,
            confidence_score=confidence_score
        )

    # Helper methods for search and analysis

    async def _search_jira(self, query: str, max_results: int = 20) -> List[SearchResult]:
        """Search JIRA using JQL query"""
        if not self.atlassian_client:
            # Mock search results for development
            return [
                SearchResult(
                    id=f"AL-{i:06d}",
                    title=f"Sample issue {i} matching: {query[:30]}...",
                    url=f"https://alationcorp.atlassian.net/browse/AL-{i:06d}",
                    content_type="jira_issue",
                    project="AL",
                    created=datetime.now() - timedelta(days=i),
                    updated=datetime.now() - timedelta(hours=i),
                    author=f"user{i}@alation.com",
                    summary=f"Issue summary for {i}",
                    relevance_score=1.0 - (i * 0.1)
                ) for i in range(min(5, max_results))
            ]

        try:
            # In production, execute actual JQL search
            issues = await self.atlassian_client.search_issues(query, maxResults=max_results)
            return [self._convert_jira_issue_to_search_result(issue) for issue in issues]
        except Exception as e:
            logger.error(f"JIRA search failed for query '{query}': {e}")
            return []

    async def _search_confluence(self, query: str, max_results: int = 15) -> List[SearchResult]:
        """Search Confluence using CQL query"""
        if not self.atlassian_client:
            # Mock search results for development
            return [
                SearchResult(
                    id=f"CONF-{i}",
                    title=f"Confluence page {i}: {query[:20]}",
                    url=f"https://alationcorp.atlassian.net/wiki/spaces/ENG/pages/{i}",
                    content_type="confluence_page",
                    project="Engineering",
                    created=datetime.now() - timedelta(days=i*2),
                    updated=datetime.now() - timedelta(days=i),
                    author=f"author{i}@alation.com",
                    summary=f"Page content about {query}",
                    relevance_score=0.9 - (i * 0.1)
                ) for i in range(min(3, max_results))
            ]

        try:
            # In production, execute actual Confluence search
            pages = await self.atlassian_client.search_content(query, limit=max_results)
            return [self._convert_confluence_page_to_search_result(page) for page in pages]
        except Exception as e:
            logger.error(f"Confluence search failed for query '{query}': {e}")
            return []

    def _extract_technical_terms(self, issue: Dict[str, Any]) -> List[str]:
        """Extract technical terms from issue content"""
        content = f"{issue.get('summary', '')} {issue.get('description', '')}"

        # Extract Alation-specific terms
        terms = []
        for component in self.alation_components:
            if component in content.lower():
                terms.append(component)

        for db in self.alation_databases:
            if db in content.lower():
                terms.append(db)

        # Extract technical patterns
        tech_patterns = re.findall(r'\b(?:api|service|connector|lineage|metadata)\w*\b', content.lower())
        terms.extend(tech_patterns[:5])

        return list(set(terms))[:10]

    def _extract_error_patterns(self, issue: Dict[str, Any]) -> List[str]:
        """Extract error patterns and messages from issue"""
        content = f"{issue.get('summary', '')} {issue.get('description', '')}"

        error_patterns = [
            r'(?:error|exception|failure|timeout)[\s:]*([^\n\r.]+)',
            r'(?:failed|unable|cannot)[\s:]*([^\n\r.]+)',
            r'(?:\d{3,4}[\s:]*)([^\n\r.]+)',  # HTTP status codes
        ]

        errors = []
        for pattern in error_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            errors.extend([match.strip()[:50] for match in matches[:3]])

        return errors[:5]

    def _extract_key_findings(self, results: List[SearchResult], phase_type: str) -> List[str]:
        """Extract key findings from search results"""
        if not results:
            return ["No significant findings in this phase"]

        findings = [
            f"Found {len(results)} related items across {len(set(r.project for r in results))} projects",
            f"Average relevance score: {sum(r.relevance_score for r in results) / len(results):.2f}",
            f"Most recent related activity: {max(r.updated for r in results).strftime('%Y-%m-%d')}"
        ]

        # Phase-specific findings
        if phase_type == "technical":
            tech_results = [r for r in results if any(comp in r.summary.lower() for comp in self.alation_components)]
            if tech_results:
                findings.append(f"Identified {len(tech_results)} technical component correlations")

        return findings

    def _identify_technical_patterns(self, results: List[SearchResult]) -> List[str]:
        """Identify technical patterns from results"""
        patterns = []

        # Component frequency analysis
        components = {}
        for result in results:
            for comp in self.alation_components:
                if comp in result.summary.lower() or comp in result.content_type.lower():
                    components[comp] = components.get(comp, 0) + 1

        top_components = sorted(components.items(), key=lambda x: x[1], reverse=True)[:3]
        for comp, count in top_components:
            patterns.append(f"High correlation with {comp} ({count} occurrences)")

        return patterns

    # Additional helper methods would be implemented for other analysis functions...
    # (Continuing with the pattern for brevity)

    def _generate_root_cause_hypothesis(self, issue: Dict[str, Any], phases: List[AnalysisPhaseResult]) -> str:
        """Generate root cause hypothesis based on all analysis phases"""
        # Analyze patterns across phases to form hypothesis
        technical_patterns = []
        customer_patterns = []
        system_patterns = []

        for phase in phases:
            if phase.phase == AnalysisPhase.TECHNICAL_EXPANSION:
                technical_patterns = phase.patterns_identified
            elif phase.phase == AnalysisPhase.CUSTOMER_IMPACT:
                customer_patterns = phase.patterns_identified
            elif phase.phase == AnalysisPhase.SYSTEM_LAYERS:
                system_patterns = phase.patterns_identified

        # Form hypothesis based on dominant patterns
        if any("timeout" in pattern.lower() for pattern in technical_patterns):
            return "Performance degradation in lineage visualization components causing UI timeouts and poor user experience"
        elif any("connector" in pattern.lower() for pattern in system_patterns):
            return "Data connector reliability issues affecting metadata ingestion and lineage accuracy"
        elif any("customer" in pattern.lower() for pattern in customer_patterns):
            return "Customer-impacting issue requiring immediate attention due to business-critical workflow disruption"
        else:
            return "Multi-faceted technical issue requiring systematic investigation across platform components"

    async def _assess_customer_impact(self, results: List[SearchResult], issue: Dict[str, Any]) -> CustomerImpact:
        """Assess comprehensive customer impact"""
        severity = "medium"  # Default

        # Analyze severity indicators
        high_priority_count = len([r for r in results if "high" in r.summary.lower() or "critical" in r.summary.lower()])
        customer_escalation_count = len([r for r in results if "escalation" in r.summary.lower()])

        if customer_escalation_count > 3 or high_priority_count > 5:
            severity = "high"
        elif "sev-1" in issue.get("summary", "").lower() or "critical" in issue.get("priority", "").lower():
            severity = "critical"

        return CustomerImpact(
            severity=severity,
            affected_customers=[f"customer_{i}" for i in range(min(customer_escalation_count, 5))],
            business_functions=["data_discovery", "lineage_analysis", "governance_workflows"],
            revenue_impact="medium" if severity in ["high", "critical"] else "low",
            user_experience="degraded" if severity != "low" else "minimal_impact",
            escalation_risk="high" if severity == "critical" else "medium",
            mitigation_urgency="immediate" if severity == "critical" else "standard"
        )

    async def _generate_recommendations(self,
                                     issue: Dict[str, Any],
                                     phases: List[AnalysisPhaseResult],
                                     issue_type: IssueType) -> List[str]:
        """Generate actionable recommendations based on comprehensive analysis"""
        recommendations = []

        # Issue type specific recommendations
        if issue_type == IssueType.CUSTOMER_ESCALATION:
            recommendations.extend([
                "Immediate customer communication acknowledging issue and providing timeline",
                "Escalate to senior engineering for rapid resolution",
                "Document impact assessment for executive visibility"
            ])

        # Pattern-based recommendations
        all_patterns = []
        for phase in phases:
            all_patterns.extend(phase.patterns_identified)

        if any("timeout" in pattern.lower() for pattern in all_patterns):
            recommendations.extend([
                "Investigate frontend performance metrics and UI rendering bottlenecks",
                "Consider cluster resource optimization for improved response times",
                "Implement enhanced monitoring for UI performance degradation"
            ])

        if any("customer" in pattern.lower() for pattern in all_patterns):
            recommendations.extend([
                "Prioritize customer communication and stakeholder updates",
                "Establish regular status updates until resolution",
                "Consider workaround solutions for immediate customer relief"
            ])

        # Default systematic recommendations
        recommendations.extend([
            "Execute systematic debugging using identified technical patterns",
            "Leverage team expertise mapping for efficient resource allocation",
            "Monitor related issues for pattern recurrence prevention"
        ])

        return recommendations[:8]  # Limit to most actionable

    def _calculate_confidence_score(self, phases: List[AnalysisPhaseResult]) -> float:
        """Calculate confidence score based on analysis completeness and quality"""
        total_searches = sum(phase.search_count for phase in phases)
        total_results = sum(phase.results_found for phase in phases)

        # Base score on search comprehensiveness
        search_score = min(total_searches / 58.0, 1.0)  # 58 is minimum for comprehensive

        # Factor in result quality
        result_score = min(total_results / 100.0, 1.0) if total_results > 0 else 0.5

        # Phase completeness score
        phase_score = len(phases) / 7.0  # Should have all 7 phases

        # Weighted combination
        confidence = (search_score * 0.4) + (result_score * 0.3) + (phase_score * 0.3)

        return round(confidence, 2)

    def _generate_analysis_summary(self,
                                 issue: Dict[str, Any],
                                 issue_type: IssueType,
                                 phases: List[AnalysisPhaseResult],
                                 confidence: float) -> str:
        """Generate comprehensive analysis summary"""
        total_searches = sum(phase.search_count for phase in phases)
        total_results = sum(phase.results_found for phase in phases)

        summary = f"""
**Comprehensive 7-Dimensional Analysis Complete**

**Issue**: {issue.get('key')} - {issue.get('summary', 'No summary')}
**Classification**: {issue_type.value.replace('_', ' ').title()}
**Analysis Confidence**: {confidence:.0%}

**Search Intelligence**:
- **Total Searches Executed**: {total_searches} across 7 analytical dimensions
- **Results Analyzed**: {total_results} items across Jira and Confluence
- **Platforms Covered**: Comprehensive Jira + Confluence deep dive
- **Analysis Depth**: Multi-dimensional systematic investigation

**Key Insights**:
{chr(10).join([f"- {finding}" for phase in phases for finding in phase.key_findings[:2]])}

**Systemic Patterns Identified**:
{chr(10).join([f"- {pattern}" for phase in phases for pattern in phase.patterns_identified[:3]])}

**Analysis Methodology**: Applied systematic 7-phase framework including technical expansion, cross-platform analysis, temporal correlation, people network mapping, customer impact assessment, system layer correlation, and comprehensive pattern recognition.

**Confidence Factors**: Based on {len(phases)} completed analysis phases, {total_searches} systematic searches, and {total_results} analyzed data points across Alation's Atlassian ecosystem.
"""

        return summary.strip()

    # Placeholder implementations for additional helper methods
    def _convert_jira_issue_to_search_result(self, issue) -> SearchResult:
        """Convert JIRA issue to SearchResult format"""
        # Implementation would convert actual JIRA issue object
        pass

    def _convert_confluence_page_to_search_result(self, page) -> SearchResult:
        """Convert Confluence page to SearchResult format"""
        # Implementation would convert actual Confluence page object
        pass

    def _extract_cross_platform_insights(self, results: List[SearchResult]) -> List[str]:
        """Extract insights from cross-platform analysis"""
        return [f"Cross-platform insight {i}" for i in range(3)]

    def _identify_cross_platform_patterns(self, results: List[SearchResult]) -> List[str]:
        """Identify patterns across Jira and Confluence"""
        return [f"Cross-platform pattern {i}" for i in range(3)]

    def _build_temporal_timeline(self, results: List[SearchResult], anchor_date: datetime) -> List[Dict]:
        """Build temporal timeline of related events"""
        return [{"date": anchor_date, "event": "Issue created", "type": "milestone"}]

    def _identify_temporal_patterns(self, timeline: List[Dict]) -> List[str]:
        """Identify temporal patterns from timeline"""
        return ["Temporal pattern identified"]

    def _analyze_people_network(self, results: List[SearchResult]) -> List[str]:
        """Analyze people network for expertise mapping"""
        return ["Expert identified from network analysis"]

    def _map_expertise_areas(self, results: List[SearchResult], issue: Dict) -> Dict[str, List[str]]:
        """Map expertise areas to people"""
        return {"lineage": ["expert1@alation.com"], "connectors": ["expert2@alation.com"]}

    def _build_system_correlation_map(self, results: List[SearchResult]) -> List[str]:
        """Build system correlation map"""
        return ["lineage-service", "analytics", "connectors"]

    def _analyze_system_dependencies(self, results: List[SearchResult], issue: Dict) -> List[str]:
        """Analyze system dependencies"""
        return ["Critical dependency identified"]

    def _identify_systemic_patterns(self, results: List[SearchResult], phases: List[AnalysisPhaseResult]) -> List[str]:
        """Identify systemic patterns across all analysis"""
        return ["Systemic pattern across customer issues", "Performance pattern detected"]

    def _analyze_cross_domain_patterns(self, results: List[SearchResult]) -> List[str]:
        """Analyze cross-domain patterns"""
        return ["Cross-domain insight identified"]

    def _consolidate_affected_components(self, phases: List[AnalysisPhaseResult]) -> List[str]:
        """Consolidate affected components from all phases"""
        components = set()
        for phase in phases:
            for pattern in phase.patterns_identified:
                if any(comp in pattern.lower() for comp in self.alation_components):
                    for comp in self.alation_components:
                        if comp in pattern.lower():
                            components.add(comp)
        return list(components)

    def _extract_related_issues(self, results: List[SearchResult]) -> List[str]:
        """Extract related issue keys"""
        return [result.id for result in results if result.content_type == "jira_issue"][:10]

    def _consolidate_team_expertise(self, phases: List[AnalysisPhaseResult]) -> Dict[str, List[str]]:
        """Consolidate team expertise from people network analysis"""
        return {"lineage": ["expert@alation.com"], "engineering": ["dev@alation.com"]}

    def _build_comprehensive_timeline(self, phases: List[AnalysisPhaseResult]) -> List[Dict]:
        """Build comprehensive timeline from all phases"""
        timeline = []
        for phase in phases:
            timeline.append({
                "timestamp": phase.completion_time.isoformat(),
                "phase": phase.phase.value,
                "results": phase.results_found,
                "key_finding": phase.key_findings[0] if phase.key_findings else "Analysis completed"
            })
        return timeline

    def _synthesize_customer_impact(self, phases: List[AnalysisPhaseResult]) -> CustomerImpact:
        """Synthesize customer impact from analysis phases"""
        # Find customer impact phase results
        customer_phase = next((p for p in phases if p.phase == AnalysisPhase.CUSTOMER_IMPACT), None)

        if customer_phase and customer_phase.patterns_identified:
            severity_patterns = [p for p in customer_phase.patterns_identified if "severity:" in p.lower()]
            if severity_patterns:
                severity = severity_patterns[0].split(":")[1].strip().lower()
            else:
                severity = "medium"
        else:
            severity = "medium"

        return CustomerImpact(
            severity=severity,
            affected_customers=["customer_analysis_pending"],
            business_functions=["data_discovery", "lineage_analysis"],
            revenue_impact="medium" if severity in ["high", "critical"] else "low",
            user_experience="impacted" if severity != "low" else "minimal",
            escalation_risk="monitor" if severity == "low" else "elevated",
            mitigation_urgency="standard"
        )

    async def analyze_issue_correlation(self,
                                      issue_keys: List[str],
                                      analysis_scope: str = "customer_impact") -> Dict[str, Any]:
        """Analyze correlation between multiple issues"""
        logger.info(f"Analyzing correlation between issues: {', '.join(issue_keys)}")

        try:
            # Analyze each issue individually
            analyses = {}
            for issue_key in issue_keys:
                try:
                    analysis = await self.analyze_issue(issue_key, analysis_depth="focused")
                    analyses[issue_key] = analysis
                except Exception as e:
                    logger.warning(f"Failed to analyze {issue_key}: {e}")
                    continue

            # Find common patterns
            common_components = set()
            common_patterns = []
            confidence_scores = []

            if analyses:
                # Extract components and patterns
                all_components = []
                all_patterns = []

                for analysis in analyses.values():
                    all_components.extend(analysis.affected_components)
                    confidence_scores.append(analysis.confidence_score)

                    # Extract patterns from summary
                    if "database" in analysis.analysis_summary.lower():
                        all_patterns.append("database_related")
                    if "permission" in analysis.analysis_summary.lower():
                        all_patterns.append("permissions_related")
                    if "performance" in analysis.analysis_summary.lower():
                        all_patterns.append("performance_related")

                # Find common elements
                from collections import Counter
                component_counts = Counter(all_components)
                pattern_counts = Counter(all_patterns)

                common_components = [comp for comp, count in component_counts.items() if count > 1]
                common_patterns = [pattern for pattern, count in pattern_counts.items() if count > 1]

            # Calculate correlation strength
            correlation_strength = 0.0
            if len(analyses) >= 2:
                avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
                component_overlap = len(common_components) / max(len(set(all_components)), 1)
                pattern_overlap = len(common_patterns) / max(len(set(all_patterns)), 1)

                correlation_strength = min(1.0, (avg_confidence + component_overlap + pattern_overlap) / 3)

            # Generate recommendations
            recommendations = []
            if correlation_strength > 0.6:
                recommendations.extend([
                    "Strong correlation detected - investigate common root cause",
                    "Consider consolidated remediation approach",
                    "Prioritize fixes for shared components"
                ])
            elif correlation_strength > 0.3:
                recommendations.extend([
                    "Moderate correlation detected - monitor for patterns",
                    "Review shared components for potential improvements"
                ])
            else:
                recommendations.append("Low correlation - handle issues independently")

            return {
                "strength": correlation_strength,
                "patterns": common_patterns,
                "components": list(common_components),
                "recommendations": recommendations,
                "individual_analyses": len(analyses),
                "scope": analysis_scope
            }

        except Exception as e:
            logger.error(f"Failed to analyze issue correlation: {e}")
            return {
                "strength": 0.0,
                "patterns": [],
                "components": [],
                "recommendations": ["Error in correlation analysis - analyze issues individually"],
                "error": str(e)
            }

    async def analyze_historical_patterns(self,
                                        timeframe: str = "30d",
                                        pattern_type: str = "all") -> List[Dict[str, Any]]:
        """Analyze historical patterns from Atlassian data"""
        logger.info(f"Analyzing historical patterns for {timeframe}, type: {pattern_type}")

        try:
            # Build JQL query for historical data
            jql_query = f"created >= -{timeframe}"

            if pattern_type != "all":
                if pattern_type == "customer_impact":
                    jql_query += " AND (labels = customer-impact OR priority in (Critical, High))"
                elif pattern_type == "technical":
                    jql_query += " AND component in (Database, API, Performance)"
                elif pattern_type == "escalation":
                    jql_query += " AND priority = Critical"

            # Search for historical issues
            search_results = await self._search_jira(jql_query, max_results=100)

            if not search_results:
                return []

            # Analyze patterns
            patterns = []

            # Component frequency analysis
            components = []
            priorities = []
            statuses = []

            for result in search_results:
                if result.metadata:
                    components.extend(result.metadata.get("components", []))
                    priorities.append(result.metadata.get("priority", "Unknown"))
                    statuses.append(result.metadata.get("status", "Unknown"))

            # Generate pattern insights
            from collections import Counter

            if components:
                component_counts = Counter(components)
                patterns.append({
                    "type": "frequent_components",
                    "title": "Most Affected Components",
                    "data": dict(component_counts.most_common(5)),
                    "insight": f"Top component: {component_counts.most_common(1)[0][0]} ({component_counts.most_common(1)[0][1]} issues)"
                })

            if priorities:
                priority_counts = Counter(priorities)
                patterns.append({
                    "type": "priority_distribution",
                    "title": "Issue Priority Distribution",
                    "data": dict(priority_counts),
                    "insight": f"Most common priority: {priority_counts.most_common(1)[0][0]}"
                })

            # Temporal patterns
            monthly_counts = {}
            for result in search_results[:30]:  # Limit for performance
                # Extract month from timestamp (mock implementation)
                month = "2024-04"  # Would parse from result.timestamp
                monthly_counts[month] = monthly_counts.get(month, 0) + 1

            if monthly_counts:
                patterns.append({
                    "type": "temporal_trend",
                    "title": "Issue Frequency Over Time",
                    "data": monthly_counts,
                    "insight": f"Peak activity in: {max(monthly_counts, key=monthly_counts.get)}"
                })

            # Add summary pattern
            patterns.insert(0, {
                "type": "summary",
                "title": "Historical Analysis Summary",
                "data": {
                    "total_issues": len(search_results),
                    "timeframe": timeframe,
                    "patterns_found": len(patterns) - 1
                },
                "insight": f"Analyzed {len(search_results)} issues from last {timeframe}"
            })

            return patterns

        except Exception as e:
            logger.error(f"Failed to analyze historical patterns: {e}")
            return [{
                "type": "error",
                "title": "Pattern Analysis Error",
                "data": {"error": str(e)},
                "insight": "Unable to complete historical pattern analysis"
            }]