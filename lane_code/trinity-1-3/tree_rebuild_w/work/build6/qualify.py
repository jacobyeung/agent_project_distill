"""Run strengthened row proofs, then the delivered tree/base suite sequentially."""
import json,subprocess,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build6'
sys.path.insert(0,str(B));from compact_tmp import inventory
packet=json.loads((B/'proofs/packet/results.json').read_text())
if len(packet)!=202 or any(r['outcome']!='passed' for r in packet.values()):
 raise ValueError('Resolve the final packet suite before packaged qualification')
steps=[('rows_build5',['rows.py','build5']),('rows',['monitor_rows.py']),('row_compare',['row_compare.py']),('package',['run_delivery.py'])]
sizes=[]
for name,args in steps:
 before=sum(inventory(L/'work/tmp').values());assert before<=200_000_000
 with (B/(name+'_qualification.log')).open('w') as log:
  result=subprocess.run([sys.executable,'-I','-s','-B',str(B/args[0]),*args[1:]],stdout=log,stderr=subprocess.STDOUT)
 if result.returncode<0:raise RuntimeError('Qualification process was killed; stop without retry')
 if result.returncode:raise RuntimeError(name+' qualification failed; inspect its log')
 after=sum(inventory(L/'work/tmp').values());assert after<=200_000_000
 sizes.append(dict(proof=name,before_bytes=before,after_bytes=after))
 (B/'proofs/rows/TEMPORARY_SIZES.json').write_text(json.dumps(sizes,indent=2)+'\n')
 with (B/'STATUS.md').open('a') as f:f.write('\nCompleted qualification step `'+name+'`; receipt/log: `work/build6/'+name+'_qualification.log`.\n')
 print(name+' completed',flush=True)
