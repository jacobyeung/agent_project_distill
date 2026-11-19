"""Refresh changed kit files using the verified staging inventory; reuse external hashes."""
from pathlib import Path
import csv,hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import ROOT,read_json,sha,write_json,INPUTS

O=ROOT/'out';W=ROOT/'work'
baseline=W/'stage_baseline_STAGE_LIST.tsv';summary=W/'stage_baseline_STAGE_TOTALS.json'
old=read_json(summary);sha(baseline);sha(__file__)
assert sha(baseline)==old['input_sha256'][str(O/'STAGE_LIST.tsv')]
with baseline.open() as f:reader=csv.DictReader(f,delimiter='\t');fields=reader.fieldnames;rows=list(reader)
assert all(not v['unlisted'] for v in old['trace_check'].values())
for part in 'ABCH':
 assert sum(int(r['bytes']) for r in rows if r['bytes'] and part in r['parts'].split(','))==old['totals'][part]['bytes']
assert sum(int(r['bytes']) for r in rows if r['bytes'])==old['totals']['union']['bytes']

changed=[]
for r in rows:
 p=Path(r['path'])
 if p==ROOT/'code':
  manifest=O/'manifests'/(str(p).strip('/').replace('/','__')+'.sha256')
  saved=W/'stage_baseline_code_manifest.sha256'
  if not saved.exists():saved.write_bytes(manifest.read_bytes())
  assert sha(saved)==r['sha256']
  paths=sorted(x for x in p.rglob('*') if x.is_file() and not x.is_symlink())
  content='\n'.join(f'{sha(x)}  {x.relative_to(p)}' for x in paths)+'\n'
  manifest.write_text(content)
  r.update(bytes=str(sum(x.stat().st_size for x in paths)),sha256=sha(manifest),hash_source=f'manifest:{manifest.relative_to(ROOT)} ({len(paths)} files)')
  changed.append(str(p))
 elif p.parent==ROOT/'scripts' or p==O/'DRYRUN.json':
  r.update(bytes=str(p.stat().st_size),sha256=sha(p));changed.append(str(p))

p=ROOT/'scripts/run_H.sh'
rows.append(dict(path=str(p),kind='file',bytes=str(p.stat().st_size),sha256=sha(p),hash_source='computed',parts='A,B,C',note='code_pins member; H launch after A/B staging and outputs'))
changed.append(str(p))
with (O/'STAGE_LIST.tsv').open('w') as f:
 writer=csv.DictWriter(f,fields,delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(rows)
totals={}
for part in (*'ABCH','union'):
 selected=[r for r in rows if r['bytes'] and (part=='union' or part in r['parts'].split(','))]
 totals[part]=dict(bytes=sum(int(r['bytes']) for r in selected),entries=len(selected))
groups=old['by_group']
for part in 'ABCH':
 groups[part]['kit_folder']=sum(int(r['bytes']) for r in rows if r['bytes'] and part in r['parts'].split(',') and r['path'].startswith(str(ROOT)))
 assert sum(groups[part].values())==totals[part]['bytes']
# Staged directories are bound by their hash manifests, as in the source inventory.
for r in rows:
 if r['sha256']:INPUTS[r['path']]=r['sha256']
for p,h in old['input_sha256'].items():
 if p not in INPUTS:INPUTS[p]=h
sha(ROOT/'work/stage_list.py');sha(O/'STAGE_LIST.tsv')
write_json(O/'STAGE_TOTALS.json',dict(command='bash scripts/cpu.sh work/refresh_stage.py',
 baseline_command=old['command'],baseline_inventory_sha256=sha(baseline),baseline_totals_sha256=sha(summary),
 changed=changed,external_inputs='Reused verified baseline hashes; no external restaging or rehash',
 totals=totals,by_group=groups,missing=old['missing'],trace_check=old['trace_check'],trace_scope=old['trace_scope'],rows=len(rows)))
print(json.dumps(dict(status='PASS',totals=totals,updated_paths=len(changed))))
