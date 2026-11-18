import offline_guard
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
for d in ('launcher','reader','reader/evaluator','cohort','proof'):sys.path.insert(0,str(ROOT/d))
os.environ['PYTHONDONTWRITEBYTECODE']='1'

import pytest
@pytest.fixture(autouse=True)
def no_test_alarm(monkeypatch):
    import signal
    monkeypatch.setattr(signal,'alarm',lambda seconds:0)
