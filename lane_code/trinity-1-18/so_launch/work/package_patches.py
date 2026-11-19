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
current_r = (edited / 'launch_s1/b/r.sh').read_text()
base_r = (original / 'launch_s1/b/r.sh').read_text()
guard = '/usr/bin/python3 -I "$HX/b/g.py" "$HX" "${1:?}"\n'
start = current_r.index('tk_run_timing() {\n')
end = current_r.index('export TK_RUNS_DIR=', start)
run_timing = current_r[start:end]
assert run_timing.count(guard) == 1 and base_r.count(guard) == 1
cache_r = current_r.replace(run_timing, guard)
timing_r = base_r.replace(guard, run_timing)
groups = {
    '01_prepared_input_cache.diff': ['launch_s1/b/c.sh', 'launch_s1/b/r.sh', 'launch_s1/b/pc.py',
                                    'tests/test_prepared_input_cache.py', 'tests/test_prepared_cache_wrapper.py'],
    '02_parallel_frame_sha.diff': ['launch_s1/b/f2.py', 'tests/test_parallel_frame_sha.py'],
    '03_checkpoint_verify_memo.diff': ['launch_s1/b/r8.py', 'tests/test_checkpoint_verify_memo.py'],
    '04_launch_phase_timing.diff': ['launch_s1/job.sh', 'launch_s1/b/c.sh', 'launch_s1/b/r.sh', 'tests/test_launch_phase_timing.py'],
}
manifest = {}
base_tree = {str(p.relative_to(original)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(original.rglob('*')) if p.is_file()}
base_tree_sha256 = hashlib.sha256(json.dumps(base_tree, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
for name, paths in groups.items():
    parts = []
    result_sha256 = {}
    for relative in paths:
        prior = original / relative
        before = prior.read_text() if prior.exists() else ''
        after = (edited / relative).read_text()
        if relative == 'launch_s1/b/c.sh':
            after = cache_c if name.startswith('01') else timing_c
        if relative == 'launch_s1/b/r.sh':
            after = cache_r if name.startswith('01') else timing_r
        result_sha256[relative] = hashlib.sha256(after.encode()).hexdigest()
        parts.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                     fromfile='a/' + relative if prior.exists() else '/dev/null', tofile='b/' + relative))
    payload = ''.join(parts).encode()
    (out / name).write_bytes(payload)
    manifest[name] = dict(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest(), files=paths,
        apply_method='patch --batch --fuzz=0 --no-backup-if-mismatch -p1',
        input_root='in/tree/work/tree_r1', depends_on=[],
        base_tree_sha256=base_tree_sha256, base_tree_files=len(base_tree),
        base_tree_hash_format='sha256(JSON {relative_file_path: file_sha256}, sorted keys, compact separators)',
        result_sha256=result_sha256,
        deployment='OFF: no useful production hit' if name.startswith('01') else 'default OFF; enable in order 03, 04, 02',
        native_gate_sha256=hashlib.sha256((root / 'work/run_native_regression.py').read_bytes()).hexdigest(),
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
