"""
Welcome to ``python-Wappalyzer`` API documentation!

:see: `Wappalyzer` and `WebPage`.
"""

from .Wappalyzer import Wappalyzer, analyze, analyze_payload
from .webpage import WebPage
__all__ = ["Wappalyzer", 
           "WebPage", 
           "analyze",
           "analyze_payload"]
