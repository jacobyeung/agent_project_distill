"""Package and verify the final report without changing the qualified source."""
from pathlib import Path
import subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build16'
results=[]
for name in ('delivery','integrity','storage'):
    with (B/(name+'.log')).open('w') as log:
        p=subprocess.run([sys.executable,'-I','-s','-B',str(B/(name+'16.py'))],
            cwd=L,stdout=log,stderr=subprocess.STDOUT)
    if p.returncode<0:raise SystemExit('Process killed; stopped without retry: '+name)
    assert p.returncode==0,(name,p.returncode)
    results.append(name+' PASS')
    print(results[-1],flush=True)
(B/'finish.log').write_text('Final qualification: QUALIFICATION.json\nInitialization boundary: proofs/init_boundary/TESTS.json\n'+
    '\n'.join(results)+'\nGO=false; production qualification remains incomplete.\n')
