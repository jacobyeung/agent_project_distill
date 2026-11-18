from pathlib import Path
import json,os,subprocess,sys
L=Path(__file__).resolve().parents[2]; B=L/'work/n1fix2'
steps=[]
for name,script,args in [('text','proof_text.py',[]),('forward','proof_forward9.py',[]),
        ('edge_tests','test_runner.py',[str(L/'work/merge11/proofs/n1/edge_final'),'tests.test_r2_n1fix']),
        ('inference_inventory','inference_inventory.py',[])]:
    row=dict(name=name,status='running');steps.append(row)
    (B/'PROOF_STEPS.json').write_text(json.dumps(steps,indent=2))
    (B/'STATUS.md').write_text('# Build n1fix status\n\nPacket and mutation proofs pass. Running '+name+'. GO=false. Evidence: PROOF_STEPS.json.\n')
    with (B/(name+'.log')).open('w') as log:
        code=subprocess.run([sys.executable,'-I','-s','-B',str(B/script),*args],cwd=L,stdout=log,stderr=subprocess.STDOUT).returncode
    row.update(returncode=code,status='complete' if code==0 else 'failed')
    (B/'PROOF_STEPS.json').write_text(json.dumps(steps,indent=2))
    print(name,code,flush=True)
    if code<0:raise SystemExit('Process killed; stop without retry.')
    if code:raise SystemExit(code)
