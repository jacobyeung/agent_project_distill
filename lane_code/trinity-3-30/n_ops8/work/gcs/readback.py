"""n_ops8: compare a receipts list (name bytes sha256 md5 generation per line) with GCS metadata via mint_n.py check. Usage: readback.py LIST"""
import json,subprocess,sys
rows=[l.split() for l in open(sys.argv[1]) if l.startswith('q9/')]; ok=0
for n,size,sha,md5,gen in rows:
  m=json.loads(subprocess.run(['/scratch/jjyeung/envs/p1cpu/bin/python','/scratch/jjyeung/orch_n30/n_ops1/work/gcs/mint_n.py','check',n],capture_output=True,text=True).stdout or 'null')
  good=m is not None and m.get('size')==size and m.get('md5Hash')==md5 and str(m.get('generation'))==gen
  ok+=good; print(('OK ' if good else 'BAD'),n,m and m.get('size'),m and m.get('md5Hash'),m and m.get('generation'),m and m.get('timeCreated'))
print('match',ok,'of',len(rows))
