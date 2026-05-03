"""
Welcome to ``python-Wappalyzer`` API documentation!

:see: `Wappalyzer` and `WebPage`.
"""

from .Wappalyzer import Wappalyzer, analyze, analyze_async, analyze_batch, analyze_batch_async, analyze_payload
from .storage import ensure_database_schema, store_analysis_results, store_analysis_results_to_sqlite
from .webpage import WebPage
__all__ = ["Wappalyzer", 
           "WebPage", 
            "analyze",
            "analyze_async",
            "analyze_batch",
            "analyze_batch_async",
            "analyze_payload",
            "ensure_database_schema",
            "store_analysis_results",
            "store_analysis_results_to_sqlite"]
