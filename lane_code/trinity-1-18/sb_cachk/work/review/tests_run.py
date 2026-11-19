from pathlib import Path
import sys
ROOT = Path('/scratch/jjyeung/orch_n30/sb_cachk/work/extract')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'kit_v2'))
import mc_common as C
C.code_pins()
C.pin(ROOT/'kit_v2/tests/test_kit.py')
C.pin(__file__)
import pytest
raise SystemExit(pytest.main(['-q', '-p', 'no:cacheprovider', '--basetemp', str(HERE/'tmp/pytest_review'), str(ROOT/'kit_v2/tests')]))
