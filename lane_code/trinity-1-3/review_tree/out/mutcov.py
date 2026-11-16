import subprocess, json, os, sys
from pathlib import Path
T = Path('/scratch/jjyeung/orch_n30/review_tree/work/lane3/work/tree_r1')
TESTS = ['tests.test_r2_data_path','tests.test_r2_families','tests.test_r2_refusals','tests.test_r2_policy','tests.test_r2_preparation',
         'tests.test_r2_sampling','tests.test_r2_final_guards','tests.test_r2_dense_decode','tests.test_r2_launch_dispatch']
M = [
 ('r2_grammar.py: answer restatement refusal (legacy_direct)', 'student_pilot/r2_grammar.py', "raise ValueError('Answer restatement is not reasoning')", "pass"),
 ('r2_grammar.py: shared-grammar errors raise (validate_direct)', 'student_pilot/r2_grammar.py', "        raise ValueError('Shared grammar: '+','.join(e.rule_id for e in errors))\n    if re.search(r'\\d\\s*(?:seconds", "        pass\n    if re.search(r'\\d\\s*(?:seconds"),
 ('r2_grammar.py: deployed response refusal (validate_program)', 'student_pilot/r2_grammar.py', "raise ValueError('Deployed selector cannot render training responses')", "pass"),
 ('r2_contract.py: route planning VQA-only', 'student_pilot/r2_contract.py', "raise ValueError('D0 route-planning rows enter VQA only')", "pass"),
 ('r2_contract.py: old-format direct row (trace_contract)', 'student_pilot/r2_contract.py', "raise ValueError('Old-format direct row')", "pass"),
 ('r2_contract.py: failed response needs Locate continuation', 'student_pilot/r2_contract.py', "raise ValueError('Failed response needs a located direct continuation')", "pass"),
 ('r2_contract.py: no call after failed response', 'student_pilot/r2_contract.py', "raise ValueError('R2 fallback calls again after a failed response')", "pass"),
 ('r2_intake.py: duplicate QID within family', 'student_pilot/r2_intake.py', "raise ValueError('Duplicate QID within family')", "pass"),
 ('r2_intake.py: withheld room reason', 'student_pilot/r2_intake.py', "reasons.append('withheld_room')", "pass"),
 ('r2_intake.py: scene_coverage None refuses', 'student_pilot/r2_intake.py', "raise ValueError('scene_coverage=None refuses; unknown overlap is not a pass')", "return [], {}"),
 ('r2_withheld.py: provenance canonical/alias names', 'student_pilot/r2_withheld.py', "        names += [v for v in (row.get('canonical'), row.get('provenance', {}).get('canonical'),\n                              row.get('provenance', {}).get('alias')) if v]", "        pass"),
 ('r2_exclusions.py: wrong scene vs coverage', 'student_pilot/r2_exclusions.py', "raise ValueError('Wrong scene: independent coverage differs')", "pass"),
 ('r2_mix.py: repeat limit 4', 'student_pilot/r2_mix.py', "if repeats[kind] > 4:", "if repeats[kind] > 40:"),
 ('r2_policy.py: bank outside claim scope', 'student_pilot/r2_policy.py', "raise ValueError('Actual bank is outside lineage claim scope')", "pass"),
 ('r2_policy.py: deployed selector on ReVSI/VSTI', 'student_pilot/r2_policy.py', "raise ValueError('Deployed selector is fitted on this bank')", "pass"),
 ('r2_openers.py: keep requires witness', 'student_pilot/r2_openers.py', "raise ValueError('Missing routing vocabulary witness for keep warm start')", "return 'kept'"),
 ('launch_r2/host.py: distinct pose sources', 'launch_r2/host.py', "raise ValueError('Missing distinct pose source')", "pass"),
 ('r2_materialize.py: full store refused on local node', 'student_pilot/r2_materialize.py', "raise ValueError('Full store forbidden on a local node; use slices of at most 2000 rows per family')", "pass"),
]
def run():
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', TMPDIR='/scratch/jjyeung/orch_n30/review_tree/work/tmp_t')
    p = subprocess.run(['/scratch/jjyeung/envs/p1cpu/bin/python','-B','-m','unittest',*TESTS], cwd=T, env=env, capture_output=True, text=True, timeout=1800)
    tail = [l for l in p.stderr.splitlines() if l.startswith(('Ran','OK','FAILED'))]
    return p.returncode, ' '.join(tail[-2:])
base = run(); print('baseline', base); res = [dict(mutation='baseline', rc=base[0], result=base[1])]
for name, f, old, new in M:
    path = T/f; orig = path.read_text()
    if orig.count(old) != 1:
        res.append(dict(mutation=name, result='NOT APPLIED (pattern count %d)' % orig.count(old))); print(name, 'NOT APPLIED', orig.count(old)); continue
    path.write_text(orig.replace(old, new))
    try:
        rc, tail = run()
    finally:
        path.write_text(orig)
    killed = rc != 0
    res.append(dict(mutation=name, killed=killed, result=tail)); print(('KILLED  ' if killed else 'SURVIVED'), name, '|', tail)
json.dump(res, open('/scratch/jjyeung/orch_n30/review_tree/work/h/MUTCOV.json','w'), indent=1)
