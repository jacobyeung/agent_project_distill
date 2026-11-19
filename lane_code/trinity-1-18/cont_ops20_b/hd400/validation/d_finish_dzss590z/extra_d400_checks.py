"""Apply the unchanged release and CPU-guard assertions to the D400 fixtures too.

The original suites retain their defaults. Only fixture selection and result
destinations change here; all assertions and guard subprocesses remain intact.
"""
import os
import sys
from pathlib import Path

WORK = Path(__file__).resolve().parent
ROOT = WORK.parent.parent
sys.path.insert(0, str(ROOT / 'dbuild'))
os.environ['D_TEST_TMPDIR'] = str(WORK)


def adapted(name, changes):
    path = ROOT / 'dbuild' / name
    code = path.read_text()
    for before, after in changes:
        assert code.count(before) == 1, before
        code = code.replace(before, after)
    exec(compile(code, str(path), 'exec'), dict(__name__='__main__', __file__=str(path)))


adapted('check_release_d.py', [
    ('for step in (200,544):', 'for step in (200,400,544):'),
    ("W/'RELEASE_RESULTS.json'", "W/'RELEASE_ALL_STEPS.json'")])
adapted('test_followup_d.py', [
    ("RAM / 'actual544/BUILD.json'", "RAM / 'actual400/BUILD.json'"),
    ("STEP='544'", "STEP='400'"),
    ("receipt_writer='actual544/delivery/a/5.py CPU.json expression'",
     "receipt_writer='actual400/delivery/a/5.py CPU.json expression'"),
    ("HERE / 'evidence/FOLLOWUP_RESULTS.json'", "RAM / 'FOLLOWUP400_RESULTS.json'")])
