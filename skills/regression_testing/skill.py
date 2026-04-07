#!/usr/bin/env python3
"""
Regression Testing Skill for Alation EMT Dashboard
Comprehensive test suite management with Claude MCP integration
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class TestStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    UNSTABLE = "unstable"
    FAILED = "failed"
    ABORTED = "aborted"

class Cluster(Enum):
    USE1 = "qa-enterprise-use1"
    USE2 = "qa-enterprise-use2"
    USW2 = "qa-enterprise-usw2"
    DEV = "development-enterprise-use1"

@dataclass
class TestSuite:
    """Test suite configuration"""
    id: str
    name: str
    job_path: str
    expected_tests: int
    timeout_minutes: int
    framework: str  # selenium, playwright, tavern, github_actions
    parameters: Dict[str, Any]

@dataclass
class TestRun:
    """Test run instance"""
    id: str
    suite_id: str
    build_number: int
    status: TestStatus
    cluster: Cluster
    manifest: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    total: int = 0
    url: str = ""
    failures: List[Dict] = None

    def __post_init__(self):
        if self.failures is None:
            self.failures = []

@dataclass
class FailureAnalysis:
    """Analysis of test failure"""
    failure_type: str
    root_cause: str
    severity: str  # low, medium, high, critical
    affected_components: List[str]
    recommendations: List[str]
    similar_failures: List[str]
    customer_impact: str

class RegressionTestingSkill:
    """
    Regression Testing Skill for Alation Feature Branches

    Provides comprehensive test suite management including:
    - Triggering all 6 lineage certification test suites
    - Monitoring Jenkins builds via MCP tools
    - Analyzing failure patterns with Claude intelligence
    - Managing different clusters and configurations
    """

    def __init__(self, claude_mcp_client=None):
        self.mcp_client = claude_mcp_client

        # Test suite configurations
        self.test_suites = {
            "selenium_qli": TestSuite(
                id="selenium_qli",
                name="Selenium QLI",
                job_path="alation_selenium/master/test_selenium_zeus",
                expected_tests=4,
                timeout_minutes=120,
                framework="selenium",
                parameters={
                    "GAUGE_SPEC_TAG_PARAM": "qli",
                    "BROWSER_NAME_PARAM": "Chrome(Headless)",
                    "FEATURE_FLAGS_TYPE_PARAM": "flags_on",
                    "USE_SHARED_RDS": True,
                    "RETRY_FAILED_JOB": True,
                    "RETRY_FAILED_TESTS": True
                }
            ),
            "tavern_static_ds": TestSuite(
                id="tavern_static_ds",
                name="Tavern Static DS",
                job_path="datasources/master/datasources_test_tavernapi/tavernapi_test_zeus/test_release_zeus_api_multiple_static_ds",
                expected_tests=42,
                timeout_minutes=180,
                framework="tavern",
                parameters={
                    "DB_TYPE": "bigquery,snowflake,virtual",
                    "API_TEST_TAVERN_MARKS_PARAM": "lineage_squad_certification",
                    "PID1_DEPLOYMENT": True
                }
            ),
            "tavern_provisioned_ds": TestSuite(
                id="tavern_provisioned_ds",
                name="Tavern Provisioned DS",
                job_path="datasources/master/datasources_test_tavernapi/tavernapi_test_zeus/test_release_zeus_api_multiple_ds",
                expected_tests=6,
                timeout_minutes=200,
                framework="tavern",
                parameters={
                    "DB_TYPE": "oracleec2,postgresec2,redshift,sqlserverec2",
                    "API_TEST_TAVERN_MARKS_PARAM": "lineage_squad_certification",
                    "PID1_DEPLOYMENT": True
                }
            ),
            "playwright_snowflake": TestSuite(
                id="playwright_snowflake",
                name="Playwright Snowflake",
                job_path="datasources/master/playwright_connector/zeus/test_release_zeus_static_ds",
                expected_tests=127,
                timeout_minutes=180,
                framework="playwright",
                parameters={
                    "ALATION_UI_BRANCH": "main",
                    "SQUAD_NAME": "lineage",
                    "DB_TYPE": "snowflake",
                    "TAG": "lineage_squad_certification",
                    "CONNECTOR_TEST_TYPE": "ocf-selenium"
                }
            ),
            "playwright_databricks": TestSuite(
                id="playwright_databricks",
                name="Playwright Databricks",
                job_path="datasources/master/playwright_connector/zeus/test_release_zeus",
                expected_tests=29,
                timeout_minutes=160,
                framework="playwright",
                parameters={
                    "ALATION_UI_BRANCH": "main",
                    "SQUAD_NAME": "lineage",
                    "DB_TYPE": "databricks_unity",
                    "TAG": "lineage_squad_certification",
                    "CONNECTOR_TEST_TYPE": "ocf-selenium"
                }
            ),
            "github_actions_e2e": TestSuite(
                id="github_actions_e2e",
                name="GitHub Actions E2E",
                job_path="Alation/alation-ui",  # GitHub Actions workflow
                expected_tests=8,
                timeout_minutes=90,
                framework="github_actions",
                parameters={
                    "workflow": "e2e-with-tenant-provisoning.yaml",
                    "PLAYWRIGHT_TAGS_PARAM": "@lineage_squad_certification",
                    "TENANT_TYPE": "enterprise",
                    "DESTROY_TENANT_AFTER_TESTS": True,
                    "ENABLE_E2E_RETRY": True
                }
            )
        }

    async def trigger_certification_suite(self,
                                        manifest: str,
                                        cluster: Cluster = Cluster.USE1,
                                        jira_key: str = None,
                                        suites: List[str] = None) -> Dict[str, TestRun]:
        """
        Trigger complete lineage certification test suite

        Args:
            manifest: Manifest version (e.g., "26.4.0.0-alation-1.87.1-...")
            cluster: Target cluster for deployment
            jira_key: JIRA ticket ID (e.g., "EMT-224570")
            suites: Specific test suites to run (defaults to all)

        Returns:
            Dictionary of test suite ID -> TestRun
        """
        if suites is None:
            suites = list(self.test_suites.keys())

        logger.info(f"Triggering certification suite for {manifest} on {cluster.value}")

        triggered_runs = {}

        for suite_id in suites:
            if suite_id not in self.test_suites:
                logger.warning(f"Unknown test suite: {suite_id}")
                continue

            try:
                test_run = await self._trigger_single_test(
                    suite_id, manifest, cluster, jira_key
                )
                triggered_runs[suite_id] = test_run

                logger.info(f"Triggered {suite_id}: {test_run.url}")

            except Exception as e:
                logger.error(f"Failed to trigger {suite_id}: {e}")

        return triggered_runs

    async def trigger_single_suite(self,
                                 suite_id: str,
                                 manifest: str,
                                 cluster: Cluster = Cluster.USE1,
                                 jira_key: str = None) -> TestRun:
        """Trigger a single test suite (public method)"""
        if suite_id not in self.test_suites:
            raise ValueError(f"Unknown test suite: {suite_id}")

        logger.info(f"Triggering single suite {suite_id} for {manifest} on {cluster.value}")

        return await self._trigger_single_test(suite_id, manifest, cluster, jira_key)

    async def _trigger_single_test(self,
                                 suite_id: str,
                                 manifest: str,
                                 cluster: Cluster,
                                 jira_key: str) -> TestRun:
        """Trigger a single test suite"""
        suite = self.test_suites[suite_id]

        # Build parameters
        parameters = suite.parameters.copy()
        parameters.update({
            "MANIFEST_VERSION": manifest,
            "CLUSTER": cluster.value
        })

        if jira_key:
            parameters["TF_VAR_jirakey"] = jira_key

        # Handle framework-specific triggering
        if suite.framework == "github_actions":
            return await self._trigger_github_actions(suite, parameters)
        else:
            return await self._trigger_jenkins_job(suite, parameters, cluster)

    async def _trigger_jenkins_job(self,
                                 suite: TestSuite,
                                 parameters: Dict,
                                 cluster: Cluster) -> TestRun:
        """Trigger Jenkins job via MCP"""
        try:
            if self.mcp_client:
                result = await self.mcp_client.call("mcp__jenkins__triggerBuild", {
                    "jobFullName": suite.job_path,
                    "parameters": parameters
                })

                # Extract queue ID and build info
                queue_id = result.get("result", {}).get("id")
                build_number = await self._wait_for_build_start(suite.job_path, queue_id)
            else:
                # Mock for development/testing
                build_number = 9999

            # Create test run record
            test_run = TestRun(
                id=f"{suite.id}_{build_number}",
                suite_id=suite.id,
                build_number=build_number,
                status=TestStatus.QUEUED,
                cluster=cluster,
                manifest=parameters.get("MANIFEST_VERSION", ""),
                started_at=datetime.now(),
                total=suite.expected_tests,
                url=self._build_jenkins_url(suite.job_path, build_number)
            )

            return test_run

        except Exception as e:
            logger.error(f"Failed to trigger Jenkins job {suite.job_path}: {e}")
            raise

    async def _trigger_github_actions(self,
                                    suite: TestSuite,
                                    parameters: Dict) -> TestRun:
        """Trigger GitHub Actions workflow"""
        try:
            # Use gh CLI via subprocess or GitHub API
            # This would integrate with GitHub Actions API

            # Mock implementation for now
            run_id = "24041609999"

            test_run = TestRun(
                id=f"{suite.id}_{run_id}",
                suite_id=suite.id,
                build_number=int(run_id),
                status=TestStatus.QUEUED,
                cluster=Cluster.USE1,  # GHA provisions its own tenant
                manifest=parameters.get("MANIFEST_VERSION", ""),
                started_at=datetime.now(),
                total=suite.expected_tests,
                url=f"https://github.com/{suite.job_path}/actions/runs/{run_id}"
            )

            return test_run

        except Exception as e:
            logger.error(f"Failed to trigger GitHub Actions {suite.job_path}: {e}")
            raise

    async def _wait_for_build_start(self, job_path: str, queue_id: int) -> int:
        """Wait for queued build to start and return build number"""
        if not self.mcp_client or not queue_id:
            return 9999  # Mock build number

        for attempt in range(30):  # Wait up to 5 minutes
            try:
                result = await self.mcp_client.call("mcp__jenkins__getQueueItem", {
                    "id": queue_id
                })

                queue_item = result.get("result", {})
                executable = queue_item.get("executable")

                if executable:
                    return executable.get("number", 9999)

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.warning(f"Queue check attempt {attempt}: {e}")
                await asyncio.sleep(10)

        logger.warning(f"Timeout waiting for build start: {job_path}")
        return 9999

    def _build_jenkins_url(self, job_path: str, build_number: int) -> str:
        """Build Jenkins build URL"""
        job_url = job_path.replace("/", "/job/")
        return f"https://jenkins.alation-labs.com/job/{job_url}/{build_number}/"

    async def get_test_status(self, test_run: TestRun) -> TestRun:
        """Get current status of a test run"""
        try:
            if test_run.suite_id == "github_actions_e2e":
                return await self._get_github_actions_status(test_run)
            else:
                return await self._get_jenkins_status(test_run)

        except Exception as e:
            logger.error(f"Failed to get status for {test_run.id}: {e}")
            return test_run

    async def _get_jenkins_status(self, test_run: TestRun) -> TestRun:
        """Get Jenkins build status via MCP"""
        if not self.mcp_client:
            return test_run  # Return unchanged if no MCP client

        try:
            suite = self.test_suites[test_run.suite_id]

            result = await self.mcp_client.call("mcp__jenkins__getBuild", {
                "jobFullName": suite.job_path,
                "buildNumber": test_run.build_number
            })

            build_data = result.get("result", {})

            # Update test run with current data
            test_run.status = self._map_jenkins_status(build_data.get("result"))

            # If completed, get test results
            if test_run.status in [TestStatus.SUCCESS, TestStatus.UNSTABLE, TestStatus.FAILED]:
                if not test_run.completed_at:
                    test_run.completed_at = datetime.now()
                    test_run.duration_seconds = build_data.get("duration", 0) // 1000

                # Get detailed test results
                await self._update_test_results(test_run, suite)

            return test_run

        except Exception as e:
            logger.error(f"Failed to get Jenkins status: {e}")
            return test_run

    async def _get_github_actions_status(self, test_run: TestRun) -> TestRun:
        """Get GitHub Actions status"""
        # This would use GitHub API or gh CLI
        # Mock implementation for now
        return test_run

    async def _update_test_results(self, test_run: TestRun, suite: TestSuite):
        """Update test run with detailed test results"""
        if not self.mcp_client:
            return

        try:
            result = await self.mcp_client.call("mcp__jenkins__getTestResults", {
                "jobFullName": suite.job_path,
                "buildNumber": test_run.build_number
            })

            test_data = result.get("result", {})
            test_action = test_data.get("TestResultAction", {})

            # Update counts
            test_run.total = test_action.get("totalCount", suite.expected_tests)
            test_run.failed = test_action.get("failCount", 0)
            test_run.skipped = test_action.get("skipCount", 0)
            test_run.passed = test_run.total - test_run.failed - test_run.skipped

            # Extract failure details
            failing_tests = test_data.get("failingTests", [])
            test_run.failures = []

            for failure in failing_tests[:5]:  # Limit to 5 failures
                test_run.failures.append({
                    "test_name": failure.get("name", "Unknown"),
                    "class_name": failure.get("className", ""),
                    "error_message": failure.get("errorDetails", ""),
                    "duration": failure.get("duration", 0)
                })

        except Exception as e:
            logger.error(f"Failed to get test results: {e}")

    def _map_jenkins_status(self, jenkins_result: str) -> TestStatus:
        """Map Jenkins result to TestStatus"""
        mapping = {
            "SUCCESS": TestStatus.SUCCESS,
            "UNSTABLE": TestStatus.UNSTABLE,
            "FAILURE": TestStatus.FAILED,
            "ABORTED": TestStatus.ABORTED,
            None: TestStatus.RUNNING  # Still building
        }
        return mapping.get(jenkins_result, TestStatus.RUNNING)

    async def analyze_failure_patterns(self, test_runs: List[TestRun]) -> FailureAnalysis:
        """
        Analyze failure patterns across test runs using Claude intelligence

        This method identifies common failure patterns, root causes, and provides
        actionable recommendations for fixing issues.
        """
        failed_runs = [run for run in test_runs if run.status in [TestStatus.UNSTABLE, TestStatus.FAILED]]

        if not failed_runs:
            return FailureAnalysis(
                failure_type="No Failures",
                root_cause="All tests passing",
                severity="low",
                affected_components=[],
                recommendations=["Continue monitoring"],
                similar_failures=[],
                customer_impact="None"
            )

        # Analyze failure patterns
        failure_types = self._categorize_failures(failed_runs)
        affected_components = self._identify_affected_components(failed_runs)

        # Determine primary failure type and severity
        primary_failure = max(failure_types.items(), key=lambda x: x[1])
        failure_type = primary_failure[0]

        # Generate analysis based on patterns
        if "UI_TIMEOUT" in failure_type:
            return FailureAnalysis(
                failure_type="UI Performance Issue",
                root_cause="Frontend rendering delays affecting lineage visualization components",
                severity="high",
                affected_components=["lineage-ui", "frontend-performance"],
                recommendations=[
                    "Switch to qa-enterprise-use2 cluster to isolate performance issues",
                    "Investigate lineage tab rendering performance",
                    "Check cluster resource utilization",
                    "Consider UI timeout threshold adjustments"
                ],
                similar_failures=[run.id for run in failed_runs if "timeout" in str(run.failures).lower()],
                customer_impact="Users may experience slow lineage visualization loading"
            )

        elif "SQL_SERVER_MDE" in failure_type:
            return FailureAnalysis(
                failure_type="SQL Server MDE Status Issue",
                root_cause="Known flaky behavior in SQL Server connector status reporting",
                severity="medium",
                affected_components=["sql-server-connector", "mde-status"],
                recommendations=[
                    "Monitor for consistent pattern across multiple runs",
                    "Check SQL Server connector version and compatibility",
                    "Verify MDE status reporting logic",
                    "Consider status validation improvements"
                ],
                similar_failures=[run.id for run in failed_runs if "sql" in run.suite_id.lower()],
                customer_impact="SQL Server customers may see inconsistent MDE status reporting"
            )

        elif "INFRASTRUCTURE" in failure_type:
            return FailureAnalysis(
                failure_type="Infrastructure Failure",
                root_cause="Build infrastructure or environment setup issues",
                severity="critical",
                affected_components=["jenkins", "github-actions", "infrastructure"],
                recommendations=[
                    "Retrigger failed jobs to verify if issue persists",
                    "Check Jenkins/GitHub Actions system status",
                    "Verify cluster connectivity and resource availability",
                    "Investigate infrastructure logs for root cause"
                ],
                similar_failures=[run.id for run in failed_runs if run.status == TestStatus.FAILED],
                customer_impact="Deployment pipeline reliability affected"
            )

        else:
            return FailureAnalysis(
                failure_type="Mixed Failures",
                root_cause="Multiple failure types detected requiring individual investigation",
                severity="medium",
                affected_components=affected_components,
                recommendations=[
                    "Investigate each failure type separately",
                    "Prioritize by customer impact and frequency",
                    "Consider partial retrigger for specific suites",
                    "Implement additional monitoring for failure patterns"
                ],
                similar_failures=[run.id for run in failed_runs],
                customer_impact="Various customer workflows may be affected"
            )

    def _categorize_failures(self, failed_runs: List[TestRun]) -> Dict[str, int]:
        """Categorize failures by type"""
        categories = {}

        for run in failed_runs:
            for failure in run.failures:
                error_msg = failure.get("error_message", "").lower()

                if "timeout" in error_msg and "lineage" in error_msg:
                    categories["UI_TIMEOUT"] = categories.get("UI_TIMEOUT", 0) + 1
                elif "partial_success" in error_msg and "sql" in error_msg:
                    categories["SQL_SERVER_MDE"] = categories.get("SQL_SERVER_MDE", 0) + 1
                elif run.status == TestStatus.FAILED and not run.failures:
                    categories["INFRASTRUCTURE"] = categories.get("INFRASTRUCTURE", 0) + 1
                else:
                    categories["OTHER"] = categories.get("OTHER", 0) + 1

        return categories

    def _identify_affected_components(self, failed_runs: List[TestRun]) -> List[str]:
        """Identify affected system components"""
        components = set()

        for run in failed_runs:
            if "selenium" in run.suite_id:
                components.add("selenium-tests")
            elif "playwright" in run.suite_id:
                components.add("playwright-tests")
            elif "tavern" in run.suite_id:
                components.add("api-tests")
            elif "github" in run.suite_id:
                components.add("github-actions")

            # Add framework-specific components
            if run.failures:
                for failure in run.failures:
                    error_msg = failure.get("error_message", "").lower()
                    if "lineage" in error_msg:
                        components.add("lineage-service")
                    if "ui" in error_msg or "frontend" in error_msg:
                        components.add("frontend")
                    if "database" in error_msg or "sql" in error_msg:
                        components.add("database")

        return list(components)

    async def recommend_actions(self, analysis: FailureAnalysis, test_runs: List[TestRun]) -> List[Dict[str, Any]]:
        """
        Generate actionable recommendations based on failure analysis

        Returns prioritized list of actions with implementation details
        """
        actions = []

        # High priority actions for critical issues
        if analysis.severity == "critical":
            actions.append({
                "priority": "critical",
                "action": "immediate_retrigger",
                "title": "Immediate Infrastructure Investigation",
                "description": "Critical infrastructure failure detected",
                "steps": [
                    "Check Jenkins/GitHub Actions system status",
                    "Verify cluster health and resource availability",
                    "Review infrastructure logs for errors",
                    "Retrigger failed jobs after verification"
                ],
                "estimated_time": "15-30 minutes",
                "automation_possible": True
            })

        # UI performance issues
        if "UI" in analysis.failure_type or "timeout" in analysis.root_cause.lower():
            actions.append({
                "priority": "high",
                "action": "cluster_switch",
                "title": "Switch to Alternative Cluster",
                "description": "UI timeouts detected, test performance on different cluster",
                "steps": [
                    "Retrigger failed tests on qa-enterprise-use2",
                    "Compare performance metrics between clusters",
                    "Investigate cluster-specific resource constraints",
                    "Monitor UI response times during execution"
                ],
                "estimated_time": "2-3 hours",
                "automation_possible": True,
                "cluster_target": "qa-enterprise-use2"
            })

            actions.append({
                "priority": "medium",
                "action": "ui_investigation",
                "title": "Frontend Performance Analysis",
                "description": "Investigate lineage UI rendering performance",
                "steps": [
                    "Review browser network timings in test logs",
                    "Check for JavaScript errors in console logs",
                    "Analyze DOM rendering performance",
                    "Consider timeout threshold adjustments"
                ],
                "estimated_time": "1-2 hours",
                "automation_possible": False
            })

        # SQL Server specific issues
        if "SQL" in analysis.failure_type:
            actions.append({
                "priority": "medium",
                "action": "connector_investigation",
                "title": "SQL Server Connector Analysis",
                "description": "Investigate SQL Server MDE status inconsistencies",
                "steps": [
                    "Check SQL Server connector version compatibility",
                    "Review MDE processing logs for partial success patterns",
                    "Verify status reporting logic in connector code",
                    "Monitor pattern across multiple test runs"
                ],
                "estimated_time": "1 hour",
                "automation_possible": False
            })

        # General monitoring and prevention
        actions.append({
            "priority": "low",
            "action": "enhanced_monitoring",
            "title": "Implement Enhanced Monitoring",
            "description": "Add monitoring to prevent future similar failures",
            "steps": [
                "Set up alerts for UI timeout patterns",
                "Implement cluster performance monitoring",
                "Add failure pattern detection automation",
                "Create dashboards for test reliability metrics"
            ],
            "estimated_time": "4-6 hours",
            "automation_possible": True
        })

        # Retrigger recommendations
        failed_runs = [run for run in test_runs if run.status in [TestStatus.UNSTABLE, TestStatus.FAILED]]
        if failed_runs:
            retrigger_suites = [run.suite_id for run in failed_runs]
            actions.append({
                "priority": "high" if len(failed_runs) > 2 else "medium",
                "action": "selective_retrigger",
                "title": "Retrigger Failed Test Suites",
                "description": f"Retrigger {len(failed_runs)} failed test suites",
                "steps": [
                    f"Retrigger test suites: {', '.join(retrigger_suites)}",
                    "Monitor execution for pattern recurrence",
                    "Compare results with previous run",
                    "Document any persistent failures"
                ],
                "estimated_time": "3-4 hours",
                "automation_possible": True,
                "retrigger_suites": retrigger_suites
            })

        return sorted(actions, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}[x["priority"]])

    def get_certification_summary(self, test_runs: List[TestRun]) -> Dict[str, Any]:
        """
        Generate certification summary for EMT ticket

        Provides executive summary suitable for EMT ticket comments and stakeholder updates
        """
        total_suites = len(test_runs)
        if not test_runs:
            return {"status": "No tests executed", "summary": "No test data available"}

        # Count by status
        status_counts = {}
        for run in test_runs:
            status_counts[run.status.value] = status_counts.get(run.status.value, 0) + 1

        success_count = status_counts.get("success", 0)
        unstable_count = status_counts.get("unstable", 0)
        failed_count = status_counts.get("failed", 0)
        running_count = status_counts.get("running", 0)

        # Overall certification status
        if failed_count > 0:
            overall_status = "BLOCKED"
        elif unstable_count > 2:
            overall_status = "CONDITIONAL"
        elif running_count > 0:
            overall_status = "IN_PROGRESS"
        elif success_count == total_suites:
            overall_status = "CERTIFIED"
        else:
            overall_status = "PARTIAL"

        # Calculate total test metrics
        total_tests = sum(run.total for run in test_runs)
        total_passed = sum(run.passed for run in test_runs)
        total_failed = sum(run.failed for run in test_runs)

        # Generate summary text
        summary_lines = [
            f"**Lineage Certification Status: {overall_status}**",
            f"",
            f"**Test Suite Results ({success_count}/{total_suites} fully passed):**"
        ]

        for run in test_runs:
            status_emoji = {
                "success": "✅",
                "unstable": "⚠️",
                "failed": "❌",
                "running": "🔄",
                "queued": "⏳"
            }.get(run.status.value, "❓")

            summary_lines.append(
                f"- {status_emoji} **{run.suite_id}**: {run.passed}/{run.total} passed "
                f"({run.status.value.upper()}) - [Build {run.build_number}]({run.url})"
            )

        if unstable_count > 0 or failed_count > 0:
            summary_lines.extend([
                f"",
                f"**Issues Requiring Attention:**"
            ])

            for run in test_runs:
                if run.status in [TestStatus.UNSTABLE, TestStatus.FAILED] and run.failures:
                    summary_lines.append(f"- **{run.suite_id}**: {len(run.failures)} failure(s)")
                    for failure in run.failures[:2]:  # Show top 2 failures
                        summary_lines.append(f"  - {failure.get('test_name', 'Unknown test')}")

        summary_lines.extend([
            f"",
            f"**Overall Test Metrics:**",
            f"- Total Tests: {total_tests}",
            f"- Passed: {total_passed} ({total_passed/total_tests*100:.1f}%)" if total_tests > 0 else "- Passed: 0",
            f"- Failed: {total_failed}",
            f"- Test Suites: {success_count} ✅, {unstable_count} ⚠️, {failed_count} ❌, {running_count} 🔄"
        ])

        return {
            "overall_status": overall_status,
            "success_rate": total_passed / total_tests if total_tests > 0 else 0,
            "suite_success_rate": success_count / total_suites if total_suites > 0 else 0,
            "summary": "\n".join(summary_lines),
            "metrics": {
                "total_suites": total_suites,
                "success_count": success_count,
                "unstable_count": unstable_count,
                "failed_count": failed_count,
                "running_count": running_count,
                "total_tests": total_tests,
                "total_passed": total_passed,
                "total_failed": total_failed
            },
            "test_runs": [asdict(run) for run in test_runs]
        }