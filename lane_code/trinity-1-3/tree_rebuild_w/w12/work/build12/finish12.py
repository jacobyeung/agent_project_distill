"""Serialize the final qualification and retain all input-bound group receipts."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
L=Path(__file__).resolve().parents[2];B=L/'work/build12';runs=[]
def run(name,script,*args):
    out=B/'proofs'/name;out.mkdir(parents=True,exist_ok=True)
    before=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file())
    assert before<=200_000_000
    (B/'STATUS.md').write_text('# Build 12 status\n\nGO=false. Final qualification: '+name+'. Evidence: FINAL_RUNS.json. FRAME64_ALL_READERS_UNQUALIFIED remains.\n')
    row=dict(name=name,tmp_before=before,start=time.time());runs.append(row)
    print('Starting '+name,flush=True)
    with (out/'console.log').open('w') as stream:
        result=subprocess.run([sys.executable,'-I','-s','-B',str(L/script),*args],cwd=L,stdout=stream,stderr=subprocess.STDOUT)
    row.update(returncode=result.returncode,seconds=time.time()-row['start'],
        tmp_after=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file()))
    (B/'FINAL_RUNS.json').write_text(json.dumps(runs,indent=2)+'\n')
    print(name,result.returncode,flush=True)
    if result.returncode<0:raise SystemExit('Process killed; stop without retry')
    if result.returncode or row['tmp_after']>200_000_000:raise SystemExit(result.returncode or 1)
if len(sys.argv)==1:
    run('refinement','work/build12/refine12.py')
    mutants=json.loads((B/'proofs/mutations/RESULT.json').read_text())['results']
    changed=[r['mutant'] for r in mutants if
        hashlib.sha256((L/'work/tree_r1'/r['source']).read_bytes()).hexdigest()!=r['source_sha256']
        or hashlib.sha256((L/'work/tree_r1'/Path(*r['test'].split('.')[:-2])).with_suffix('.py').read_bytes()).hexdigest()!=r['test_source_sha256']]
    if changed:run('mutations','work/build12/mutation_confirm.py',*changed)
    run('coverage','work/build12/coverage12.py')
    run('seal','work/n1fix2/seal.py')
    run('n1/kits','work/n1fix2/stage9.py')
    run('packet','work/n1fix2/packet_final.py','integrated','packet','contract')
    run('delivery','work/n1fix2/make_delivery.py')
    delivery=json.loads((L/'work/n1fix2/DELIVERY.json').read_text())
    run('package','work/n1fix2/package.py',str(L/delivery['path']))
    run('legacy_guards','work/n1fix2/legacy_guard_proof.py')
    run('comparison','work/n1fix2/compare.py')
run('coverage','work/build12/coverage12.py')
assert not json.loads((B/'GAPS.json').read_text()),'CPU gaps need a real proof before final delivery'
run('inference','work/build12/inference.py')
run('evidence_equality','work/build12/evidence_checks.py')
run('merge_finalize','work/build12/report12.py','--merge-only')
run('delivery','work/n1fix2/make_delivery.py')
delivery=json.loads((L/'work/n1fix2/DELIVERY.json').read_text())
run('package_resume','work/n1fix2/package.py',str(L/delivery['path']))
run('integrity','work/build12/integrity12.py')
run('report','work/build12/report12.py')
(B/'STATUS.md').write_text('# Build 12 status\n\nBuild work is complete; GO=false. The source, kits, frozen package, comparison and changed-statement coverage are verified. Findings, limitations and operator obligations are in ../../out/BUILD12_REPORT.md. Evidence: FINAL_INTEGRITY.json and FINAL_RUNS.json. FRAME64_ALL_READERS_UNQUALIFIED, production P receipt publication, BF16 parity and product-inference acceptance remain blocked.\n')
