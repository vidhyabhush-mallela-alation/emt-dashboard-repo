#!/usr/bin/env python3
"""
EMT Dashboard Main Application
Integrates Regression Testing and Atlassian Context Enricher skills
"""

import asyncio
import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import aiofiles
from aiohttp import web, WSMsgType
from aiohttp.web_middlewares import middleware
import aiohttp_cors

# Import skills
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from skills.regression_testing.skill import RegressionTestingSkill, TestRun, TestStatus, Cluster
from skills.atlassian_context_enricher.skill import AtlassianContextEnricher, IssueAnalysis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EMTDashboard:
    """
    EMT Dashboard Application

    Combines Claude-powered skills for comprehensive EMT ticket management:
    - Regression Testing Skill: Automated test suite management
    - Atlassian Context Enricher: Deep issue analysis via Jira/Confluence
    """

    def __init__(self):
        self.app = web.Application(middlewares=[self.cors_middleware])
        self.websockets = set()
        self.db_path = Path(__file__).parent.parent.parent / "data" / "dashboard.db"

        # Initialize skills
        self.regression_skill = RegressionTestingSkill()
        self.atlassian_skill = AtlassianContextEnricher()

        # Active test runs and analyses
        self.active_test_runs: Dict[str, TestRun] = {}
        self.active_analyses: Dict[str, IssueAnalysis] = {}

        # Setup application
        self.setup_routes()
        self.setup_database()

    @middleware
    async def cors_middleware(self, request, handler):
        """CORS middleware for cross-origin requests"""
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def setup_routes(self):
        """Setup HTTP and WebSocket routes"""
        # Static files
        self.app.router.add_get('/', self.serve_dashboard)
        self.app.router.add_static('/static', Path(__file__).parent.parent.parent / 'static', name='static')

        # API v1 routes
        api_v1 = '/api/v1'

        # Dashboard overview
        self.app.router.add_get(f'{api_v1}/dashboard/overview', self.get_dashboard_overview)
        self.app.router.add_get(f'{api_v1}/dashboard/timeline', self.get_timeline)

        # Test management (Regression Testing Skill)
        self.app.router.add_get(f'{api_v1}/tests', self.get_all_tests)
        self.app.router.add_post(f'{api_v1}/tests/certification/trigger', self.trigger_certification_suite)
        self.app.router.add_get(f'{api_v1}/tests/{{test_id}}/status', self.get_test_status)
        self.app.router.add_get(f'{api_v1}/tests/{{test_id}}/results', self.get_test_results)
        self.app.router.add_post(f'{api_v1}/tests/{{test_id}}/analyze', self.analyze_test_failures)
        self.app.router.add_post(f'{api_v1}/tests/{{suite_id}}/trigger', self.trigger_single_test)

        # Issue analysis (Atlassian Context Enricher Skill)
        self.app.router.add_post(f'{api_v1}/analyze/issue', self.analyze_issue)
        self.app.router.add_get(f'{api_v1}/analyze/{{analysis_id}}/report', self.get_analysis_report)
        self.app.router.add_post(f'{api_v1}/analyze/correlation', self.analyze_issue_correlation)
        self.app.router.add_get(f'{api_v1}/analyze/patterns', self.get_pattern_analysis)

        # Integrated workflows
        self.app.router.add_post(f'{api_v1}/emt/{{ticket_id}}/full-analysis', self.full_emt_analysis)
        self.app.router.add_get(f'{api_v1}/emt/{{ticket_id}}/summary', self.get_emt_summary)

        # WebSocket for real-time updates
        self.app.router.add_get('/ws', self.websocket_handler)

        # Health checks
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/health/detailed', self.detailed_health_check)

    def setup_database(self):
        """Setup SQLite database for persistence"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Test runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_runs (
                id TEXT PRIMARY KEY,
                suite_id TEXT NOT NULL,
                build_number INTEGER,
                status TEXT NOT NULL,
                cluster TEXT NOT NULL,
                manifest TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                duration_seconds INTEGER,
                passed INTEGER DEFAULT 0,
                failed INTEGER DEFAULT 0,
                skipped INTEGER DEFAULT 0,
                total INTEGER DEFAULT 0,
                url TEXT NOT NULL,
                failures TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Issue analyses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS issue_analyses (
                id TEXT PRIMARY KEY,
                issue_key TEXT NOT NULL,
                issue_type TEXT NOT NULL,
                priority TEXT NOT NULL,
                customer_impact TEXT NOT NULL,
                root_cause_hypothesis TEXT,
                affected_components TEXT DEFAULT '[]',
                related_issues TEXT DEFAULT '[]',
                recommendations TEXT DEFAULT '[]',
                confidence_score REAL DEFAULT 0.0,
                analysis_summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Timeline events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timeline_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                related_id TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    # Dashboard and Static Routes

    async def serve_dashboard(self, request):
        """Serve main dashboard HTML"""
        try:
            dashboard_file = Path(__file__).parent.parent.parent / 'static' / 'dashboard.html'
            async with aiofiles.open(dashboard_file, 'r') as f:
                content = await f.read()
            return web.Response(text=content, content_type='text/html')
        except FileNotFoundError:
            return web.Response(
                text="<h1>EMT Dashboard</h1><p>Dashboard UI not found. Please check static files.</p>",
                content_type='text/html'
            )

    # API Routes - Dashboard Overview

    async def get_dashboard_overview(self, request):
        """Get dashboard overview with test and analysis summaries"""
        try:
            # Get test summary
            test_summary = await self._get_test_summary()

            # Get recent analyses
            analysis_summary = await self._get_analysis_summary()

            # Get recent timeline events
            timeline_events = await self._get_recent_timeline_events(10)

            overview = {
                "last_updated": datetime.now().isoformat(),
                "test_summary": test_summary,
                "analysis_summary": analysis_summary,
                "recent_events": timeline_events,
                "system_status": {
                    "regression_skill": "active",
                    "atlassian_skill": "active",
                    "database": "connected",
                    "websocket_clients": len(self.websockets)
                }
            }

            return web.json_response(overview)

        except Exception as e:
            logger.error(f"Failed to get dashboard overview: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_timeline(self, request):
        """Get timeline events with filtering"""
        try:
            limit = int(request.query.get('limit', 50))
            event_type = request.query.get('type')

            events = await self._get_timeline_events(limit, event_type)
            return web.json_response(events)

        except Exception as e:
            logger.error(f"Failed to get timeline: {e}")
            return web.json_response({"error": str(e)}, status=500)

    # API Routes - Test Management (Regression Testing Skill)

    async def get_all_tests(self, request):
        """Get all test runs"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM test_runs
                ORDER BY updated_at DESC
                LIMIT 100
            """)

            tests = []
            for row in cursor.fetchall():
                test = {
                    "id": row[0],
                    "suite_id": row[1],
                    "build_number": row[2],
                    "status": row[3],
                    "cluster": row[4],
                    "manifest": row[5],
                    "started_at": row[6],
                    "completed_at": row[7],
                    "duration_seconds": row[8],
                    "passed": row[9],
                    "failed": row[10],
                    "skipped": row[11],
                    "total": row[12],
                    "url": row[13],
                    "failures": json.loads(row[14] or '[]')
                }
                tests.append(test)

            conn.close()
            return web.json_response(tests)

        except Exception as e:
            logger.error(f"Failed to get tests: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def trigger_certification_suite(self, request):
        """Trigger complete lineage certification test suite"""
        try:
            data = await request.json()

            manifest = data.get('manifest')
            cluster_name = data.get('cluster', 'qa-enterprise-use1')
            jira_key = data.get('jira_key')
            suites = data.get('suites')  # Optional subset

            if not manifest:
                return web.json_response({"error": "manifest is required"}, status=400)

            try:
                cluster = Cluster(cluster_name)
            except ValueError:
                return web.json_response({"error": f"Invalid cluster: {cluster_name}"}, status=400)

            # Trigger certification suite using regression testing skill
            test_runs = await self.regression_skill.trigger_certification_suite(
                manifest=manifest,
                cluster=cluster,
                jira_key=jira_key,
                suites=suites
            )

            # Store test runs in database
            for test_run in test_runs.values():
                await self._store_test_run(test_run)

            # Add to active runs
            self.active_test_runs.update({run.id: run for run in test_runs.values()})

            # Add timeline event
            await self._add_timeline_event(
                "test_suite_triggered",
                f"Certification suite triggered: {len(test_runs)} suites",
                f"Manifest: {manifest[:50]}..., Cluster: {cluster_name}",
                metadata={
                    "manifest": manifest,
                    "cluster": cluster_name,
                    "jira_key": jira_key,
                    "suite_count": len(test_runs)
                }
            )

            # Broadcast to WebSocket clients
            await self._broadcast_update({
                "type": "certification_triggered",
                "test_runs": [{"id": run.id, "suite_id": run.suite_id, "status": run.status.value}
                             for run in test_runs.values()]
            })

            return web.json_response({
                "status": "triggered",
                "test_runs": [{"id": run.id, "suite_id": run.suite_id, "url": run.url}
                             for run in test_runs.values()]
            })

        except Exception as e:
            logger.error(f"Failed to trigger certification suite: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_test_status(self, request):
        """Get current status of a test run"""
        try:
            test_id = request.match_info['test_id']

            # Get from active runs first
            if test_id in self.active_test_runs:
                test_run = self.active_test_runs[test_id]

                # Update status using regression skill
                updated_run = await self.regression_skill.get_test_status(test_run)

                # Update in memory and database
                self.active_test_runs[test_id] = updated_run
                await self._store_test_run(updated_run)

                return web.json_response({
                    "id": updated_run.id,
                    "status": updated_run.status.value,
                    "passed": updated_run.passed,
                    "failed": updated_run.failed,
                    "total": updated_run.total,
                    "url": updated_run.url,
                    "last_updated": datetime.now().isoformat()
                })

            # Fallback to database
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM test_runs WHERE id = ?", (test_id,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                return web.json_response({"error": "Test not found"}, status=404)

            return web.json_response({
                "id": row[0],
                "status": row[3],
                "passed": row[9],
                "failed": row[10],
                "total": row[12],
                "url": row[13]
            })

        except Exception as e:
            logger.error(f"Failed to get test status: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def analyze_test_failures(self, request):
        """Analyze test failures using regression testing skill"""
        try:
            test_id = request.match_info['test_id']

            # Get test run
            if test_id not in self.active_test_runs:
                return web.json_response({"error": "Test run not found"}, status=404)

            test_run = self.active_test_runs[test_id]

            if test_run.status not in [TestStatus.UNSTABLE, TestStatus.FAILED]:
                return web.json_response({"error": "No failures to analyze"}, status=400)

            # Analyze failures using skill
            analysis = await self.regression_skill.analyze_failure_patterns([test_run])

            # Generate recommendations
            recommendations = await self.regression_skill.recommend_actions(analysis, [test_run])

            result = {
                "test_id": test_id,
                "analysis": {
                    "failure_type": analysis.failure_type,
                    "root_cause": analysis.root_cause,
                    "severity": analysis.severity,
                    "affected_components": analysis.affected_components,
                    "customer_impact": analysis.customer_impact
                },
                "recommendations": recommendations,
                "analyzed_at": datetime.now().isoformat()
            }

            return web.json_response(result)

        except Exception as e:
            logger.error(f"Failed to analyze test failures: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_test_results(self, request):
        """Get detailed test results"""
        try:
            test_id = request.match_info['test_id']

            # Get test run from active runs or database
            if test_id in self.active_test_runs:
                test_run = self.active_test_runs[test_id]
            else:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM test_runs WHERE id = ?", (test_id,))
                row = cursor.fetchone()
                conn.close()

                if not row:
                    return web.json_response({"error": "Test not found"}, status=404)

                return web.json_response({
                    "id": row[0],
                    "suite_id": row[1],
                    "build_number": row[2],
                    "status": row[3],
                    "cluster": row[4],
                    "manifest": row[5],
                    "started_at": row[6],
                    "completed_at": row[7],
                    "duration_seconds": row[8],
                    "passed": row[9],
                    "failed": row[10],
                    "skipped": row[11],
                    "total": row[12],
                    "url": row[13],
                    "failures": json.loads(row[14] or '[]')
                })

            return web.json_response({
                "id": test_run.id,
                "suite_id": test_run.suite_id,
                "build_number": test_run.build_number,
                "status": test_run.status.value,
                "cluster": test_run.cluster.value,
                "manifest": test_run.manifest,
                "started_at": test_run.started_at.isoformat(),
                "completed_at": test_run.completed_at.isoformat() if test_run.completed_at else None,
                "duration_seconds": test_run.duration_seconds,
                "passed": test_run.passed,
                "failed": test_run.failed,
                "skipped": test_run.skipped,
                "total": test_run.total,
                "url": test_run.url,
                "failures": test_run.failures
            })

        except Exception as e:
            logger.error(f"Failed to get test results: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def trigger_single_test(self, request):
        """Trigger a single test suite"""
        try:
            suite_id = request.match_info['suite_id']
            data = await request.json()

            manifest = data.get('manifest')
            cluster_name = data.get('cluster', 'qa-enterprise-use1')
            jira_key = data.get('jira_key')

            if not manifest:
                return web.json_response({"error": "manifest is required"}, status=400)

            try:
                cluster = Cluster(cluster_name)
            except ValueError:
                return web.json_response({"error": f"Invalid cluster: {cluster_name}"}, status=400)

            # Trigger single test suite
            test_run = await self.regression_skill.trigger_single_suite(
                suite_id=suite_id,
                manifest=manifest,
                cluster=cluster,
                jira_key=jira_key
            )

            # Store test run
            await self._store_test_run(test_run)
            self.active_test_runs[test_run.id] = test_run

            # Add timeline event
            await self._add_timeline_event(
                "single_test_triggered",
                f"Test suite {suite_id} triggered",
                f"Manifest: {manifest[:50]}..., Cluster: {cluster_name}",
                related_id=test_run.id,
                metadata={
                    "suite_id": suite_id,
                    "manifest": manifest,
                    "cluster": cluster_name,
                    "jira_key": jira_key
                }
            )

            return web.json_response({
                "status": "triggered",
                "test_run": {
                    "id": test_run.id,
                    "suite_id": test_run.suite_id,
                    "url": test_run.url,
                    "status": test_run.status.value
                }
            })

        except Exception as e:
            logger.error(f"Failed to trigger single test: {e}")
            return web.json_response({"error": str(e)}, status=500)

    # API Routes - Issue Analysis (Atlassian Context Enricher Skill)

    async def analyze_issue(self, request):
        """Analyze issue using Atlassian Context Enricher skill"""
        try:
            data = await request.json()

            issue_key = data.get('issue_key')
            analysis_depth = data.get('analysis_depth', 'comprehensive')
            focus_areas = data.get('focus_areas')

            if not issue_key:
                return web.json_response({"error": "issue_key is required"}, status=400)

            # Execute analysis using skill
            analysis = await self.atlassian_skill.analyze_issue(
                issue_key=issue_key,
                analysis_depth=analysis_depth,
                focus_areas=focus_areas
            )

            # Store analysis
            analysis_id = f"analysis_{issue_key}_{int(datetime.now().timestamp())}"
            self.active_analyses[analysis_id] = analysis
            await self._store_issue_analysis(analysis_id, analysis)

            # Add timeline event
            await self._add_timeline_event(
                "issue_analysis_completed",
                f"7-dimensional analysis completed for {issue_key}",
                f"Confidence: {analysis.confidence_score:.0%}, Type: {analysis.issue_type.value}",
                related_id=analysis_id,
                metadata={
                    "issue_key": issue_key,
                    "confidence_score": analysis.confidence_score,
                    "issue_type": analysis.issue_type.value
                }
            )

            # Broadcast to WebSocket clients
            await self._broadcast_update({
                "type": "analysis_completed",
                "analysis_id": analysis_id,
                "issue_key": issue_key,
                "confidence": analysis.confidence_score
            })

            return web.json_response({
                "analysis_id": analysis_id,
                "issue_key": issue_key,
                "status": "completed",
                "confidence_score": analysis.confidence_score,
                "summary": analysis.analysis_summary[:200] + "..." if len(analysis.analysis_summary) > 200 else analysis.analysis_summary,
                "recommendations_count": len(analysis.recommendations),
                "related_issues_count": len(analysis.related_issues)
            })

        except Exception as e:
            logger.error(f"Failed to analyze issue: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_analysis_report(self, request):
        """Get complete analysis report"""
        try:
            analysis_id = request.match_info['analysis_id']

            if analysis_id in self.active_analyses:
                analysis = self.active_analyses[analysis_id]
            else:
                # Try to load from database
                analysis = await self._load_issue_analysis(analysis_id)
                if not analysis:
                    return web.json_response({"error": "Analysis not found"}, status=404)

            return web.json_response({
                "analysis_id": analysis_id,
                "issue_key": analysis.issue_key,
                "issue_type": analysis.issue_type.value,
                "priority": analysis.priority,
                "customer_impact": analysis.customer_impact,
                "root_cause_hypothesis": analysis.root_cause_hypothesis,
                "affected_components": analysis.affected_components,
                "related_issues": analysis.related_issues,
                "recommendations": analysis.recommendations,
                "confidence_score": analysis.confidence_score,
                "analysis_summary": analysis.analysis_summary,
                "phase_results": [
                    {
                        "phase": phase.phase.value,
                        "search_count": phase.search_count,
                        "results_found": phase.results_found,
                        "key_findings": phase.key_findings,
                        "patterns_identified": phase.patterns_identified
                    }
                    for phase in analysis.phase_results
                ]
            })

        except Exception as e:
            logger.error(f"Failed to get analysis report: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def analyze_issue_correlation(self, request):
        """Analyze correlation between multiple issues"""
        try:
            data = await request.json()
            issue_keys = data.get('issue_keys', [])
            analysis_scope = data.get('analysis_scope', 'customer_impact')

            if not issue_keys or len(issue_keys) < 2:
                return web.json_response({"error": "At least 2 issue keys required"}, status=400)

            # Execute correlation analysis using Atlassian skill
            correlation_analysis = await self.atlassian_skill.analyze_issue_correlation(
                issue_keys=issue_keys,
                analysis_scope=analysis_scope
            )

            return web.json_response({
                "correlation_id": f"corr_{int(datetime.now().timestamp())}",
                "issue_keys": issue_keys,
                "analysis_scope": analysis_scope,
                "correlation_strength": correlation_analysis.get("strength", 0.0),
                "common_patterns": correlation_analysis.get("patterns", []),
                "shared_components": correlation_analysis.get("components", []),
                "recommendations": correlation_analysis.get("recommendations", [])
            })

        except Exception as e:
            logger.error(f"Failed to analyze issue correlation: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_pattern_analysis(self, request):
        """Get pattern analysis from historical data"""
        try:
            timeframe = request.query.get('timeframe', '30d')
            pattern_type = request.query.get('type', 'all')

            # Get pattern analysis using Atlassian skill
            patterns = await self.atlassian_skill.analyze_historical_patterns(
                timeframe=timeframe,
                pattern_type=pattern_type
            )

            return web.json_response({
                "timeframe": timeframe,
                "pattern_type": pattern_type,
                "patterns_found": len(patterns),
                "patterns": patterns,
                "generated_at": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Failed to get pattern analysis: {e}")
            return web.json_response({"error": str(e)}, status=500)

    # Integrated Workflows

    async def full_emt_analysis(self, request):
        """Execute full EMT ticket analysis combining both skills"""
        try:
            ticket_id = request.match_info['ticket_id']
            data = await request.json()

            # Extract parameters
            manifest = data.get('manifest')
            cluster_name = data.get('cluster', 'qa-enterprise-use1')
            analysis_depth = data.get('analysis_depth', 'comprehensive')

            # Phase 1: Atlassian Context Analysis
            issue_analysis = await self.atlassian_skill.analyze_issue(
                issue_key=ticket_id,
                analysis_depth=analysis_depth
            )

            # Phase 2: Regression Testing (if manifest provided)
            test_results = {}
            if manifest:
                cluster = Cluster(cluster_name)
                test_results = await self.regression_skill.trigger_certification_suite(
                    manifest=manifest,
                    cluster=cluster,
                    jira_key=ticket_id
                )

                # Store test runs
                for test_run in test_results.values():
                    await self._store_test_run(test_run)
                    self.active_test_runs[test_run.id] = test_run

            # Store analysis
            analysis_id = f"full_analysis_{ticket_id}_{int(datetime.now().timestamp())}"
            self.active_analyses[analysis_id] = issue_analysis
            await self._store_issue_analysis(analysis_id, issue_analysis)

            # Generate comprehensive summary
            summary = {
                "ticket_id": ticket_id,
                "analysis_id": analysis_id,
                "issue_analysis": {
                    "confidence_score": issue_analysis.confidence_score,
                    "issue_type": issue_analysis.issue_type.value,
                    "customer_impact": issue_analysis.customer_impact,
                    "recommendations_count": len(issue_analysis.recommendations)
                },
                "test_analysis": {
                    "suites_triggered": len(test_results),
                    "test_runs": [
                        {"id": run.id, "suite_id": run.suite_id, "status": run.status.value}
                        for run in test_results.values()
                    ] if test_results else []
                },
                "started_at": datetime.now().isoformat()
            }

            # Add comprehensive timeline event
            await self._add_timeline_event(
                "full_emt_analysis",
                f"Full EMT analysis initiated for {ticket_id}",
                f"Issue analysis + {len(test_results)} test suites triggered",
                related_id=analysis_id,
                metadata=summary
            )

            return web.json_response(summary)

        except Exception as e:
            logger.error(f"Failed to execute full EMT analysis: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_emt_summary(self, request):
        """Get summary of EMT ticket analysis and testing"""
        try:
            ticket_id = request.match_info['ticket_id']

            # Find analyses for this ticket
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Get issue analyses
            cursor.execute("""
                SELECT * FROM issue_analyses
                WHERE issue_key = ?
                ORDER BY created_at DESC
            """, (ticket_id,))

            analyses = []
            for row in cursor.fetchall():
                analyses.append({
                    "id": row[0],
                    "confidence_score": row[9],
                    "issue_type": row[2],
                    "customer_impact": row[4],
                    "created_at": row[11]
                })

            # Get test runs
            cursor.execute("""
                SELECT * FROM test_runs
                WHERE manifest LIKE ?
                ORDER BY started_at DESC
            """, (f"%{ticket_id}%",))

            test_runs = []
            for row in cursor.fetchall():
                test_runs.append({
                    "id": row[0],
                    "suite_id": row[1],
                    "status": row[3],
                    "passed": row[9],
                    "failed": row[10],
                    "total": row[12],
                    "started_at": row[6]
                })

            conn.close()

            summary = {
                "ticket_id": ticket_id,
                "analyses_count": len(analyses),
                "test_runs_count": len(test_runs),
                "latest_analysis": analyses[0] if analyses else None,
                "recent_test_runs": test_runs[:5],  # Last 5 test runs
                "overall_status": self._calculate_emt_status(analyses, test_runs),
                "generated_at": datetime.now().isoformat()
            }

            return web.json_response(summary)

        except Exception as e:
            logger.error(f"Failed to get EMT summary: {e}")
            return web.json_response({"error": str(e)}, status=500)

    def _calculate_emt_status(self, analyses, test_runs):
        """Calculate overall EMT ticket status"""
        if not analyses and not test_runs:
            return "no_data"

        # Check latest analysis confidence
        latest_analysis = analyses[0] if analyses else None
        high_confidence = latest_analysis and latest_analysis["confidence_score"] > 0.8

        # Check test results
        recent_tests = test_runs[:3] if test_runs else []
        tests_passing = all(run["failed"] == 0 for run in recent_tests if run["total"] > 0)

        if high_confidence and tests_passing:
            return "resolved"
        elif high_confidence or tests_passing:
            return "in_progress"
        else:
            return "investigating"

    # WebSocket Handler

    async def websocket_handler(self, request):
        """Handle WebSocket connections for real-time updates"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self.websockets.add(ws)
        logger.info(f"WebSocket client connected. Total: {len(self.websockets)}")

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_websocket_message(ws, data)
                    except json.JSONDecodeError:
                        await ws.send_str(json.dumps({"error": "Invalid JSON"}))

                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")

        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.websockets.discard(ws)
            logger.info(f"WebSocket client disconnected. Total: {len(self.websockets)}")

        return ws

    async def _handle_websocket_message(self, ws, data):
        """Handle incoming WebSocket messages"""
        message_type = data.get('type')

        if message_type == 'subscribe_updates':
            await ws.send_str(json.dumps({
                "type": "subscription_confirmed",
                "message": "Subscribed to real-time updates"
            }))

        elif message_type == 'get_status':
            # Send current dashboard status
            status = await self._get_current_status()
            await ws.send_str(json.dumps({
                "type": "status_update",
                "data": status
            }))

    # Health Checks

    async def health_check(self, request):
        """Basic health check"""
        return web.json_response({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        })

    async def detailed_health_check(self, request):
        """Detailed health check with skill status"""
        try:
            db_status = "connected"
            try:
                conn = sqlite3.connect(str(self.db_path))
                conn.close()
            except:
                db_status = "error"

            return web.json_response({
                "status": "healthy",
                "components": {
                    "database": db_status,
                    "regression_skill": "active",
                    "atlassian_skill": "active",
                    "websockets": {"active_connections": len(self.websockets)}
                },
                "metrics": {
                    "active_test_runs": len(self.active_test_runs),
                    "active_analyses": len(self.active_analyses),
                    "uptime": "runtime_calculation_needed"
                },
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            return web.json_response({
                "status": "error",
                "error": str(e)
            }, status=500)

    # Helper Methods

    async def _store_test_run(self, test_run: TestRun):
        """Store test run in database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO test_runs
            (id, suite_id, build_number, status, cluster, manifest, started_at,
             completed_at, duration_seconds, passed, failed, skipped, total, url, failures)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_run.id, test_run.suite_id, test_run.build_number, test_run.status.value,
            test_run.cluster.value, test_run.manifest, test_run.started_at.isoformat(),
            test_run.completed_at.isoformat() if test_run.completed_at else None,
            test_run.duration_seconds, test_run.passed, test_run.failed, test_run.skipped,
            test_run.total, test_run.url, json.dumps(test_run.failures)
        ))

        conn.commit()
        conn.close()

    async def _store_issue_analysis(self, analysis_id: str, analysis: IssueAnalysis):
        """Store issue analysis in database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO issue_analyses
            (id, issue_key, issue_type, priority, customer_impact, root_cause_hypothesis,
             affected_components, related_issues, recommendations, confidence_score, analysis_summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            analysis_id, analysis.issue_key, analysis.issue_type.value, analysis.priority,
            analysis.customer_impact, analysis.root_cause_hypothesis,
            json.dumps(analysis.affected_components), json.dumps(analysis.related_issues),
            json.dumps(analysis.recommendations), analysis.confidence_score, analysis.analysis_summary
        ))

        conn.commit()
        conn.close()

    async def _add_timeline_event(self, event_type: str, title: str, description: str = "",
                                related_id: str = None, metadata: Dict = None):
        """Add timeline event"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO timeline_events (timestamp, event_type, title, description, related_id, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(), event_type, title, description, related_id,
            json.dumps(metadata or {})
        ))

        conn.commit()
        conn.close()

    async def _broadcast_update(self, data: Dict):
        """Broadcast update to all WebSocket clients"""
        if not self.websockets:
            return

        message = json.dumps(data)
        closed_sockets = set()

        for ws in self.websockets:
            try:
                await ws.send_str(message)
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")
                closed_sockets.add(ws)

        # Clean up closed connections
        self.websockets -= closed_sockets

    async def _get_test_summary(self):
        """Get test summary for dashboard"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT status, COUNT(*) FROM test_runs
            GROUP BY status
        """)

        status_counts = dict(cursor.fetchall())

        cursor.execute("""
            SELECT COUNT(*) FROM test_runs
            WHERE started_at >= datetime('now', '-24 hours')
        """)

        recent_count = cursor.fetchone()[0]

        conn.close()

        return {
            "total_runs": sum(status_counts.values()),
            "status_breakdown": status_counts,
            "recent_24h": recent_count,
            "active_runs": len([run for run in self.active_test_runs.values()
                              if run.status in [TestStatus.RUNNING, TestStatus.QUEUED]])
        }

    async def _get_analysis_summary(self):
        """Get analysis summary for dashboard"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*), AVG(confidence_score) FROM issue_analyses
        """)

        count, avg_confidence = cursor.fetchone()

        conn.close()

        return {
            "total_analyses": count or 0,
            "average_confidence": avg_confidence or 0.0,
            "active_analyses": len(self.active_analyses)
        }

    async def _get_recent_timeline_events(self, limit: int = 10):
        """Get recent timeline events"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT timestamp, event_type, title, description, related_id
            FROM timeline_events
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

        events = []
        for row in cursor.fetchall():
            events.append({
                "timestamp": row[0],
                "event_type": row[1],
                "title": row[2],
                "description": row[3],
                "related_id": row[4]
            })

        conn.close()
        return events

    async def _get_current_status(self):
        """Get current dashboard status"""
        return {
            "active_test_runs": len(self.active_test_runs),
            "active_analyses": len(self.active_analyses),
            "websocket_clients": len(self.websockets),
            "timestamp": datetime.now().isoformat()
        }

    def run(self, host='0.0.0.0', port=8080, debug=False):
        """Run the dashboard application"""
        logger.info(f"Starting EMT Dashboard on {host}:{port}")
        logger.info("Skills loaded: Regression Testing + Atlassian Context Enricher")

        # Start background tasks
        async def start_background_tasks():
            # Start periodic status updates
            asyncio.create_task(self._periodic_status_updates())

        # Setup and run
        web.run_app(
            self.app,
            host=host,
            port=port,
            access_log=logger if debug else None
        )

    async def _periodic_status_updates(self):
        """Periodic status updates and cleanup"""
        while True:
            try:
                # Update active test runs
                for test_id, test_run in list(self.active_test_runs.items()):
                    if test_run.status in [TestStatus.RUNNING, TestStatus.QUEUED]:
                        updated_run = await self.regression_skill.get_test_status(test_run)
                        self.active_test_runs[test_id] = updated_run
                        await self._store_test_run(updated_run)

                # Broadcast status update to WebSocket clients
                if self.websockets:
                    status = await self._get_current_status()
                    await self._broadcast_update({
                        "type": "periodic_update",
                        "status": status
                    })

                # Wait 30 seconds before next update
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Error in periodic status updates: {e}")
                await asyncio.sleep(60)  # Longer wait on error


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="EMT Dashboard with Claude Skills")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Initialize and run dashboard
    dashboard = EMTDashboard()
    dashboard.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()