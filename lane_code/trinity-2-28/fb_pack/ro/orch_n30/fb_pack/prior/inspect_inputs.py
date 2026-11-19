import json, hashlib, sqlite3, base64
from pathlib import Path
W=Path.cwd(); T=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1'); O=T.parent.parent/'out'
cfg=json.loads((O/'N_LAUNCH_CONFIG.json').read_text())
p=Path('/data2/jjyeung/agent_project_data/distill_design/R1_M200_TRACE_ANALYSIS_20261119.md')
b=p.read_bytes()
e={'path':str(p),'sha256':hashlib.sha256(b).hexdigest()}
(W/'out/EVIDENCE_S400.md').write_text('Source: '+str(p)+'\nSHA256: '+e['sha256']+'\n\n'+'\n'.join(f'{i}: {s}' for i,s in enumerate(b.decode().splitlines(),1) if 436<=i<=480)+'\n')
(W/'out/EVIDENCE_PIN.json').write_text(json.dumps({'inputs':[e], 'excerpt':'out/EVIDENCE_S400.md'},indent=2)+'\n')
print((W/'out/EVIDENCE_S400.md').read_text())
for pin in cfg['remove_files']:
 p=Path(pin['path']); print('REMOVE',p, 'exists',p.is_file(),'bytes',p.stat().st_size if p.is_file() else None)
for k in ['mix','row_sources','room_audit','wording_exclusion','camera_wording_exclusion']:
 pin=cfg['r1_training'][k]; p=Path(pin['path']); print(k,p,p.is_file())
kit=json.loads((O/'kit_n_go/k/n.json').read_text()); kit=json.loads(base64.b64decode(kit['payload']))
print('KIT config root keys',list(kit))
print('KIT sampling',kit.get('r2_sampling'))
print('KIT remove hashes match', [p['sha256'] for p in cfg['remove_files']]==[p['sha256'] for p in kit['remove_files']])
p=Path(cfg['r1_training']['direction_twins']['source_database']['path'])
conn=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True)
print('DB schema',conn.execute('select sql from sqlite_master').fetchall())
seen=set()
for raw, in conn.execute('SELECT row FROM rows ORDER BY i'):
 r=json.loads(raw); typ=r.get('question_type',''); group=(typ,r.get('facing'))
 if 'direction' in typ and group not in seen:
  seen.add(group); print('SAMPLE',json.dumps(r,ensure_ascii=False))
 if len(seen)>=9:break
conn.close()
with Path(cfg['r1_training']['direction_twins']['rows']['path']).open() as f:print('TWIN',f.readline())
(W/'STATUS.md').write_text('Stage 1: Inspected the sealed N tree and launch kit on trinity-1-18. The sampler enforces four draws per row per 1,000 steps and accepts only unique, exhaustive cell indices; it has no per-row weight field. The bound population is an incomplete zero-count placeholder, so a production draw audit is not yet available. The census will use authenticated source rows and removal lists; no tree or external file has changed.\n')
