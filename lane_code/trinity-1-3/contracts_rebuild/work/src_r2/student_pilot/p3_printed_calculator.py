"""Alias the shared formatter so calculator receipts hash the implementation itself."""
import sys
from trace_format import calculator
sys.modules[__name__] = calculator
