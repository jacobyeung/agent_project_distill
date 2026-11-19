"""Replay sb_ph2rev's planted-file attacks plus new ones on work/gcopy (run inside sbx.sh gcopy)."""
import json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path('/scratch/jjyeung/orch_n30/sb_ph2fix')
KIT = ROOT/'sb_mask_phrase'
OUTF = Path('/scratch/jjyeung/orch_n30/sb_ph2chk/work/GUARD_ATTACK.json')
CPU = '/scratch/jjyeung/envs/p1cpu/bin/python'
GPU = str(ROOT/'payload/environment/bin/python')
BARS = KIT/'part2/BARS_PART2.json'
ENV = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1')
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
P2 = KIT/'out/part2'
POOL = KIT/'out/pool_part2'
CAPS = KIT/'work/part2_caps'


def snapshot():
    out = {}
    for base, dirs, names in os.walk(ROOT):
        b = Path(base)
        if b == ROOT:
            dirs[:] = [d for d in dirs if d != 'payload']
        dirs[:] = [d for d in dirs if d not in ('launcher_tests', 'gate_tests')]
        for n in names + dirs:
            p = b/n
            st = p.lstat()
            out[str(p)] = (st.st_size, st.st_mtime_ns, os.readlink(p) if p.is_symlink() else '')
    return out


def run(name, extra=None):
    before = snapshot()
    env = dict(ENV, PART2_GO='1') if 'sam3' in name else dict(ENV)
    env.update(extra or {})
    r = subprocess.run(ENTRY[name], cwd=KIT, env=env, capture_output=True, text=True)
    after = snapshot()
    changed = sorted(set(after) ^ set(before) | {k for k in after if k in before and after[k] != before[k]})
    msg = (r.stderr.strip().splitlines() or [''])[-1][:200]
    return dict(rc=r.returncode, refused='REFUSED' in (r.stderr+r.stdout), msg=msg, writes=changed[:8], n_writes=len(changed))


def touch(p, text='{}'):
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)


def plant(kind):
    """Returns the undo list. Every planted object lives in the copy; undo restores the clean tree."""
    undo = []
    made = []  # top-level directories created here, removed in undo after their contents

    def mk(d):
        if not d.exists():
            d.mkdir(parents=True); made.append(d)
    if kind == 'missing_bars':
        BARS.rename(BARS.with_name('BARS_PART2.moved')); undo.append(lambda: BARS.with_name('BARS_PART2.moved').rename(BARS))
    elif kind == 'altered_bars':
        orig = BARS.read_bytes(); BARS.chmod(0o644); BARS.write_bytes(orig.replace(b'-1.0', b'-2.0', 1))
        undo.append(lambda: (BARS.write_bytes(orig), BARS.chmod(0o444)))
    elif kind == 'bars_symlink_same_bytes':
        alt = KIT/'work/bars_copy.json'; alt.write_bytes(BARS.read_bytes())
        BARS.rename(BARS.with_name('BARS_PART2.moved')); BARS.symlink_to(alt)
        undo.append(lambda: (BARS.unlink(), BARS.with_name('BARS_PART2.moved').rename(BARS), alt.unlink()))
    elif kind == 'part2_code_dir_ancestor_symlink':
        # out/ itself becomes a symlink to a real directory with the same contents.
        real = KIT/'work/out_real'; (KIT/'out').rename(real); (KIT/'out').symlink_to(real, target_is_directory=True)
        undo.append(lambda: ((KIT/'out').unlink(), real.rename(KIT/'out')))
    else:
        files = {'per_item': P2/'PER_ITEM_PART2.jsonl', 'deep_json': P2/'a/b/c/x.json', 'hidden_json': P2/'.hidden.json',
                 'upper_JSON': P2/'scores.JSON', 'csv_scores': P2/'per_item_part2.csv', 'decision': P2/'DECISION_PART2.json',
                 'gz_capture': CAPS/'arkitscenes__41048124.json.gz', 'killed': POOL/'KILLED.json',
                 'stop': POOL/'STOP.json', 'tmp_suffix': P2/'PER_ITEM_PART2.jsonl.tmp',
                 'mixed_jsonl': P2/'score.JsOnL', 'tsv_scores': P2/'score.TSV',
                 # new
                 'json_bak': P2/'DECISION_PART2.json.bak', 'upper_gz_caps': CAPS/'X.JSON.GZ', 'stop_plain': POOL/'STOP',
                 'killed_plain': POOL/'KILLED', 'running_marker': POOL/'RUNNING', 'pool_partial': POOL/'0123456789abcdef/candidates.json'}
        if kind in files:
            f = files[kind]
            for d in (P2, POOL, CAPS):
                if d in f.parents: mk(d)
            touch(f)
            undo.append(lambda: f.unlink())
            if kind == 'deep_json':
                undo.append(lambda: [(P2/x).rmdir() for x in ('a/b/c', 'a/b', 'a')])
            if kind == 'pool_partial':
                undo.append(lambda: (POOL/'0123456789abcdef').rmdir())
        elif kind == 'dangling_symlink':
            mk(P2); f = P2/'PER_ITEM_PART2.jsonl'; f.symlink_to(KIT/'work/nonexistent_target.jsonl'); undo.append(lambda: f.unlink())
        elif kind in ('dir_symlink', 'dangling_dir_symlink'):
            mk(P2); d = KIT/'work/elsewhere'
            if kind == 'dir_symlink':
                d.mkdir(); (d/'PER_ITEM_PART2.jsonl').write_text('{}')
            f = P2/'linked'; f.symlink_to(d, target_is_directory=True)
            undo.append(lambda: (f.unlink(), (d/'PER_ITEM_PART2.jsonl').unlink() if d.exists() else None, d.rmdir() if d.exists() else None))
        elif kind == 'file_symlink':
            mk(P2); t = KIT/'work/file.json'; t.write_text('{}'); f = P2/'linked'; f.symlink_to(t)
            undo.append(lambda: (f.unlink(), t.unlink()))
        elif kind == 'output_dir_symlink':
            real = KIT/'work/p2_real'; real.mkdir(); P2.rename(KIT/'work/p2_saved'); P2.symlink_to(real, target_is_directory=True)
            undo.append(lambda: (P2.unlink(), real.rmdir(), (KIT/'work/p2_saved').rename(P2)))
        elif kind == 'pool_symlink':
            real = KIT/'work/pool_real'; real.mkdir(); POOL.symlink_to(real, target_is_directory=True)
            undo.append(lambda: (POOL.unlink(), real.rmdir()))
        elif kind == 'caps_symlink':
            saved = KIT/'work/part2_caps_saved'
            had = CAPS.exists()
            if had:
                CAPS.rename(saved)
            real = KIT/'work/caps_real'; real.mkdir(); CAPS.symlink_to(real, target_is_directory=True)
            undo.append(lambda: (CAPS.unlink(), real.rmdir(), saved.rename(CAPS) if had else None))
        elif kind == 'hardlink_score':
            mk(P2); t = KIT/'work/A0_ROWS.json'; f = P2/'score.json'; os.link(t, f); undo.append(lambda: f.unlink())
        elif kind == 'dir_named_decision':
            mk(P2); f = P2/'DECISION_PART2.json'; f.mkdir(); undo.append(lambda: f.rmdir())
        elif kind == 'dir_named_per_item':
            mk(P2); f = P2/'PER_ITEM_PART2.jsonl'; f.mkdir(); undo.append(lambda: f.rmdir())
        elif kind == 'fifo_decision':
            mk(P2); f = P2/'DECISION_PART2.json'; os.mkfifo(f); undo.append(lambda: f.unlink())
        elif kind == 'dir_named_caps_gz':
            mk(CAPS); f = CAPS/'arkitscenes__41048124.json.gz'; f.mkdir(); undo.append(lambda: f.rmdir())
        else:
            raise ValueError(kind)
    undo.extend(lambda d=d: d.rmdir() for d in reversed(made))
    return undo


def reach(kind):
    """Gate-passing non-regular plants against an aggregate that has all 209 synthetic captures."""
    fx = KIT/('work/reach_'+kind)
    fx.mkdir()
    shutil.copytree(KIT/'work/part2_fixture/caps', fx/'caps', symlinks=True)
    agg = fx/'aggregate'; agg.mkdir()
    if kind == 'dir_decision':
        (agg/'DECISION_PART2.json').mkdir()
    elif kind == 'fifo_decision':
        os.mkfifo(agg/'DECISION_PART2.json')
    before = {str(p) for p in agg.rglob('*')}
    r = subprocess.run(['bash', 'run.sh', 'part2/price.py', 'fixture-aggregate'], cwd=KIT,
                       env=dict(ENV, PART2_FIXTURE_DIR=str(fx.relative_to(KIT))), capture_output=True, text=True)
    after = {str(p) for p in agg.rglob('*')}
    return dict(rc=r.returncode, refused='REFUSED' in (r.stderr+r.stdout), msg=(r.stderr.strip().splitlines() or [''])[-1][:200],
                new_files=sorted(after - before), note='reach dirs are kept as evidence under gcopy/sb_mask_phrase/work')


def main():
    results = {}
    old = ['clean', 'missing_bars', 'altered_bars', 'bars_symlink_same_bytes', 'per_item', 'deep_json', 'hidden_json',
           'upper_JSON', 'csv_scores', 'decision', 'tmp_suffix', 'dangling_symlink', 'dir_symlink', 'gz_capture', 'killed', 'stop']
    builder = ['dangling_dir_symlink', 'file_symlink', 'output_dir_symlink', 'mixed_jsonl', 'tsv_scores']
    new = ['json_bak', 'upper_gz_caps', 'stop_plain', 'killed_plain', 'pool_symlink', 'caps_symlink', 'hardlink_score',
           'part2_code_dir_ancestor_symlink', 'running_marker', 'pool_partial',
           'dir_named_decision', 'dir_named_per_item', 'fifo_decision', 'dir_named_caps_gz']
    heavy = {'clean', 'missing_bars', 'altered_bars', 'per_item', 'dangling_symlink', 'dir_symlink', 'killed',
             'output_dir_symlink', 'part2_code_dir_ancestor_symlink', 'pool_symlink', 'caps_symlink', 'stop_plain',
             'dir_named_decision', 'dir_named_per_item', 'fifo_decision', 'dir_named_caps_gz', 'running_marker', 'pool_partial'}
    base = None
    for s in old + builder + new:
        undo = [] if s == 'clean' else plant(s)
        try:
            names = list(ENTRY) if s in heavy else ['gate_aggregate', 'gate_capture', 'gate_pass']
            results[s] = {}
            for n in [x for x in names if x != 'launch_gpu.sh']:
                results[s][n] = run(n)
            # The launcher waits 300 s after admission; run it only where the gate or admit_state refuses first.
            if 'launch_gpu.sh' in names and (results[s]['gate_pass']['rc'] != 0 or s in ('running_marker', 'pool_partial')):
                results[s]['launch_gpu.sh'] = run('launch_gpu.sh')
        finally:
            for u in undo:
                u()
        print(s, {n: (r['rc'], r['refused'], r['n_writes']) for n, r in results[s].items()}, flush=True)
        if s == 'clean':
            base = snapshot()
    for d, extra in (('fixture_escape_dotdot', {'PART2_FIXTURE_DIR': '../out/part2'}),
                     ('fixture_escape_abs', {'PART2_FIXTURE_DIR': str(KIT/'out/part2')})):
        before = snapshot()
        r = subprocess.run([CPU, '-B', 'part2/gate.py', 'fixture'], cwd=KIT, env=dict(ENV, **extra), capture_output=True, text=True)
        results[d] = dict(rc=r.returncode, msg=(r.stderr.strip().splitlines() or [''])[-1][:200], n_writes=len(set(snapshot()) ^ set(before)))
        print(d, results[d], flush=True)
    def files_only(s):
        return {k: v for k, v in s.items() if not Path(k).is_dir() or Path(k).is_symlink()}
    now = files_only(snapshot())
    then = files_only(base)
    results['_tree_restored_after_attacks'] = dict(same=now == then, added=sorted(set(now) - set(then))[:10],
                                                   removed=sorted(set(then) - set(now))[:10],
                                                   changed=sorted(k for k in now.keys() & then.keys() if now[k] != then[k])[:10])
    for k in ('dir_decision', 'fifo_decision'):
        results['reach_'+k] = reach(k)
        print('reach_'+k, results['reach_'+k], flush=True)
    OUTF.write_text(json.dumps(results, indent=1))


if __name__ == '__main__':
    main()
