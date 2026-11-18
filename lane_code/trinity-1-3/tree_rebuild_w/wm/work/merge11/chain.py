from pathlib import Path
import json,os,subprocess,sys,time
L=Path(__file__).resolve().parents[2];B=L/'work/merge11';stage=sys.argv[1]
records=[]
def size():
    total=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file())
    assert total<=200_000_000,total
    return total
def run(name,script,*args,allow=False):
    out=B/'proofs'/name;out.mkdir(parents=True,exist_ok=True)
    row=dict(name=name,status='running',tmp_before=size());records.append(row)
    (B/(stage+'_RUNS.json')).write_text(json.dumps(records,indent=2)+'\n')
    (B/'STATUS.md').write_text('# Build 11 status\n\nGO=false. Steps 1 and 2 complete. Current phase: '+stage+' / '+name+'. Evidence: '+stage+'_RUNS.json.\n')
    print('Starting '+name,flush=True)
    with (out/'console.log').open('w') as log:
        code=subprocess.run([sys.executable,'-I','-s','-B',str(L/script),*args],cwd=L,stdout=log,stderr=subprocess.STDOUT).returncode
    row.update(returncode=code,tmp_after=size(),status='complete' if code==0 else 'failed')
    (B/(stage+'_RUNS.json')).write_text(json.dumps(records,indent=2)+'\n')
    print(name,code,flush=True)
    if code<0:raise SystemExit('Process killed; no retry authorized: '+name)
    if code and not allow:raise SystemExit(code)
if stage=='merge':
    for name,mod in [('g1','test_build10'),('g2','test_build10_heading'),('g3','test_build10_availability'),('g4','test_build10_config'),('g5','test_build10_budgets'),('g6','test_build10_manifest'),('g7','test_build10_refusals')]:
        run(name,'work/n1fix2/test_runner.py',str(B/'proofs'/name),'tests.'+mod)
    run('parity','work/build10/parity10.py')
    run('numeric','work/build10/proof_parity_numeric10.py')
    run('parity_build7','work/build10/parity_build7_10.py')
    run('n1/mutations','work/n1fix2/mutations.py')
    run('g8','work/build10/proof_runner10.py','g8',*['eat1.tests.test_eat1.'+n for n in ('Adversarial','FixedMathContract','Instruments','StaticScanner','ToyEndToEnd')])
    run('eat1','work/build10/final_eat10.py')
elif stage=='n1':
    for name in ('text','forward','checkpoint','target_prepared','review_variants','row_delta','host_checks','faults','contract_closure','registry_closure','gate_edges9','r1_edges9','prepared9','mix_checks9','mix_edges9','mix_accounting9','extent_conflict9','kit_scope'):
        run('n1/'+name,'work/n1fix2/proof_'+name+'.py',allow=True)
elif stage=='review':
    run('review_tests','work/n1fix2/test_runner.py',str(B/'proofs/review_tests'),'tests.test_merge11','tests.test_batched_routed_decode','tests.test_r2_n1fix','tests.test_r2_n1fix2','tests.test_r2_build_n1')
    run('l1','work/build10/proof_runner10.py','l1','eat1.tests.test_eat1.FixedMathContract')
elif stage=='qualify':
    run('depth_sweep','work/merge11/sweep.py')
    run('seal','work/n1fix2/seal.py')
    run('n1/kits','work/n1fix2/stage9.py')
    run('n1_chain','work/merge11/chain.py','n1')
    run('preservation','work/merge11/preservation.py')
    run('coverage','work/merge11/coverage.py')
    run('packet','work/n1fix2/packet_final.py','integrated','packet','contract')
    run('delivery','work/n1fix2/make_delivery.py')
    delivery=json.loads((L/'work/n1fix2/DELIVERY.json').read_text())
    run('package','work/n1fix2/package.py',str(L/delivery['path']))
    run('legacy_guards','work/n1fix2/legacy_guard_proof.py')
    run('comparison','work/n1fix2/compare.py')
    run('final_coverage','work/merge11/coverage.py')
