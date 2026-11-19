"""Check 2: the new runtime test fails when its reader sequence lacks the M4 fix.

Each mutant copies work/new, edits only reader_steps in tests/test_scale_donor.py, and runs the runtime test.
Also checks that reader_steps equals the READER_REQUEST.md block minus its import and torch.load lines.
"""
import json, re, shutil, subprocess, sys
from pathlib import Path

W = Path(__file__).resolve().parent
TEST = 'tests/test_scale_donor.py'
NAME = 'tests.test_scale_donor.ScaleDonorTests.test_mdg_runtime_strict_load_requires_reader_metadata_steps'
src = (W / 'new' / TEST).read_text()
m = re.search(r"reader_steps = '''\n(.*?)'''", src, re.S)
steps = m.group(1)
doc = Path('/scratch/jjyeung/orch_n30/fb_pack/donor3/out/READER_REQUEST.md').read_text()
block = re.search(r'## Separate runtime[^\n]*\n.*?```python\n(.*?)```', doc, re.S).group(1)
doc_steps = '\n'.join(l for l in block.split('\n') if not l.startswith(('from student_pilot import', 'heads = torch.load'))).lstrip('\n')
LOAD = ('visual = model.auxiliary_heads.depth.model.visual\nprefix = "depth.model.visual."\n'
        'visual.load_state_dict({key[len(prefix):]: value for key, value in heads.items()\n'
        '                        if key.startswith(prefix)}, strict=True)\n')
FREEZE = 'visual.requires_grad_(False)\n'
assert LOAD in steps and FREEZE in steps
MUTANTS = {
    'old_order': steps.replace(LOAD, '').replace(FREEZE, ''),
    'no_freeze': steps.replace(FREEZE, ''),
    'no_visual_load': steps.replace(LOAD, 'visual = model.auxiliary_heads.depth.model.visual\n'),
}
res = dict(reader_steps_equals_doc_block=steps.strip() == doc_steps.strip(), mutants={})
py = '/scratch/jjyeung/envs/p1cpu/bin/python'
for name, mutated in MUTANTS.items():
    assert mutated != steps, name
    tree = W / f'mut_{name}'
    if tree.exists():
        shutil.rmtree(tree)
    shutil.copytree(W / 'new', tree, ignore=shutil.ignore_patterns('__pycache__'))
    (tree / TEST).write_text(src.replace(steps, mutated, 1))
    r = subprocess.run(['nice', '-n', '10', py, '-B', str(W / 'run_unit.py'), tree.name, NAME],
                       capture_output=True, text=True, cwd=W)
    log = r.stdout + r.stderr
    (W / f'mut_{name}.log').write_text(log)
    errs = re.findall(r'^(?:\w+Error|AssertionError): .*$', log, re.M)
    res['mutants'][name] = dict(rc=r.returncode, test_failed=r.returncode != 0, first_errors=errs[:3])
res['status'] = 'PASS' if res['reader_steps_equals_doc_block'] and all(v['test_failed'] for v in res['mutants'].values()) else 'FAIL'
(W / 'TEST_MUTANTS.json').write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
