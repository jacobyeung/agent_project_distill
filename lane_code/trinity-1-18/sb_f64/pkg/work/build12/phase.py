from pathlib import Path
import json,os,subprocess,sys,time
L=Path(__file__).resolve().parents[2];B=L/'work/build12'
phase=sys.argv[1];runs=[]
def run(name,script,*args):
    folder=B/'proofs'/name;folder.mkdir(parents=True,exist_ok=True)
    total=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file())
    assert total<=200_000_000
    row=dict(name=name,tmp_before=total,start=time.time());runs.append(row)
    (B/'STATUS.md').write_text('# Build 12 status\n\nGO=false. Review fixes implemented; current validation: '+name+'. Evidence: '+phase+'_RUNS.json. FRAME64_ALL_READERS_UNQUALIFIED remains.\n')
    print('Starting '+name,flush=True)
    with (folder/'console.log').open('w') as log:
        result=subprocess.run([sys.executable,'-I','-s','-B',str(L/script),*args],cwd=L,stdout=log,stderr=subprocess.STDOUT)
    row.update(returncode=result.returncode,seconds=time.time()-row['start'],tmp_after=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file()))
    (B/(phase+'_RUNS.json')).write_text(json.dumps(runs,indent=2))
    print(name,result.returncode,flush=True)
    if result.returncode<0:raise SystemExit('Process killed; stop without retry')
    if result.returncode or row['tmp_after']>200_000_000:raise SystemExit(result.returncode or 1)
if phase=='proofs':
    run('mutations','work/build12/mutation_confirm.py',*sys.argv[2:])
    run('n1/text','work/n1fix2/proof_text.py')
    run('n1/row_delta','work/n1fix2/proof_row_delta.py')
    run('n1/forward','work/n1fix2/proof_forward9.py')
    run('preservation','work/build12/preservation.py')
    run('legacy_export','work/build12/legacy_export12.py')
    run('depth_sweep','work/build12/sweep.py')
    run('eat1','work/build10/final_eat10.py')
elif phase=='freeze':
    run('seal','work/n1fix2/seal.py')
    run('n1/kits','work/n1fix2/stage9.py')
    run('packet','work/n1fix2/packet_final.py','integrated','packet','contract')
    run('delivery','work/n1fix2/make_delivery.py')
    delivery=json.loads((L/'work/n1fix2/DELIVERY.json').read_text())
    run('package','work/n1fix2/package.py',str(L/delivery['path']))
    run('legacy_guards','work/n1fix2/legacy_guard_proof.py')
    run('comparison','work/n1fix2/compare.py')
