"""Try to defeat the bars-first guard with planted files (run inside bwrap with work/gcopy bound at sb_ph2fix)."""
import json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path('/scratch/jjyeung/orch_n30/sb_ph2fix')
KIT = ROOT/'sb_mask_phrase'
CPU = '/scratch/jjyeung/envs/p1cpu/bin/python'
GPU = str(ROOT/'payload/environment/bin/python')
FAKE = '/scratch/jjyeung/orch_n30/sb_ph2rev/work/fakebin'
BARS = KIT/'part2/BARS_PART2.json'
ENV = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', PATH=FAKE+':'+os.environ['PATH'])
ENTRY = {
    'gate_aggregate': [CPU, '-B', 'part2/gate.py', 'aggregate'],
    'gate_capture': [CPU, '-B', 'part2/gate.py', 'capture'],
    'gate_pass': [CPU, '-B', 'part2/gate.py', 'pass'],
    'run.sh price aggregate': ['bash', 'run.sh', 'part2/price.py', 'aggregate'],
    'price.py aggregate (no run.sh)': [CPU, '-B', 'part2/price.py', 'aggregate'],
    'launch_part2.sh capture': ['bash', 'part2/launch_part2.sh', 'capture', 'arkitscenes/41048124'],
    'sam3_pass.py pass': [GPU, '-B', 'part2/sam3_pass.py', 'pass'],
    'launch_gpu.sh': ['bash', 'part2/launch_gpu.sh', '--node-local', '0'],
}


def snapshot():
    out = {}
    for base in (KIT/'out', KIT/'work'):
        for p in base.rglob('*'):
            if 'launcher_tests' in p.parts or 'gate_tests' in p.parts:
                continue
            try:
                st = p.lstat()
                out[str(p)] = (st.st_size, st.st_mtime_ns)
            except FileNotFoundError:
                pass
    return out


def run(name, extra=None, timeout=240):
    before = snapshot()
    env = dict(ENV, PART2_GO='1') if 'sam3' in name else dict(ENV)
    env.update(extra or {})
    r = subprocess.run(ENTRY[name], cwd=KIT, env=env, capture_output=True, text=True, timeout=timeout)
    after = snapshot()
    changed = sorted(set(after) ^ set(before) | {k for k in after if k in before and after[k] != before[k]})
    msg = (r.stderr.strip().splitlines() or [''])[-1][:160]
    return dict(rc=r.returncode, refused='REFUSED' in (r.stderr+r.stdout), msg=msg, writes=changed[:5])


def plant(kind):
    p2 = KIT/'out/part2'
    undo = []
    if kind == 'missing_bars':
        BARS.rename(BARS.with_name('BARS_PART2.moved')); undo.append(lambda: BARS.with_name('BARS_PART2.moved').rename(BARS))
    elif kind == 'altered_bars':
        orig = BARS.read_bytes(); BARS.chmod(0o644); BARS.write_bytes(orig.replace(b'-1.0', b'-2.0', 1))
        undo.append(lambda: (BARS.write_bytes(orig), BARS.chmod(0o444)))
    elif kind == 'bars_symlink_same_bytes':
        orig = BARS.read_bytes(); alt = KIT/'work/bars_copy.json'; alt.write_bytes(orig)
        BARS.chmod(0o644); BARS.rename(BARS.with_name('BARS_PART2.moved')); BARS.symlink_to(alt)
        undo.append(lambda: (BARS.unlink(), BARS.with_name('BARS_PART2.moved').rename(BARS), BARS.chmod(0o444), alt.unlink()))
    else:
        files = {'per_item': p2/'PER_ITEM_PART2.jsonl', 'deep_json': p2/'a/b/c/x.json', 'hidden_json': p2/'.hidden.json',
                 'upper_JSON': p2/'scores.JSON', 'csv_scores': p2/'per_item_part2.csv', 'decision': p2/'DECISION_PART2.json',
                 'gz_capture': KIT/'work/part2_caps/arkitscenes__41048124.json.gz', 'killed': KIT/'out/pool_part2/KILLED.json',
                 'stop': KIT/'out/pool_part2/STOP.json', 'tmp_suffix': p2/'PER_ITEM_PART2.jsonl.tmp'}
        if kind in files:
            f = files[kind]; f.parent.mkdir(parents=True, exist_ok=True); f.write_text('{}')
            undo.append(lambda: f.unlink())
        elif kind == 'dangling_symlink':
            f = p2/'PER_ITEM_PART2.jsonl'; f.parent.mkdir(parents=True, exist_ok=True); f.symlink_to('/scratch/jjyeung/orch_n30/sb_ph2rev/work/nonexistent_target.jsonl')
            undo.append(lambda: f.unlink())
        elif kind == 'dir_symlink':
            d = KIT/'work/elsewhere'; d.mkdir(exist_ok=True); (d/'PER_ITEM_PART2.jsonl').write_text('{}')
            f = p2/'linked'; f.symlink_to(d)
            undo.append(lambda: (f.unlink(), (d/'PER_ITEM_PART2.jsonl').unlink(), d.rmdir()))
    return undo


def main():
    results = {}
    scenarios = ['clean', 'missing_bars', 'altered_bars', 'bars_symlink_same_bytes', 'per_item', 'deep_json', 'hidden_json',
                 'upper_JSON', 'csv_scores', 'decision', 'tmp_suffix', 'dangling_symlink', 'dir_symlink', 'gz_capture', 'killed', 'stop']
    heavy = {'clean', 'missing_bars', 'altered_bars', 'per_item', 'dangling_symlink', 'dir_symlink', 'killed'}
    for s in scenarios:
        undo = [] if s == 'clean' else plant(s)
        try:
            names = list(ENTRY) if s in heavy else ['gate_aggregate', 'gate_capture', 'gate_pass']
            results[s] = {}
            for n in [x for x in names if x != 'launch_gpu.sh']:
                results[s][n] = run(n)
            # The launcher waits 300 s after admission; run it only where the gate already refuses (never time it out).
            if 'launch_gpu.sh' in names and results[s]['gate_pass']['rc'] != 0:
                results[s]['launch_gpu.sh'] = run('launch_gpu.sh')
        finally:
            for u in undo:
                u()
        print(s, {n: (r['rc'], r['refused'], len(r['writes'])) for n, r in results[s].items()}, flush=True)
    for d, extra in (('fixture_escape_dotdot', {'PART2_FIXTURE_DIR': '../out/part2'}),
                     ('fixture_escape_abs', {'PART2_FIXTURE_DIR': str(KIT/'out/part2')})):
        before = snapshot()
        r = subprocess.run([CPU, '-B', 'part2/gate.py', 'fixture'], cwd=KIT, env=dict(ENV, **extra), capture_output=True, text=True)
        results[d] = dict(rc=r.returncode, msg=(r.stderr.strip().splitlines() or [''])[-1][:160], writes=len(set(snapshot()) ^ set(before)))
    Path('/scratch/jjyeung/orch_n30/sb_ph2rev/work/GUARD_ATTACK.json').write_text(json.dumps(results, indent=1))


if __name__ == '__main__':
    main()
