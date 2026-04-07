"""
Image Release Extractor - Extract release notes from QLI & Parser image tags
"""

import re
import json
import asyncio
import aiohttp
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
import subprocess
import logging

logger = logging.getLogger(__name__)

@dataclass
class ImageMetadata:
    """Container for image metadata and release information"""
    image_tag: str
    image_type: str  # 'qli' or 'parser'
    version: str
    build_number: Optional[str] = None
    branch: Optional[str] = None
    commit_hash: Optional[str] = None
    build_date: Optional[datetime] = None
    jira_tickets: List[str] = None
    release_notes: List[str] = None
    compatibility_info: Dict[str, Any] = None
    performance_metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.jira_tickets is None:
            self.jira_tickets = []
        if self.release_notes is None:
            self.release_notes = []
        if self.compatibility_info is None:
            self.compatibility_info = {}
        if self.performance_metrics is None:
            self.performance_metrics = {}

class ImageReleaseExtractor:
    """
    Extract comprehensive release information from QLI and Parser image tags
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Image tag patterns for QLI and Parser images
        self.qli_patterns = [
            r'qli-(?P<version>[\d\.]+)-(?P<build>\d+)-(?P<hash>[a-f0-9]{7,})',
            r'alation-qli:(?P<version>[\d\.]+)-(?P<branch>[\w\-]+)-(?P<hash>[a-f0-9]{7,})',
            r'query-log-ingestion:(?P<version>[\d\.]+)\.(?P<build>\d+)'
        ]

        self.parser_patterns = [
            r'parser-(?P<version>[\d\.]+)-(?P<build>\d+)-(?P<hash>[a-f0-9]{7,})',
            r'alation-parser:(?P<version>[\d\.]+)-(?P<branch>[\w\-]+)-(?P<hash>[a-f0-9]{7,})',
            r'gsp-parser:(?P<version>[\d\.]+)\.(?P<build>\d+)'
        ]

        # Repository configurations
        self.repos = {
            'qli': {
                'git_url': 'git@github.com:Alation/alation-qli.git',
                'jira_project': 'QLI',
                'component': 'query-log-ingestion'
            },
            'parser': {
                'git_url': 'git@github.com:Alation/alation-parser.git',
                'jira_project': 'AL',
                'component': 'parser'
            }
        }

    def parse_image_tag(self, image_tag: str) -> ImageMetadata:
        """
        Parse an image tag and extract basic metadata
        """
        logger.info(f"Parsing image tag: {image_tag}")

        # Determine image type and extract metadata
        image_type = self._detect_image_type(image_tag)
        patterns = self.qli_patterns if image_type == 'qli' else self.parser_patterns

        metadata = ImageMetadata(
            image_tag=image_tag,
            image_type=image_type,
            version="unknown"
        )

        # Try to match against known patterns
        for pattern in patterns:
            match = re.search(pattern, image_tag)
            if match:
                metadata.version = match.group('version')
                metadata.build_number = match.groupdict().get('build')
                metadata.branch = match.groupdict().get('branch')
                metadata.commit_hash = match.groupdict().get('hash')
                break

        # Extract build date if present in tag
        date_match = re.search(r'(\d{4})(\d{2})(\d{2})', image_tag)
        if date_match:
            try:
                metadata.build_date = datetime(
                    int(date_match.group(1)),
                    int(date_match.group(2)),
                    int(date_match.group(3))
                )
            except ValueError:
                pass

        return metadata

    def _detect_image_type(self, image_tag: str) -> str:
        """Detect whether image is QLI or Parser based on tag"""
        qli_indicators = ['qli', 'query-log', 'ingestion']
        parser_indicators = ['parser', 'gsp', 'sql-parser']

        tag_lower = image_tag.lower()

        if any(indicator in tag_lower for indicator in qli_indicators):
            return 'qli'
        elif any(indicator in tag_lower for indicator in parser_indicators):
            return 'parser'
        else:
            # Default fallback based on common patterns
            return 'parser' if 'parse' in tag_lower else 'qli'

    async def enrich_metadata(self, metadata: ImageMetadata) -> ImageMetadata:
        """
        Enrich basic metadata with release notes, Jira tickets, and Git info
        """
        logger.info(f"Enriching metadata for {metadata.image_tag}")

        # Parallel enrichment tasks
        tasks = []

        if metadata.commit_hash:
            tasks.append(self._get_git_info(metadata))

        tasks.append(self._extract_jira_tickets(metadata))
        tasks.append(self._get_compatibility_info(metadata))

        # Execute enrichment tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Enrichment task failed: {result}")
            elif isinstance(result, dict):
                # Merge enrichment data
                for key, value in result.items():
                    if hasattr(metadata, key) and value:
                        setattr(metadata, key, value)

        return metadata

    async def _get_git_info(self, metadata: ImageMetadata) -> Dict[str, Any]:
        """Extract Git commit information"""
        try:
            repo_config = self.repos.get(metadata.image_type, {})
            if not metadata.commit_hash or not repo_config:
                return {}

            # Note: In production, this would use git API or local clone
            # For now, return structured placeholder
            return {
                'release_notes': [
                    f"Commit {metadata.commit_hash[:7]}: {metadata.image_type} improvements",
                    f"Version {metadata.version} release candidate",
                    "Bug fixes and performance improvements"
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get git info: {e}")
            return {}

    async def _extract_jira_tickets(self, metadata: ImageMetadata) -> Dict[str, Any]:
        """Extract Jira ticket references from commit messages and branches"""
        try:
            jira_tickets = []

            # Extract from branch name
            if metadata.branch:
                jira_matches = re.findall(r'([A-Z]{2,}-\d+)', metadata.branch.upper())
                jira_tickets.extend(jira_matches)

            # Extract from image tag
            tag_matches = re.findall(r'([A-Z]{2,}-\d+)', metadata.image_tag.upper())
            jira_tickets.extend(tag_matches)

            # Common QLI/Parser ticket patterns
            if metadata.image_type == 'qli':
                jira_tickets.extend(['QLI-1234', 'AL-123456'])  # Example tickets
            else:
                jira_tickets.extend(['AL-234567', 'PARSER-567'])  # Example tickets

            return {
                'jira_tickets': list(set(jira_tickets))  # Remove duplicates
            }
        except Exception as e:
            logger.error(f"Failed to extract Jira tickets: {e}")
            return {}

    async def _get_compatibility_info(self, metadata: ImageMetadata) -> Dict[str, Any]:
        """Get compatibility information for the image"""
        try:
            if metadata.image_type == 'qli':
                compatibility = {
                    'supported_databases': ['snowflake', 'databricks', 'bigquery', 'redshift'],
                    'min_alation_version': '26.4.0.0',
                    'connector_requirements': {
                        'snowflake': '>=2.1.0',
                        'databricks': '>=1.8.0'
                    }
                }
            else:  # parser
                compatibility = {
                    'supported_databases': ['postgresql', 'mysql', 'oracle', 'sqlserver', 'db2'],
                    'sql_standards': ['ANSI SQL', 'SQL-92', 'SQL:1999'],
                    'gsp_version': metadata.version
                }

            return {
                'compatibility_info': compatibility
            }
        except Exception as e:
            logger.error(f"Failed to get compatibility info: {e}")
            return {}

    def extract_performance_baseline(self, metadata: ImageMetadata) -> Dict[str, Any]:
        """Extract performance baseline information for regression testing"""

        if metadata.image_type == 'qli':
            return {
                'ingestion_rate_baseline': '10000 queries/minute',
                'memory_usage_baseline': '2GB peak',
                'latency_baseline': '500ms p95',
                'throughput_baseline': '50MB/s'
            }
        else:  # parser
            return {
                'parse_rate_baseline': '1000 statements/second',
                'memory_usage_baseline': '1GB peak',
                'accuracy_baseline': '99.9%',
                'supported_complexity': 'nested queries up to 5 levels'
            }

    def generate_test_matrix(self, metadata: ImageMetadata) -> Dict[str, Any]:
        """Generate test matrix based on image metadata"""

        base_tests = {
            'unit_tests': True,
            'integration_tests': True,
            'performance_tests': True
        }

        if metadata.image_type == 'qli':
            qli_tests = {
                'connector_tests': metadata.compatibility_info.get('supported_databases', []),
                'ingestion_volume_tests': ['small', 'medium', 'large'],
                'concurrent_ingestion_tests': True,
                'data_quality_tests': True
            }
            base_tests.update(qli_tests)
        else:  # parser
            parser_tests = {
                'sql_dialect_tests': metadata.compatibility_info.get('supported_databases', []),
                'complexity_tests': ['simple', 'complex', 'nested'],
                'accuracy_tests': True,
                'performance_regression_tests': True
            }
            base_tests.update(parser_tests)

        return base_tests

    def to_json(self, metadata: ImageMetadata) -> str:
        """Convert metadata to JSON format"""
        data = asdict(metadata)
        # Handle datetime serialization
        if data.get('build_date'):
            data['build_date'] = data['build_date'].isoformat()
        return json.dumps(data, indent=2)

    def to_deployment_summary(self, metadata: ImageMetadata) -> str:
        """Generate human-readable deployment summary"""

        summary = f"""
# {metadata.image_type.upper()} Image Deployment Summary

**Image Tag:** `{metadata.image_tag}`
**Version:** {metadata.version}
**Build:** {metadata.build_number or 'N/A'}
**Branch:** {metadata.branch or 'N/A'}
**Commit:** {metadata.commit_hash or 'N/A'}

## Release Notes
"""

        if metadata.release_notes:
            for note in metadata.release_notes:
                summary += f"- {note}\n"
        else:
            summary += "- No release notes available\n"

        summary += f"""
## Associated Jira Tickets
"""
        if metadata.jira_tickets:
            for ticket in metadata.jira_tickets:
                summary += f"- {ticket}\n"
        else:
            summary += "- No Jira tickets found\n"

        summary += f"""
## Compatibility Information
"""
        if metadata.compatibility_info:
            for key, value in metadata.compatibility_info.items():
                summary += f"- **{key.replace('_', ' ').title()}:** {value}\n"

        summary += f"""
## Recommended Test Suite
"""
        test_matrix = self.generate_test_matrix(metadata)
        for test_type, enabled in test_matrix.items():
            if isinstance(enabled, bool) and enabled:
                summary += f"- ✅ {test_type.replace('_', ' ').title()}\n"
            elif isinstance(enabled, list):
                summary += f"- ✅ {test_type.replace('_', ' ').title()}: {', '.join(enabled)}\n"

        return summary

# CLI interface for standalone usage
if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Extract release notes from image tags')
    parser.add_argument('image_tag', help='Docker image tag to analyze')
    parser.add_argument('--format', choices=['json', 'summary'], default='summary',
                       help='Output format (default: summary)')
    parser.add_argument('--enrich', action='store_true',
                       help='Enrich with Git and Jira information')

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    extractor = ImageReleaseExtractor()
    metadata = extractor.parse_image_tag(args.image_tag)

    if args.enrich:
        metadata = asyncio.run(extractor.enrich_metadata(metadata))

    if args.format == 'json':
        print(extractor.to_json(metadata))
    else:
        print(extractor.to_deployment_summary(metadata))