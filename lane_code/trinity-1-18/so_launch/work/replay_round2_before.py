"""Apply the current regressions to a retained copy of the reviewed production files."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BEFORE = ROOT / 'work/review_round2_before'
LOGS = ROOT / 'out/tests/review_round2'
tree = Path(tempfile.mkdtemp(prefix='round2-red-', dir=ROOT / 'work'))
for source_root in (BEFORE / 'tree/launch_s1', ROOT / 'work/tree/tests'):
    # Only six production files and five delivered test modules are copied.
    paths = list(source_root.rglob('*')) if source_root.name == 'launch_s1' else [
        source_root / name for name in ('test_prepared_input_cache.py', 'test_prepared_cache_wrapper.py')]
    for path in paths:
        if path.is_file():
            target = tree / source_root.name / path.relative_to(source_root)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
python = [sys.executable, '-I', '-s', '-B']
cases = [
    ('cache.before.txt', python + [str(tree / 'tests/test_prepared_input_cache.py'),
        'PreparedCacheTests.test_reports_and_receipts_store_only_component_digests',
        'PreparedCacheTests.test_unpinned_optional_input_cli_refuses_without_method_or_traceback', '-v'], {}),
    ('lock.before.txt', python + [str(tree / 'tests/test_prepared_cache_wrapper.py'),
        'PreparedWrapperTests.test_duplicate_training_or_resume_job_times_out_with_75', '-v'], {}),
    ('delivery.before.txt', python + [str(ROOT / 'work/test_review_round2_delivery.py'), '-v'],
        {'REVIEW_TREE':str(BEFORE / 'tree'), 'REVIEW_OUT':str(BEFORE / 'out')}),
]
for name, command, overrides in cases:
    result = subprocess.run(command, env={**os.environ, **overrides}, capture_output=True, text=True, timeout=30)
    text = '$ ' + ' '.join(command) + '\nENV: ' + repr(overrides) + '\n'
    text += result.stdout + result.stderr + f'EXIT: {result.returncode}\n'
    (LOGS / name).write_text(text)
    assert result.returncode == 1 and 'FAILED (failures=' in text, text
    print(name + ': expected regression failure reproduced')
