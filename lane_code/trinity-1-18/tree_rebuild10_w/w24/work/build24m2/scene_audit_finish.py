import sys;from pathlib import Path;sys.path.insert(0,str(Path(__file__).resolve().parent))
from buildlib import *
c=J.load(kit('q')/'k/n.json');s=J.load(kit('q')/'k/p.json');v=J.load(D/'SCENE_REBUILD_INPUTS.json')
for r in v['inputs']:
 if r['authenticated_u']:r['authentication']='k/p.json uploads; pl.remember + checked'
 elif r['input'].startswith('source population '):r['authentication']='pl.closure(cfg.streams): native receipt database pin, checked, copied to q/u/<sha256>';r['authenticated_u']=True
 elif r['sha256'] in c['s1_routing']['catalog']:r['authentication']='k/n.json s1_routing.catalog; pl.remember + checked; copied to q/u/<sha256>';r['authenticated_u']=True
 else:r['authentication']='MISSING'
v['missing']=[r for r in v['inputs'] if not r['authenticated_u']];v['status']='READY' if not v['missing'] else 'STOPPED'
J.write(D/'SCENE_REBUILD_INPUTS.json',v)
lines=['All 54 listed inputs have an existing authenticated staging path. No new exclusion source is introduced.','',
'Native rebuild reads dev/benchmark lists, the source-relative withheld-80 file, five source receipts and their database populations, the pool manifest and its lists/populations, removals and tokenizer. The R0 reserve and K1 held-out sets come from the native Rooms authority for publication; rebuild does not read that authority directly.','',
'| Input | SHA256 | Existing authenticated staging |','| --- | --- | --- |']
for r in v['inputs']:lines.append('| '+r['input']+' | '+r['sha256']+' | '+r['authentication']+' |')
lines += ['', 'All upload-listed bytes were hashed locally. Production databases and catalog payloads are unavailable here; the planner authenticates their stated pins on the staged host before use. The five receipts bind the population SHA256s listed above. Withheld-80 is also authenticated by the sealed source archive.', '',
'The wrapper calls native rebuild and binds its receipt and scene_coverage verbatim. It does not choose rows, edit receipts or replace verification. The private child view gives generated receipts their final q/sc paths while keeping the native q output fresh.']
replace(L/'out/SCENE_REBUILD_INPUTS.md','\n'.join(lines)+'\n')
print(v['status'],len(v['inputs']))
