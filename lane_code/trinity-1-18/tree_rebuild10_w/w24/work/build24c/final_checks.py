from pathlib import Path
import subprocess,sys,json,shutil
L=Path(__file__).resolve().parents[2];D=L/'work/build24c'
# Retain the first successful run, and exercise every staging helper again
# without stamp reuse. Move, never erase, the earlier extracted proof source.
for name in ('q','n'):
 node=D/'sequence'/name/'q_22c714e1_20';a=L/'attic/build24c/sequence'/name;a.mkdir(parents=True,exist_ok=True)
 for p in (node/'s',node/'p'):
  if p.exists():
   target=a/p.name
   if target.exists():target=a/(p.name+'_1')
   p.rename(target)
 shutil.copyfile(D/'sequence'/name/'operator/shell.log',a/'shell.log')
records=[]
for name in ('sequence','runtime_tests','kit_tests','lookahead'):
 with (D/(name+'_final.log')).open('w') as f:
  p=subprocess.run([sys.executable,'-I','-s','-B',str(D/(name+'.py'))],stdout=f,stderr=subprocess.STDOUT)
 records.append(dict(name=name,returncode=p.returncode));(D/'FINAL_CHECKS.json').write_text(json.dumps(records,indent=2)+'\n');print(name,p.returncode,flush=True)
 if p.returncode:raise SystemExit(p.returncode)
