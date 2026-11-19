"""Produce independent unified diffs; never invoke Git or alter the input tree."""
import difflib
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
original, edited = root / 'in/tree/work/tree_r1', root / 'work/tree'
out = root / 'out/patches'
timing = '''    local stage_wait_start
    if [[ "${TK_LAUNCH_TIMING:-0}" == 1 ]]; then
        stage_wait_start=$(date +%s)
        tk_step "stage $mode lock wait start"
    fi
    flock 8
    if [[ "${TK_LAUNCH_TIMING:-0}" == 1 ]]; then
        tk_step "stage $mode lock acquired wait_seconds=$(( $(date +%s) - stage_wait_start ))"
    fi
'''
current_c = (edited / 'launch_s1/b/c.sh').read_text()
base_c = (original / 'launch_s1/b/c.sh').read_text()
assert current_c.count(timing) == 1
assert base_c.count('    flock 8\n') == 1
cache_c = current_c.replace(timing, '    flock 8\n')
timing_c = base_c.replace('    flock 8\n', timing)
groups = {
    '01_prepared_input_cache.diff': ['launch_s1/b/c.sh', 'launch_s1/b/r.sh', 'launch_s1/b/pc.py',
                                    'tests/test_prepared_input_cache.py', 'tests/test_prepared_cache_wrapper.py'],
    '02_parallel_frame_sha.diff': ['launch_s1/b/f2.py', 'tests/test_parallel_frame_sha.py'],
    '03_checkpoint_verify_memo.diff': ['launch_s1/b/r8.py', 'tests/test_checkpoint_verify_memo.py'],
    '04_launch_phase_timing.diff': ['launch_s1/job.sh', 'launch_s1/b/c.sh', 'tests/test_launch_phase_timing.py'],
}
manifest = {}
for name, paths in groups.items():
    parts = []
    for relative in paths:
        prior = original / relative
        before = prior.read_text() if prior.exists() else ''
        after = (edited / relative).read_text()
        if relative == 'launch_s1/b/c.sh':
            after = cache_c if name.startswith('01') else timing_c
        parts.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                     fromfile='a/' + relative if prior.exists() else '/dev/null', tofile='b/' + relative))
    payload = ''.join(parts).encode()
    (out / name).write_bytes(payload)
    manifest[name] = dict(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest(), files=paths,
        apply_method='patch --batch --fuzz=0 -p1',
        input_root='in/tree/work/tree_r1', depends_on=[],
        base_sha256={relative: hashlib.sha256((original / relative).read_bytes()).hexdigest()
                     if (original / relative).is_file() else None for relative in paths})
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
expected = {p for paths in groups.values() for p in paths}
different = {str(p.relative_to(edited)) for p in edited.rglob('*') if p.is_file()
             and (not (original / p.relative_to(edited)).is_file()
                  or p.read_bytes() != (original / p.relative_to(edited)).read_bytes())}
assert different == expected, (different - expected, expected - different)
print(json.dumps(manifest, indent=2))
print('PASS: only the 11 declared production/test paths differ from the input tree')
