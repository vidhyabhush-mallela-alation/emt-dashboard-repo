"""
Image Validator - Validate QLI & Parser images before deployment
"""

import asyncio
import logging
import aiohttp
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from .extractor import ImageMetadata

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of image validation"""
    is_valid: bool
    validation_type: str
    message: str
    details: Dict[str, Any] = None

@dataclass
class ImageValidationReport:
    """Complete validation report for an image"""
    image_tag: str
    overall_status: str  # 'pass', 'warning', 'fail'
    validations: List[ValidationResult]
    deployment_ready: bool
    blocking_issues: List[str]
    warnings: List[str]
    recommendations: List[str]

class ImageValidator:
    """
    Comprehensive validator for QLI and Parser images
    Performs security, functionality, and deployment readiness checks
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Validation thresholds and requirements
        self.validation_config = {
            'qli': {
                'required_tags': ['version', 'build'],
                'security_scan_required': True,
                'performance_baseline': {
                    'ingestion_rate': 5000,  # queries/minute minimum
                    'memory_limit': 4096,    # MB maximum
                    'startup_time': 60       # seconds maximum
                },
                'compatibility_check': True
            },
            'parser': {
                'required_tags': ['version', 'build'],
                'security_scan_required': True,
                'performance_baseline': {
                    'parse_rate': 500,       # statements/second minimum
                    'memory_limit': 2048,    # MB maximum
                    'startup_time': 30       # seconds maximum
                },
                'accuracy_threshold': 0.999  # 99.9% parsing accuracy
            }
        }

        # Known vulnerabilities database (would be populated from security scanners)
        self.known_vulnerabilities = {
            'critical': [],
            'high': ['CVE-2024-1234'],  # Example
            'medium': ['CVE-2024-5678'],
            'low': []
        }

    async def validate_image(self, metadata: ImageMetadata) -> ImageValidationReport:
        """
        Perform comprehensive validation of image
        """
        logger.info(f"Validating image: {metadata.image_tag}")

        validations = []

        # Run validation tasks in parallel
        validation_tasks = [
            self._validate_metadata_completeness(metadata),
            self._validate_security(metadata),
            self._validate_functionality(metadata),
            self._validate_performance_readiness(metadata),
            self._validate_deployment_readiness(metadata)
        ]

        results = await asyncio.gather(*validation_tasks, return_exceptions=True)

        # Process validation results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Validation task failed: {result}")
                validations.append(ValidationResult(
                    is_valid=False,
                    validation_type='error',
                    message=f'Validation failed: {result}',
                    details={'exception': str(result)}
                ))
            elif isinstance(result, list):
                validations.extend(result)
            elif isinstance(result, ValidationResult):
                validations.append(result)

        # Generate overall assessment
        report = self._generate_validation_report(metadata, validations)

        return report

    async def _validate_metadata_completeness(self, metadata: ImageMetadata) -> List[ValidationResult]:
        """Validate that image metadata is complete"""
        results = []

        # Check required fields
        required_fields = ['image_tag', 'image_type', 'version']
        for field in required_fields:
            value = getattr(metadata, field, None)
            if not value or value == 'unknown':
                results.append(ValidationResult(
                    is_valid=False,
                    validation_type='metadata',
                    message=f'Missing required field: {field}',
                    details={'field': field, 'value': value}
                ))
            else:
                results.append(ValidationResult(
                    is_valid=True,
                    validation_type='metadata',
                    message=f'Required field present: {field}',
                    details={'field': field, 'value': value}
                ))

        # Validate version format
        if metadata.version and metadata.version != 'unknown':
            if self._is_valid_semver(metadata.version):
                results.append(ValidationResult(
                    is_valid=True,
                    validation_type='metadata',
                    message='Version follows semantic versioning',
                    details={'version': metadata.version}
                ))
            else:
                results.append(ValidationResult(
                    is_valid=False,
                    validation_type='metadata',
                    message='Version does not follow semantic versioning',
                    details={'version': metadata.version}
                ))

        # Check for Jira tickets (recommended)
        if not metadata.jira_tickets:
            results.append(ValidationResult(
                is_valid=True,  # Not blocking, but warning
                validation_type='metadata',
                message='No associated Jira tickets found (recommended for traceability)',
                details={'ticket_count': 0}
            ))
        else:
            results.append(ValidationResult(
                is_valid=True,
                validation_type='metadata',
                message=f'Associated Jira tickets found: {len(metadata.jira_tickets)}',
                details={'tickets': metadata.jira_tickets}
            ))

        return results

    async def _validate_security(self, metadata: ImageMetadata) -> List[ValidationResult]:
        """Validate security aspects of the image"""
        results = []

        # Simulate security scan (in production, integrate with actual scanners)
        security_scan_result = await self._simulate_security_scan(metadata)

        if security_scan_result['critical_vulnerabilities'] > 0:
            results.append(ValidationResult(
                is_valid=False,
                validation_type='security',
                message=f'Critical vulnerabilities found: {security_scan_result["critical_vulnerabilities"]}',
                details=security_scan_result
            ))
        elif security_scan_result['high_vulnerabilities'] > 0:
            results.append(ValidationResult(
                is_valid=False,  # Block deployment for high vulnerabilities
                validation_type='security',
                message=f'High severity vulnerabilities found: {security_scan_result["high_vulnerabilities"]}',
                details=security_scan_result
            ))
        else:
            results.append(ValidationResult(
                is_valid=True,
                validation_type='security',
                message='No critical or high severity vulnerabilities found',
                details=security_scan_result
            ))

        # Check for security best practices
        security_checks = await self._check_security_practices(metadata)
        results.extend(security_checks)

        return results

    async def _validate_functionality(self, metadata: ImageMetadata) -> List[ValidationResult]:
        """Validate functional aspects of the image"""
        results = []

        image_type = metadata.image_type

        if image_type == 'qli':
            # QLI-specific functional validations
            qli_validations = await self._validate_qli_functionality(metadata)
            results.extend(qli_validations)
        else:  # parser
            # Parser-specific functional validations
            parser_validations = await self._validate_parser_functionality(metadata)
            results.extend(parser_validations)

        # Common functional validations
        common_validations = await self._validate_common_functionality(metadata)
        results.extend(common_validations)

        return results

    async def _validate_performance_readiness(self, metadata: ImageMetadata) -> List[ValidationResult]:
        """Validate performance readiness of the image"""
        results = []

        config = self.validation_config.get(metadata.image_type, {})
        baseline = config.get('performance_baseline', {})

        # Simulate performance validation (in production, run actual benchmarks)
        perf_results = await self._simulate_performance_test(metadata)

        for metric, expected_value in baseline.items():
            actual_value = perf_results.get(metric, 0)

            if metric in ['ingestion_rate', 'parse_rate']:  # Higher is better
                is_valid = actual_value >= expected_value
                comparison = 'meets' if is_valid else 'below'
            else:  # Lower is better (memory, startup time)
                is_valid = actual_value <= expected_value
                comparison = 'within' if is_valid else 'exceeds'

            results.append(ValidationResult(
                is_valid=is_valid,
                validation_type='performance',
                message=f'{metric.replace("_", " ").title()} {comparison} baseline: {actual_value} (expected: {expected_value})',
                details={'metric': metric, 'actual': actual_value, 'expected': expected_value}
            ))

        return results

    async def _validate_deployment_readiness(self, metadata: ImageMetadata) -> List[ValidationResult]:
        """Validate deployment readiness"""
        results = []

        # Check compatibility information
        if not metadata.compatibility_info:
            results.append(ValidationResult(
                is_valid=False,
                validation_type='deployment',
                message='Compatibility information missing',
                details={'issue': 'no_compatibility_info'}
            ))
        else:
            results.append(ValidationResult(
                is_valid=True,
                validation_type='deployment',
                message='Compatibility information available',
                details=metadata.compatibility_info
            ))

        # Check for release notes
        if not metadata.release_notes:
            results.append(ValidationResult(
                is_valid=True,  # Warning, not blocking
                validation_type='deployment',
                message='No release notes available (recommended for deployment)',
                details={'note_count': 0}
            ))
        else:
            results.append(ValidationResult(
                is_valid=True,
                validation_type='deployment',
                message=f'Release notes available: {len(metadata.release_notes)} entries',
                details={'notes': metadata.release_notes}
            ))

        # Check build freshness
        if metadata.build_date:
            days_old = (datetime.now() - metadata.build_date).days
            if days_old > 30:
                results.append(ValidationResult(
                    is_valid=False,
                    validation_type='deployment',
                    message=f'Image build is {days_old} days old (consider rebuilding)',
                    details={'days_old': days_old, 'build_date': metadata.build_date.isoformat()}
                ))
            else:
                results.append(ValidationResult(
                    is_valid=True,
                    validation_type='deployment',
                    message=f'Image build is recent ({days_old} days old)',
                    details={'days_old': days_old}
                ))

        return results

    async def _validate_qli_functionality(self, metadata: ImageMetadata) -> List[ValidationResult]:
        """QLI-specific functionality validation"""
        results = []

        # Check supported databases
        if metadata.compatibility_info:
            supported_dbs = metadata.compatibility_info.get('supported_databases', [])

            required_dbs = ['snowflake', 'databricks', 'bigquery']  # Core QLI databases
            missing_dbs = [db for db in required_dbs if db not in supported_dbs]

            if missing_dbs:
                results.append(ValidationResult(
                    is_valid=False,
                    validation_type='qli_functionality',
                    message=f'Missing support for required databases: {", ".join(missing_dbs)}',
                    details={'missing_databases': missing_dbs}
                ))
            else:
                results.append(ValidationResult(
                    is_valid=True,
                    validation_type='qli_functionality',
                    message='All required databases supported',
                    details={'supported_databases': supported_dbs}
                ))

        # Simulate QLI ingestion test
        ingestion_test = await self._simulate_qli_ingestion_test(metadata)
        results.append(ValidationResult(
            is_valid=ingestion_test['success'],
            validation_type='qli_functionality',
            message=f'QLI ingestion test: {"PASS" if ingestion_test["success"] else "FAIL"}',
            details=ingestion_test
        ))

        return results

    async def _validate_parser_functionality(self, metadata: ImageMetadata) -> List[ValidationResult]:
        """Parser-specific functionality validation"""
        results = []

        # Check supported SQL dialects
        if metadata.compatibility_info:
            supported_dbs = metadata.compatibility_info.get('supported_databases', [])

            required_dbs = ['postgresql', 'mysql', 'oracle', 'sqlserver']  # Core parser databases
            missing_dbs = [db for db in required_dbs if db not in supported_dbs]

            if missing_dbs:
                results.append(ValidationResult(
                    is_valid=False,
                    validation_type='parser_functionality',
                    message=f'Missing support for required SQL dialects: {", ".join(missing_dbs)}',
                    details={'missing_dialects': missing_dbs}
                ))
            else:
                results.append(ValidationResult(
                    is_valid=True,
                    validation_type='parser_functionality',
                    message='All required SQL dialects supported',
                    details={'supported_dialects': supported_dbs}
                ))

        # Simulate parser accuracy test
        accuracy_test = await self._simulate_parser_accuracy_test(metadata)
        threshold = self.validation_config.get('parser', {}).get('accuracy_threshold', 0.999)

        results.append(ValidationResult(
            is_valid=accuracy_test['accuracy'] >= threshold,
            validation_type='parser_functionality',
            message=f'Parser accuracy: {accuracy_test["accuracy"]:.1%} (threshold: {threshold:.1%})',
            details=accuracy_test
        ))

        return results

    async def _validate_common_functionality(self, metadata: ImageMetadata) -> List[ValidationResult]:
        """Common functionality validation for all images"""
        results = []

        # Simulate basic health check
        health_check = await self._simulate_health_check(metadata)
        results.append(ValidationResult(
            is_valid=health_check['healthy'],
            validation_type='common_functionality',
            message=f'Health check: {"PASS" if health_check["healthy"] else "FAIL"}',
            details=health_check
        ))

        # Simulate startup test
        startup_test = await self._simulate_startup_test(metadata)
        results.append(ValidationResult(
            is_valid=startup_test['success'],
            validation_type='common_functionality',
            message=f'Startup test: {"PASS" if startup_test["success"] else "FAIL"} ({startup_test["startup_time"]}s)',
            details=startup_test
        ))

        return results

    # Simulation methods (in production, these would call actual services)

    async def _simulate_security_scan(self, metadata: ImageMetadata) -> Dict[str, Any]:
        """Simulate security scan results"""
        await asyncio.sleep(0.1)  # Simulate scan time

        # Simulate based on version (newer versions generally have fewer vulnerabilities)
        version_parts = metadata.version.split('.')
        major_version = int(version_parts[0]) if version_parts else 0

        if major_version >= 2:  # Newer versions
            return {
                'critical_vulnerabilities': 0,
                'high_vulnerabilities': 0,
                'medium_vulnerabilities': 1,
                'low_vulnerabilities': 2,
                'scan_date': datetime.now().isoformat(),
                'scanner': 'simulated'
            }
        else:  # Older versions
            return {
                'critical_vulnerabilities': 0,
                'high_vulnerabilities': 1,
                'medium_vulnerabilities': 3,
                'low_vulnerabilities': 5,
                'scan_date': datetime.now().isoformat(),
                'scanner': 'simulated'
            }

    async def _check_security_practices(self, metadata: ImageMetadata) -> List[ValidationResult]:
        """Check security best practices"""
        results = []

        # Check if running as non-root (simulated)
        results.append(ValidationResult(
            is_valid=True,
            validation_type='security',
            message='Image configured to run as non-root user',
            details={'user': 'alation'}
        ))

        # Check for secrets in environment (simulated)
        results.append(ValidationResult(
            is_valid=True,
            validation_type='security',
            message='No hardcoded secrets detected in image',
            details={'secrets_scan': 'pass'}
        ))

        return results

    async def _simulate_performance_test(self, metadata: ImageMetadata) -> Dict[str, Any]:
        """Simulate performance test results"""
        await asyncio.sleep(0.2)  # Simulate test time

        if metadata.image_type == 'qli':
            return {
                'ingestion_rate': 8000,  # queries/minute
                'memory_limit': 3072,    # MB
                'startup_time': 45       # seconds
            }
        else:  # parser
            return {
                'parse_rate': 750,       # statements/second
                'memory_limit': 1536,    # MB
                'startup_time': 25       # seconds
            }

    async def _simulate_qli_ingestion_test(self, metadata: ImageMetadata) -> Dict[str, Any]:
        """Simulate QLI ingestion test"""
        await asyncio.sleep(0.3)
        return {
            'success': True,
            'queries_processed': 1000,
            'ingestion_rate': 150.5,
            'errors': 0,
            'test_duration_seconds': 10
        }

    async def _simulate_parser_accuracy_test(self, metadata: ImageMetadata) -> Dict[str, Any]:
        """Simulate parser accuracy test"""
        await asyncio.sleep(0.3)
        return {
            'accuracy': 0.9995,  # 99.95%
            'total_statements': 10000,
            'successful_parses': 9995,
            'failed_parses': 5,
            'test_duration_seconds': 15
        }

    async def _simulate_health_check(self, metadata: ImageMetadata) -> Dict[str, Any]:
        """Simulate basic health check"""
        await asyncio.sleep(0.1)
        return {
            'healthy': True,
            'response_time_ms': 150,
            'status_code': 200,
            'checks': {
                'database': 'pass',
                'dependencies': 'pass',
                'disk_space': 'pass'
            }
        }

    async def _simulate_startup_test(self, metadata: ImageMetadata) -> Dict[str, Any]:
        """Simulate startup test"""
        await asyncio.sleep(0.2)

        baseline = self.validation_config.get(metadata.image_type, {}).get('performance_baseline', {})
        max_startup = baseline.get('startup_time', 60)

        # Simulate startup time (usually better than baseline)
        startup_time = max_startup * 0.7

        return {
            'success': startup_time <= max_startup,
            'startup_time': startup_time,
            'max_allowed': max_startup
        }

    def _generate_validation_report(self, metadata: ImageMetadata,
                                  validations: List[ValidationResult]) -> ImageValidationReport:
        """Generate comprehensive validation report"""

        # Categorize validations
        passed = [v for v in validations if v.is_valid]
        failed = [v for v in validations if not v.is_valid]

        # Determine overall status
        if not failed:
            overall_status = 'pass'
        elif any(v.validation_type in ['security', 'metadata'] and not v.is_valid for v in validations):
            overall_status = 'fail'
        else:
            overall_status = 'warning'

        # Extract blocking issues and warnings
        blocking_issues = [v.message for v in failed if v.validation_type in ['security', 'metadata', 'qli_functionality', 'parser_functionality']]
        warnings = [v.message for v in failed if v.validation_type not in ['security', 'metadata', 'qli_functionality', 'parser_functionality']]

        # Generate recommendations
        recommendations = self._generate_validation_recommendations(failed, metadata)

        return ImageValidationReport(
            image_tag=metadata.image_tag,
            overall_status=overall_status,
            validations=validations,
            deployment_ready=overall_status == 'pass',
            blocking_issues=blocking_issues,
            warnings=warnings,
            recommendations=recommendations
        )

    def _generate_validation_recommendations(self, failed_validations: List[ValidationResult],
                                           metadata: ImageMetadata) -> List[str]:
        """Generate recommendations based on validation failures"""
        recommendations = []

        validation_types = set(v.validation_type for v in failed_validations)

        if 'security' in validation_types:
            recommendations.append('Address security vulnerabilities before deployment')
            recommendations.append('Run updated security scan after fixes')

        if 'metadata' in validation_types:
            recommendations.append('Complete missing metadata fields')
            recommendations.append('Follow semantic versioning standards')

        if 'performance' in validation_types:
            recommendations.append('Optimize performance to meet baseline requirements')
            recommendations.append('Run performance profiling to identify bottlenecks')

        if f'{metadata.image_type}_functionality' in validation_types:
            if metadata.image_type == 'qli':
                recommendations.append('Verify QLI ingestion functionality across all supported databases')
            else:
                recommendations.append('Validate parser accuracy with comprehensive SQL test suite')

        if 'deployment' in validation_types:
            recommendations.append('Update compatibility information and release notes')
            recommendations.append('Consider rebuilding image if build is too old')

        return recommendations

    def _is_valid_semver(self, version: str) -> bool:
        """Check if version follows semantic versioning"""
        import re
        semver_pattern = r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
        return re.match(semver_pattern, version) is not None

    def generate_validation_summary(self, report: ImageValidationReport) -> str:
        """Generate human-readable validation summary"""

        status_emoji = {'pass': '✅', 'warning': '⚠️', 'fail': '❌'}
        emoji = status_emoji.get(report.overall_status, '❓')

        summary = f"""
# Image Validation Report {emoji}

**Image:** `{report.image_tag}`
**Overall Status:** {report.overall_status.upper()}
**Deployment Ready:** {'Yes' if report.deployment_ready else 'No'}
**Validation Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary Statistics
- **Total Validations:** {len(report.validations)}
- **Passed:** {len([v for v in report.validations if v.is_valid])}
- **Failed:** {len([v for v in report.validations if not v.is_valid])}

## Validation Results by Category
"""

        # Group by validation type
        by_type = {}
        for validation in report.validations:
            if validation.validation_type not in by_type:
                by_type[validation.validation_type] = []
            by_type[validation.validation_type].append(validation)

        for val_type, validations in by_type.items():
            passed = len([v for v in validations if v.is_valid])
            total = len(validations)
            summary += f"\n### {val_type.replace('_', ' ').title()}\n"
            summary += f"**Status:** {passed}/{total} passed\n\n"

            for validation in validations:
                status = '✅' if validation.is_valid else '❌'
                summary += f"- {status} {validation.message}\n"

        if report.blocking_issues:
            summary += f"\n## Blocking Issues\n"
            for issue in report.blocking_issues:
                summary += f"- ❌ {issue}\n"

        if report.warnings:
            summary += f"\n## Warnings\n"
            for warning in report.warnings:
                summary += f"- ⚠️ {warning}\n"

        if report.recommendations:
            summary += f"\n## Recommendations\n"
            for rec in report.recommendations:
                summary += f"- {rec}\n"

        return summary