"""Route the existing suite's proof output into the authorized kit directory."""
from pathlib import Path


def pytest_collection_modifyitems(items):
    for item in items:
        if item.module.__name__.endswith('test_tiny_e2e'):
            item.module.OUT = Path(__file__).resolve().parent / 'test_results'
