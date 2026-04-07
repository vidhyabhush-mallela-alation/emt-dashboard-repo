"""
Release Notes from Image Tags - QLI & Parser Image Analysis

This module provides automated extraction of release notes and metadata from
Alation QLI and Parser Docker image tags. Integrates with Git, Jira, and
deployment systems to provide comprehensive release intelligence.
"""

from .extractor import ImageReleaseExtractor
from .analyzer import ReleaseAnalyzer
from .validator import ImageValidator

__version__ = "1.0.0"
__all__ = ["ImageReleaseExtractor", "ReleaseAnalyzer", "ImageValidator"]