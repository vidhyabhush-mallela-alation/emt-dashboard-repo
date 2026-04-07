"""
Release Analyzer - Intelligent analysis of QLI & Parser image releases
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from .extractor import ImageMetadata

logger = logging.getLogger(__name__)

@dataclass
class RiskAssessment:
    """Risk assessment for image deployment"""
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    risk_factors: List[str]
    recommendations: List[str]
    required_tests: List[str]
    rollback_plan: str
    confidence_score: float  # 0.0 to 1.0

@dataclass
class DeploymentRecommendation:
    """Deployment recommendation based on analysis"""
    should_deploy: bool
    deployment_strategy: str  # 'immediate', 'staged', 'canary', 'hold'
    required_approvals: List[str]
    monitoring_requirements: List[str]
    success_criteria: List[str]
    rollback_triggers: List[str]

class ReleaseAnalyzer:
    """
    Intelligent analyzer for QLI and Parser image releases
    Provides risk assessment, deployment recommendations, and test planning
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Risk assessment thresholds
        self.risk_thresholds = {
            'version_jump': {
                'major': 0.8,  # High risk for major version jumps
                'minor': 0.4,  # Medium risk for minor version jumps
                'patch': 0.1   # Low risk for patch releases
            },
            'time_since_last': {
                'high_risk_days': 7,    # High risk if less than 7 days since last
                'medium_risk_days': 14   # Medium risk if less than 14 days
            },
            'jira_ticket_count': {
                'high_risk': 10,    # High risk if >10 tickets
                'medium_risk': 5    # Medium risk if >5 tickets
            }
        }

        # Known compatibility issues database
        self.known_issues = {
            'qli': {
                'snowflake': ['connection_timeout', 'large_result_set'],
                'databricks': ['unity_catalog', 'delta_table_format'],
                'bigquery': ['nested_schema', 'array_columns']
            },
            'parser': {
                'postgresql': ['json_operators', 'window_functions'],
                'oracle': ['pl_sql_blocks', 'hierarchical_queries'],
                'sqlserver': ['cte_syntax', 'merge_statements']
            }
        }

    async def analyze_release(self, metadata: ImageMetadata,
                            previous_metadata: Optional[ImageMetadata] = None) -> Tuple[RiskAssessment, DeploymentRecommendation]:
        """
        Comprehensive analysis of image release including risk assessment and deployment recommendations
        """
        logger.info(f"Analyzing release for {metadata.image_tag}")

        # Parallel analysis tasks
        tasks = [
            self._assess_version_risk(metadata, previous_metadata),
            self._assess_compatibility_risk(metadata),
            self._assess_timeline_risk(metadata),
            self._assess_change_complexity(metadata),
            self._assess_test_coverage(metadata)
        ]

        risk_assessments = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine risk assessments
        combined_risk = self._combine_risk_assessments(risk_assessments, metadata)

        # Generate deployment recommendation
        deployment_rec = self._generate_deployment_recommendation(combined_risk, metadata)

        return combined_risk, deployment_rec

    async def _assess_version_risk(self, metadata: ImageMetadata,
                                 previous_metadata: Optional[ImageMetadata] = None) -> Dict[str, Any]:
        """Assess risk based on version changes"""
        try:
            if not previous_metadata:
                return {
                    'risk_level': 'medium',
                    'factors': ['No previous version for comparison'],
                    'confidence': 0.5
                }

            current_version = self._parse_version(metadata.version)
            previous_version = self._parse_version(previous_metadata.version)

            risk_level = 'low'
            factors = []
            confidence = 0.9

            # Major version change
            if current_version[0] > previous_version[0]:
                risk_level = 'high'
                factors.append('Major version increment detected')
                confidence = 0.95

            # Minor version change
            elif current_version[1] > previous_version[1]:
                if current_version[1] - previous_version[1] > 2:
                    risk_level = 'medium'
                    factors.append('Significant minor version jump')
                else:
                    risk_level = 'low'
                    factors.append('Minor version increment')

            # Patch version
            else:
                factors.append('Patch release - minimal risk expected')

            return {
                'risk_level': risk_level,
                'factors': factors,
                'confidence': confidence
            }

        except Exception as e:
            logger.error(f"Version risk assessment failed: {e}")
            return {'risk_level': 'medium', 'factors': ['Version analysis failed'], 'confidence': 0.3}

    async def _assess_compatibility_risk(self, metadata: ImageMetadata) -> Dict[str, Any]:
        """Assess compatibility risks based on known issues"""
        try:
            risk_level = 'low'
            factors = []
            confidence = 0.8

            image_type = metadata.image_type
            known_db_issues = self.known_issues.get(image_type, {})

            if metadata.compatibility_info:
                supported_dbs = metadata.compatibility_info.get('supported_databases', [])

                for db in supported_dbs:
                    if db in known_db_issues:
                        risk_level = 'medium'
                        factors.append(f'Known issues with {db}: {", ".join(known_db_issues[db])}')

            # Check for new database support
            if image_type == 'qli' and metadata.compatibility_info:
                connector_reqs = metadata.compatibility_info.get('connector_requirements', {})
                for connector, version in connector_reqs.items():
                    if 'beta' in version.lower() or 'alpha' in version.lower():
                        risk_level = 'high'
                        factors.append(f'Using beta/alpha connector: {connector} {version}')

            return {
                'risk_level': risk_level,
                'factors': factors or ['No known compatibility issues'],
                'confidence': confidence
            }

        except Exception as e:
            logger.error(f"Compatibility risk assessment failed: {e}")
            return {'risk_level': 'medium', 'factors': ['Compatibility analysis failed'], 'confidence': 0.3}

    async def _assess_timeline_risk(self, metadata: ImageMetadata) -> Dict[str, Any]:
        """Assess risk based on deployment timeline"""
        try:
            risk_level = 'low'
            factors = []
            confidence = 0.7

            if metadata.build_date:
                days_old = (datetime.now() - metadata.build_date).days

                if days_old < 1:
                    risk_level = 'high'
                    factors.append('Very recent build - insufficient soak time')
                elif days_old < 3:
                    risk_level = 'medium'
                    factors.append('Recent build - limited testing time')
                elif days_old > 30:
                    risk_level = 'medium'
                    factors.append('Old build - may contain outdated dependencies')
                else:
                    factors.append('Build age is appropriate for deployment')

            else:
                factors.append('Build date unknown - assess deployment timeline manually')
                confidence = 0.5

            return {
                'risk_level': risk_level,
                'factors': factors,
                'confidence': confidence
            }

        except Exception as e:
            logger.error(f"Timeline risk assessment failed: {e}")
            return {'risk_level': 'medium', 'factors': ['Timeline analysis failed'], 'confidence': 0.3}

    async def _assess_change_complexity(self, metadata: ImageMetadata) -> Dict[str, Any]:
        """Assess risk based on change complexity"""
        try:
            risk_level = 'low'
            factors = []
            confidence = 0.6

            # Assess based on number of Jira tickets
            ticket_count = len(metadata.jira_tickets)

            if ticket_count >= self.risk_thresholds['jira_ticket_count']['high_risk']:
                risk_level = 'high'
                factors.append(f'High change volume: {ticket_count} associated tickets')
            elif ticket_count >= self.risk_thresholds['jira_ticket_count']['medium_risk']:
                risk_level = 'medium'
                factors.append(f'Medium change volume: {ticket_count} associated tickets')
            else:
                factors.append(f'Low change volume: {ticket_count} associated tickets')

            # Assess based on release notes content
            if metadata.release_notes:
                critical_keywords = ['breaking', 'incompatible', 'deprecated', 'removed']
                for note in metadata.release_notes:
                    if any(keyword in note.lower() for keyword in critical_keywords):
                        risk_level = 'high'
                        factors.append('Breaking changes detected in release notes')
                        break

            return {
                'risk_level': risk_level,
                'factors': factors,
                'confidence': confidence
            }

        except Exception as e:
            logger.error(f"Change complexity assessment failed: {e}")
            return {'risk_level': 'medium', 'factors': ['Change analysis failed'], 'confidence': 0.3}

    async def _assess_test_coverage(self, metadata: ImageMetadata) -> Dict[str, Any]:
        """Assess risk based on available test coverage"""
        try:
            risk_level = 'low'
            factors = []
            confidence = 0.8

            # This would integrate with actual test results in production
            # For now, simulate based on image type and version

            if metadata.image_type == 'qli':
                expected_tests = ['ingestion_rate', 'data_quality', 'connector_compatibility']
                factors.append('QLI test suite: ingestion, quality, compatibility')
            else:  # parser
                expected_tests = ['parsing_accuracy', 'performance', 'dialect_support']
                factors.append('Parser test suite: accuracy, performance, dialects')

            # Check if this is a major version (higher test requirements)
            version_parts = self._parse_version(metadata.version)
            if version_parts[0] > 0:  # Not a 0.x version
                factors.append('Production version - full test suite required')
            else:
                risk_level = 'medium'
                factors.append('Pre-release version - enhanced testing recommended')

            return {
                'risk_level': risk_level,
                'factors': factors,
                'confidence': confidence
            }

        except Exception as e:
            logger.error(f"Test coverage assessment failed: {e}")
            return {'risk_level': 'medium', 'factors': ['Test analysis failed'], 'confidence': 0.3}

    def _combine_risk_assessments(self, risk_assessments: List[Any], metadata: ImageMetadata) -> RiskAssessment:
        """Combine individual risk assessments into overall assessment"""

        valid_assessments = [r for r in risk_assessments if isinstance(r, dict)]

        if not valid_assessments:
            return RiskAssessment(
                risk_level='high',
                risk_factors=['Risk assessment failed'],
                recommendations=['Manual review required'],
                required_tests=['Full regression test suite'],
                rollback_plan='Immediate rollback on any issues',
                confidence_score=0.1
            )

        # Calculate overall risk level
        risk_scores = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        max_risk = max(risk_scores.get(r.get('risk_level', 'medium'), 2) for r in valid_assessments)

        risk_levels = {1: 'low', 2: 'medium', 3: 'high', 4: 'critical'}
        overall_risk = risk_levels[max_risk]

        # Combine factors
        all_factors = []
        for assessment in valid_assessments:
            all_factors.extend(assessment.get('factors', []))

        # Calculate confidence
        confidences = [r.get('confidence', 0.5) for r in valid_assessments]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5

        # Generate recommendations based on risk level
        recommendations = self._generate_risk_recommendations(overall_risk, metadata)
        required_tests = self._generate_required_tests(overall_risk, metadata)
        rollback_plan = self._generate_rollback_plan(overall_risk, metadata)

        return RiskAssessment(
            risk_level=overall_risk,
            risk_factors=all_factors,
            recommendations=recommendations,
            required_tests=required_tests,
            rollback_plan=rollback_plan,
            confidence_score=avg_confidence
        )

    def _generate_deployment_recommendation(self, risk_assessment: RiskAssessment,
                                         metadata: ImageMetadata) -> DeploymentRecommendation:
        """Generate deployment recommendation based on risk assessment"""

        risk_level = risk_assessment.risk_level

        if risk_level == 'low':
            strategy = 'staged'
            should_deploy = True
            approvals = ['Tech Lead']
        elif risk_level == 'medium':
            strategy = 'canary'
            should_deploy = True
            approvals = ['Tech Lead', 'QA Lead']
        elif risk_level == 'high':
            strategy = 'staged'
            should_deploy = False  # Requires manual approval
            approvals = ['Tech Lead', 'QA Lead', 'Engineering Manager']
        else:  # critical
            strategy = 'hold'
            should_deploy = False
            approvals = ['Tech Lead', 'QA Lead', 'Engineering Manager', 'VP Engineering']

        monitoring_requirements = self._generate_monitoring_requirements(metadata)
        success_criteria = self._generate_success_criteria(metadata)
        rollback_triggers = self._generate_rollback_triggers(metadata)

        return DeploymentRecommendation(
            should_deploy=should_deploy,
            deployment_strategy=strategy,
            required_approvals=approvals,
            monitoring_requirements=monitoring_requirements,
            success_criteria=success_criteria,
            rollback_triggers=rollback_triggers
        )

    def _generate_risk_recommendations(self, risk_level: str, metadata: ImageMetadata) -> List[str]:
        """Generate risk-specific recommendations"""
        base_recs = [
            'Review all release notes and associated Jira tickets',
            'Verify compatibility with current production environment'
        ]

        if risk_level in ['medium', 'high', 'critical']:
            base_recs.extend([
                'Run full regression test suite before deployment',
                'Coordinate with on-call team for deployment window'
            ])

        if risk_level in ['high', 'critical']:
            base_recs.extend([
                'Prepare detailed rollback plan with specific steps',
                'Schedule deployment during low-traffic hours',
                'Have senior engineer available during deployment'
            ])

        if metadata.image_type == 'qli':
            base_recs.append('Monitor ingestion rates closely post-deployment')
        else:  # parser
            base_recs.append('Validate parsing accuracy with production queries')

        return base_recs

    def _generate_required_tests(self, risk_level: str, metadata: ImageMetadata) -> List[str]:
        """Generate required tests based on risk level"""
        base_tests = ['Unit tests', 'Integration tests']

        if risk_level in ['medium', 'high', 'critical']:
            base_tests.extend(['Performance regression tests', 'Compatibility tests'])

        if risk_level in ['high', 'critical']:
            base_tests.extend(['Full end-to-end tests', 'Stress tests', 'Failover tests'])

        if metadata.image_type == 'qli':
            base_tests.extend(['Ingestion volume tests', 'Data quality validation'])
        else:  # parser
            base_tests.extend(['SQL dialect tests', 'Parsing accuracy validation'])

        return base_tests

    def _generate_rollback_plan(self, risk_level: str, metadata: ImageMetadata) -> str:
        """Generate rollback plan based on risk level"""
        if risk_level == 'low':
            return 'Standard rollback: revert to previous image tag if issues detected'
        elif risk_level == 'medium':
            return 'Prepared rollback: have rollback commands ready, execute within 15 minutes of issue detection'
        elif risk_level == 'high':
            return 'Immediate rollback: automated monitoring with 5-minute rollback SLA'
        else:  # critical
            return 'Zero-downtime rollback: blue/green deployment with instant switchback capability'

    def _generate_monitoring_requirements(self, metadata: ImageMetadata) -> List[str]:
        """Generate monitoring requirements"""
        base_monitoring = [
            'Application health checks',
            'Error rate monitoring',
            'Performance metrics tracking'
        ]

        if metadata.image_type == 'qli':
            base_monitoring.extend([
                'Ingestion rate monitoring',
                'Queue depth tracking',
                'Data quality metrics'
            ])
        else:  # parser
            base_monitoring.extend([
                'Parsing success rate',
                'Response time monitoring',
                'Memory usage tracking'
            ])

        return base_monitoring

    def _generate_success_criteria(self, metadata: ImageMetadata) -> List[str]:
        """Generate success criteria for deployment"""
        base_criteria = [
            'All health checks passing for 30 minutes',
            'Error rate within normal baseline',
            'No critical alerts triggered'
        ]

        if metadata.image_type == 'qli':
            base_criteria.extend([
                'Ingestion rate matches or exceeds baseline',
                'Data quality metrics stable',
                'No ingestion pipeline failures'
            ])
        else:  # parser
            base_criteria.extend([
                'Parsing accuracy maintains 99.9%+',
                'Response times within SLA',
                'Memory usage stable'
            ])

        return base_criteria

    def _generate_rollback_triggers(self, metadata: ImageMetadata) -> List[str]:
        """Generate rollback triggers"""
        base_triggers = [
            'Error rate >5% above baseline',
            'Critical health check failures',
            'Memory/CPU usage >150% of baseline'
        ]

        if metadata.image_type == 'qli':
            base_triggers.extend([
                'Ingestion rate drops >20%',
                'Data quality issues detected',
                'Pipeline failures >3 in 10 minutes'
            ])
        else:  # parser
            base_triggers.extend([
                'Parsing accuracy drops below 99%',
                'Response time >200% of baseline',
                'Parser crashes or hangs'
            ])

        return base_triggers

    def _parse_version(self, version_str: str) -> Tuple[int, int, int]:
        """Parse version string into (major, minor, patch) tuple"""
        try:
            parts = version_str.split('.')
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            return (major, minor, patch)
        except (ValueError, IndexError):
            return (0, 0, 0)

    def generate_analysis_report(self, risk_assessment: RiskAssessment,
                               deployment_rec: DeploymentRecommendation,
                               metadata: ImageMetadata) -> str:
        """Generate comprehensive analysis report"""

        report = f"""
# {metadata.image_type.upper()} Image Deployment Analysis

**Image:** `{metadata.image_tag}`
**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Risk Assessment

**Overall Risk Level:** {risk_assessment.risk_level.upper()}
**Confidence Score:** {risk_assessment.confidence_score:.1%}

### Risk Factors
"""

        for factor in risk_assessment.risk_factors:
            report += f"- {factor}\n"

        report += f"""

### Recommendations
"""
        for rec in risk_assessment.recommendations:
            report += f"- {rec}\n"

        report += f"""

## Deployment Recommendation

**Should Deploy:** {'✅ Yes' if deployment_rec.should_deploy else '❌ No (requires approval)'}
**Strategy:** {deployment_rec.deployment_strategy.title()}

### Required Approvals
"""
        for approval in deployment_rec.required_approvals:
            report += f"- [ ] {approval}\n"

        report += f"""

### Required Tests
"""
        for test in risk_assessment.required_tests:
            report += f"- [ ] {test}\n"

        report += f"""

### Success Criteria
"""
        for criteria in deployment_rec.success_criteria:
            report += f"- [ ] {criteria}\n"

        report += f"""

### Rollback Plan
{risk_assessment.rollback_plan}

### Rollback Triggers
"""
        for trigger in deployment_rec.rollback_triggers:
            report += f"- {trigger}\n"

        report += f"""

### Monitoring Requirements
"""
        for requirement in deployment_rec.monitoring_requirements:
            report += f"- {requirement}\n"

        return report