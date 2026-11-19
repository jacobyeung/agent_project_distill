#!/bin/bash
# r1_ops8: read-only check of okh7/h_6ed2c7aa/m400 (pool, login node): s.tar manifest, clause-by-clause handover refusal cause
export TZ=UTC; D=/project/community/jjyeung/okh7/h_6ed2c7aa/m400; cd /tmp
cat $D/DONE.json; sha256sum $D/e.json $D/s.tar $D/RP.json $D/r.json | cut -c1-64,66-
cat $D/h.out | cut -c1-300 | tail -3; cat $D/s.err
python3 - $D <<'PY'
import json,sys,tarfile,collections
D=sys.argv[1]; t=tarfile.open(D+'/s.tar')
mem={m.name:m for m in t.getmembers()}
man=json.load(t.extractfile('MANIFEST.json'))
print('MANIFEST schema',man['schema'],'step',man['step'],'checkpoint',man['checkpoint'],'files',len(man['files']),'bytes',man['bytes'],'skipped',len(man['skipped']),'mismatch',sum(1 for f in man['files'] if not f['match']))
print('skipped reasons',dict(collections.Counter(s['reason'] for s in man['skipped'])))
for s in man['skipped']:
  if s['reason'] not in ('checkpoint shard','export shard (GCS tar)'): print(' SKIP',s['reason'],s['path'][-110:])
for f in man['files']:
  p=f['path']
  if any(k in p for k in ('tokenizer','config.json','model','manifest','vocab','generation','special_tokens','chat_template')): print(' FILE',f['bytes'],f['sha256'][:8],p[-120:])
def J(p): return json.load(t.extractfile('files'+p))
rp=json.load(open(D+'/RP.json')); e=json.load(open(D+'/e.json'))
print('e.json keys',sorted(e)[:20]); print('e.json schema',e.get('schema'),'step',e.get('step'),'stop',e.get('stop',e.get('stop_step')),'checkpoint_status',e.get('checkpoint_status'))
cfg=J(rp['config']['path']); b=J(rp['binding']['path']); c=J(rp['checkpoint']['path'])
art=J(rp['config']['path'].split('/inputs/')[0]+'/m400/artifact.json')
prepp=rp['preparation']; prep=J(prepp['path']) if isinstance(prepp,dict) and 'path' in prepp else None
idn='9459724f1b925b7d750628ccb36d7a29f871e953751c0e1d2c9abaea67d567e4'
print('clause complete.step==400:',c.get('step'),'| schema',c.get('schema'),'| complete.binding==bound',c.get('binding')==b,
 '| bound.config_sha==id',b.get('config_sha256')==idn,'| art.config_sha==id',art.get('config_sha256')==idn,
 '| cfg.prep==RP.prep',cfg.get('preparation')==rp['preparation'],'| bound.prep==RP.prep',b.get('preparation')==rp['preparation'],
 '| prep.config_sha==id',(prep or {}).get('config_sha256')==idn)
print('complete layouts',bool(c.get('layouts')),'rng files',[k for k in c.get('files',{}) if k.startswith('rng')][:6],'nfiles',len(c.get('files',{})))
PY
