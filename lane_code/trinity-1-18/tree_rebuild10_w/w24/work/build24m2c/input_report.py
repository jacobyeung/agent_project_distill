from common import *
sys.path.insert(0,str(kit('q')/'b'))
from px import inventory
from z import selected400
audit=J.load(D/'PIN_AUDIT.json');staged=inventory(kit('q'))
manifest=J.load(L.parent/'ext/m400real/MANIFEST.json');small={}
for v in manifest['files']:
 try:selected400(v['path'])
 except ValueError:continue
 small[v['sha256']]=v
uploads={v['sha256'] for v in J.load(kit('q')/'k/p.json')['uploads']}
missing=[]
for row in audit['inputs']:
 h=row['sha256']
 if h in uploads:row['source']='k/p.json upload, checked and staged as u/'+h
 elif h in small:
  row['source']='authenticated m400 small archive member, checked by planner';row['bytes']=small[h]['bytes']
 elif h in staged:row['source']='sealed k/l.json member inventory, resolved by SHA256 and checked'
 else:
  row['source']='NO INVENTORIED SOURCE';missing.append(row)
audit['missing']=missing
J.write(D/'PIN_AUDIT_FINAL.json',audit)
lines=['The planner never opens a literal receipt path as a fallback. A missing SHA256 refuses R1_STAGED_PIN_MISSING:<sha256>:<config field> before preparation.','',
 'The following pins have no source in the available authenticated upload, m400-member, joined-file, tar-member or package-member inventories. The production small archive e00 is not supplied locally; its private staged members are indexed by hash at runtime. No source or size is invented.','',
 '| SHA256 | Size (bytes) | Config field | Evidence |','| --- | --- | --- | --- |']
for r in missing:
 reason='m400 MANIFEST explicitly skips this database as store or weights; no k/l.json payload binds it' if r['sha256'].startswith('4e8e6c04') else 'Catalog entry has no available member inventory or local replica; runtime small-archive coverage remains unverified'
 lines.append('| '+r['sha256']+' | '+(str(r['bytes']) if r['bytes'] is not None else 'unknown; not recorded in supplied receipt')+' | '+'; '.join(r['fields'])+' | '+reason+' |')
lines.extend(['','The routing receipt ca0616db binds database 4e8e6c04 with 47,898 rows but no byte count. Its absence is the expected first discovery refusal, in mode r before preparation. The eac5f9f0 catalog entry is an additional unresolved dependency after that boundary.','',
 'Frame map 17aa3e9e (14,502,816 bytes) and tokenizer 5f9e4d49 (12,807,982 bytes) are authenticated m400 small-archive members; their large byte bodies are not part of the local snapshot. They are not classified as absent from production staging.'])
replace(L/'out/MISSING_STAGED_PINS.md','\n'.join(lines)+'\n')
scene=J.load(L/'work/build24m2/SCENE_REBUILD_INPUTS.json');missing_scene=[]
for r in scene['inputs']:
 h=r['sha256']
 if h in uploads:source='k/p.json upload; checked and staged as u/<sha256>'
 elif h in small:source='authenticated m400 member; planner checks and stages u/<sha256>'
 elif h in staged:source='k/l.json '+staged[h][0]['field']+'; planner resolves by SHA256, checks and stages u/<sha256>'
 else:source='MISSING: no authenticated staged member';missing_scene.append(r['input'])
 r['authentication']=source;r['authenticated_u']=not source.startswith('MISSING')
scene.update(status='STOPPED',missing=missing_scene,installed=False)
J.write(D/'SCENE_REBUILD_INPUTS.json',scene)
assert missing_scene==['source population camera'],missing_scene
lines=['Item 2b is stopped: P’s camera/routing population 4e8e6c04 has no authenticated staged member. No scene-rebuild step is installed in q, n, n_go or qd. Native scene verification remains unchanged.','',
 'Native rebuild reads the benchmark and merged dev lists, the source-relative withheld-80 list, five source receipts and their populations, and pool evidence, exclusions, removals and tokenizer. R0 and K1 are read by the requested native room census; rebuild itself does not read those authorities.','',
 '| Input | SHA256 | Authenticated staging |','| --- | --- | --- |']
for r in scene['inputs']:lines.append('| '+r['input']+' | '+r['sha256']+' | '+r['authentication']+' |')
lines.extend(['','The complete input census has 54 entries. The missing routing population blocks installation under item 2b’s explicit stop condition. Existing null rebuild/coverage fields are preserved; no synthetic evidence enters the production kits.','',
 'After the routing source is staged, mode q will still need native scene rebuild evidence before preparation. The kit census reports admitted rows and protected-status row keys only after successful native preparation; it grants no exemption from the verifier.'])
replace(L/'out/SCENE_REBUILD_INPUTS.md','\n'.join(lines)+'\n')
print('scene installation STOPPED; missing pin records',len(missing))
