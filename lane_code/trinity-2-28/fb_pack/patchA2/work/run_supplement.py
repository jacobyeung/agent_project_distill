"""Final MUST regressions and unmodified real-envelope tests, run serially."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PY='/scratch/jjyeung/envs/p1cpu/bin/python'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
plan=[(t,'must_final_'+t,['test_r1_patch_a2','patch_a2_checks']) for t in ('base','patch_a','new','live')]
# Keep the original camera stand-in expectations as historical diagnostics;
# exercise all other real-route declaration tests without altering their guards.
real=['real_route_tests.RealRoute.'+n for n in (
    'test_four_real_envelopes_reach_genuine_host_veto',
    'test_four_plus_recovery_reach_genuine_host_veto',
    'test_each_selected_real_envelope_preserves_host_veto',
    'test_declared_missing_envelope_names_recovery',
    'test_undeclared_envelope_names_recovery',
    'test_bound_source_and_manifest_refusals_remain',
    'test_deferred_build23_declaration_unchanged')]
plan += [(t,'real_declared_'+t,real) for t in ('base','new','live')]
records=[]
inputs={str(p):sha(p) for p in (Path(__file__),ROOT/'work/run_tests.py',ROOT/'work/support/patch_a2_checks.py',ROOT/'work/support/real_route_tests.py')}
for tree,label,names in plan:
    command=['env','PYTHONDONTWRITEBYTECODE=1','OMP_NUM_THREADS=16','MKL_NUM_THREADS=16','OPENBLAS_NUM_THREADS=16','nice','-n','10',PY,'-B','work/run_tests.py',tree,label,*names]
    with (ROOT/'out'/(label+'.log')).open('x') as log:
        p=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    report=ROOT/'out'/(label+'.json')
    row=dict(tree=tree,label=label,command=' '.join(command),returncode=p.returncode)
    if report.exists():
        r=json.loads(report.read_text());row.update({k:r[k] for k in ('tests','failures','errors','skipped')});inputs[str(report)]=sha(report)
    records.append(row)
    print(json.dumps(row),flush=True)
    (ROOT/'out/SUPPLEMENT.json').write_text(json.dumps(dict(command='env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 nice -n 10 '+PY+' -B work/run_supplement.py',inputs_sha256=inputs,runs=records),indent=2)+'\n')
    if p.returncode<0:sys.exit('STOP: subprocess killed; no rerun')
