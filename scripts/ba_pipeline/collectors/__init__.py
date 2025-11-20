# [NEXUS IDENTITY] ID: -175669379644154931 | DATE: 2025-11-19

"""
Collector registry for BA data pipeline.
"""

from .conference import ConferenceCollector
from .internal_usage import InternalUsageCollector
from .job_market import JobMarketCollector
from .regulation import RegulationCollector

__all__ = [
    "ConferenceCollector",
    "InternalUsageCollector",
    "JobMarketCollector",
    "RegulationCollector",
]

