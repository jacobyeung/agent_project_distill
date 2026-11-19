"""Reviewer source mutations on real copied trees; obligations() runs in a fresh interpreter per mutant."""
import json, shutil, subprocess, sys
from pathlib import Path
W = Path(__file__).resolve().parents[1]
ORIG, AFTER = W/'work/tree_src_orig', W/'work/tree_src_patched'
import time
MUT = W/'work'/('mut_%d' % time.time()); MUT.mkdir(parents=True)
I, M = 'student_pilot/r2_intake.py', 'student_pilot/r2_materialize.py'
NA, NB = "os.environ.get(env_key('STUDENT_R2_FRAME_HOST'))", "os.environ.get('STUDENT_R2_FRAME_HOST')"

def block(s, start, n):
    lines = s.splitlines(True)
    i = next(i for i, l in enumerate(lines) if start in l)
    return ''.join(lines[:i+n] + lines[i:i+n] + lines[i+n:])

def comment(s):
    head = 'def intake(manifest_path, *, limit=2000, select_types=None):\n'
    assert s.count(head) == 1
    return s.replace(head, head + "    # remote_full = (limit is None and " + NA + " == '1'\n")

def edits(look):
    return {
        'I_drop':    [(I, look+" == '1'", 'True')],
        'I_dup':     [(I, lambda s: block(s, 'remote_full = (limit is None', 3))],
        'I_weak':    [(I, look+" == '1'", look+" != '0'")],
        'I_limit':   [(I, 'remote_full = (limit is None and ', 'remote_full = (True and ')],
        'I_comment': [(I, comment)],
        'I_local':   [(I, "and os.environ.get('STUDENT_R2_LOCAL_NODE') != '1'", 'and True')],
        'I_host':    [(I, "and not os.uname().nodename.startswith('trinity'))", 'and True)')],
        'M_drop':    [(M, 'if '+look+" != '1':", 'if False:')],
        'M_dup':     [(M, lambda s: block(s, 'if '+look, 2))],
        'M_weak':    [(M, 'if '+look+" != '1':", 'if '+look+" != '1' and False:")],
        'M_local':   [(M, "if full and (os.environ.get('STUDENT_R2_LOCAL_NODE') == '1' or", 'if full and (False or')],
    }

CASES = [('after', 'clean', AFTER, []), ('before', 'clean', ORIG, [])]
CASES += [('after', k, AFTER, v) for k, v in edits(NA).items()]
CASES += [('before', k, ORIG, v) for k, v in edits(NB).items() if k not in ('I_comment',)]
CASES += [('after', 'I_native', AFTER, [(I, NA, NB)]), ('after', 'M_native', AFTER, [(M, NA, NB)]),
          ('after', 'X_orig_readers', AFTER, [(I, None, ORIG/I), (M, None, ORIG/M)]),
          ('after', 'X_orig_intake', AFTER, [(I, None, ORIG/I)]),
          ('before', 'X_after_readers', ORIG, [(I, None, AFTER/I), (M, None, AFTER/M)])]

PROBE = r'''
import json,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve();sys.path.insert(0,str(root))
from launch_r2.runtime import obligations
from student_pilot import r2_intake,r2_materialize
assert Path(r2_intake.__file__).resolve().is_relative_to(root) and Path(r2_materialize.__file__).resolve().is_relative_to(root)
try:
    r=obligations();print(json.dumps(dict(refused=False,records=[(Path(x['source']['path']).name,x['line'],x['category']) for x in r])))
except ValueError as e:print(json.dumps(dict(refused=True,error=str(e))))
'''
results = []
for tree, name, src, changes in CASES:
    dst = MUT/(tree+'_'+name)
    shutil.copytree(src, dst)
    for change in changes:
        rel = change[0]; p = dst/rel; s = p.read_text()
        if len(change) == 2: new = change[1](s)
        elif change[1] is None: new = Path(change[2]).read_text()
        else:
            assert s.count(change[1]) == 1, (tree, name, change[1], s.count(change[1])); new = s.replace(change[1], change[2])
        assert new != s, (tree, name); p.write_text(new)
    out = subprocess.run([sys.executable, '-B', '-c', PROBE, str(dst)], capture_output=True, text=True)
    row = json.loads(out.stdout.strip().splitlines()[-1]) if out.returncode == 0 else dict(crash=out.stderr[-800:])
    results.append(dict(tree=tree, mutation=name, **row)); print(tree, name, row, flush=True)
(W/'out/MUTATIONS.json').write_text(json.dumps(results, indent=1)+'\n')
