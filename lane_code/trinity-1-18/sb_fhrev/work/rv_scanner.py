"""Reviewer scanner check: opaque Q_E7 literals pass, native-name literals refuse (Python and shell sinks)."""
import ast, json, sys
from pathlib import Path
W = Path(__file__).resolve().parents[1]
T = Path(sys.argv[1]).resolve(); label = sys.argv[2]
S = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21')
sys.path[:0] = [str(T), str(W/'work/support')]
from launch_r2.build import bad_string
from student_pilot.p3_provenance import load
from naming21 import scan_python_environment
from environment21f import scan_shell
hashes = load(S/'work/build21/kits/q/b/wh.json')
def check(value, where, exception=None):
    if bad_string(value, hashes): raise ValueError('INPUT_NAME:'+where+':'+value)
N = 'STUDENT_R2_FRAME_HOST'
PY = {
    'py_subscript_opaque': ("import os\nos.environ['Q_E7']='1'\n", True),
    'py_update_opaque': ("import os\nos.environ.update(Q_E7='1')\n", True),
    'py_setdefault_opaque': ("import os\nos.environ.setdefault('Q_E7','1')\n", True),
    'py_env_kw_opaque': ("import subprocess\nsubprocess.run(['x'],env={'Q_E7':'1'})\n", True),
    'py_subscript_native': ("import os\nos.environ[%r]='1'\n" % N, False),
    'py_update_native': ("import os\nos.environ.update(%s='1')\n" % N, False),
    'py_concat_native': ("import os\nk='STU'+'DENT_R2_FRAME_HOST'\nos.environ[k]='1'\n", False),
    'py_fstring_native': ("import os\na='STU'\nos.environ[f'{a}DENT_R2_FRAME_HOST']='1'\n", False),
}
SH = {
    'sh_export_opaque': ('export Q_E7=1\n', True),
    'sh_prefix_opaque': ('Q_E7=1 python3 -I b/a.py q x y\n', True),
    'sh_export_native': ('export %s=1\n' % N, False),
    'sh_prefix_native': ('%s=1 python3 -I b/a.py q x y\n' % N, False),
}
rows = []
for name, (source, expect) in PY.items():
    try: scan_python_environment(ast.parse(source), check, 'b/h.py'); ok, err = True, None
    except ValueError as e: ok, err = False, str(e)
    rows.append(dict(case=name, accepted=ok, expected=expect, error=err))
for name, (source, expect) in SH.items():
    try:
        scan_shell(source, check, 'b/j.sh')
        for line in source.splitlines(): check(line, 'b/j.sh:line')
        ok, err = True, None
    except ValueError as e: ok, err = False, str(e)
    rows.append(dict(case=name, accepted=ok, expected=expect, error=err))
bad = [r for r in rows if r['accepted'] != r['expected']]
(W/'out'/('scanner_'+label+'.json')).write_text(json.dumps(dict(tree=str(T), rows=rows, mismatches=bad), indent=1)+'\n')
for r in rows: print(r)
print('MISMATCHES', len(bad))
