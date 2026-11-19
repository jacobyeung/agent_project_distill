import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from round4_common import L, SOURCE, PYTHONS, run, status

mode = sys.argv[1]
root = L / 'work/round4_before' if mode == 'before' else SOURCE
for tag, py in PYTHONS:
    run('regressions_' + mode + '_' + tag,
        [py, '-I', '-s', '-B', '-m', 'unittest', 'discover', '-s', 'tests',
         '-p', 'test_review_round4.py', '-v'], root, dict(LCS_REVIEW2_FIXES='1', LCS_PYTHON=py),
        expected=1 if mode == 'before' else 0)
status('Round-4 ' + mode + ' regression evidence recorded on both interpreters; no Git attempted.')
