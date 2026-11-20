import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import gzip,importlib.util
from collections import Counter
from student_pilot.s1_exclusions import Exclusions
from student_pilot.p3_provenance import file_pin

def mod(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
rdmod=mod('rd_a',L/'work/build24m4n/rdiff.py')
ps=mod('ns_a',L/'out/rcj/nd.py')
old=mod('student_pilot.p_ex',D/'p_tree/student_pilot/s1_exclusions.py')
newdev=T/'student_pilot/r2_dev_merged.json'
assert z.sha(newdev)=='a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5'
olddev=L/'work/build24m4n/inputs/969cdb56ce508eff79390d67099c889b92bd360e93dc42ba07f3683ec216a986'
bench=L/'work/build24m4n/inputs/3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970'
assert z.sha(olddev)==olddev.name and z.sha(bench)==bench.name
nrule=Exclusions(file_pin(newdev),file_pin(bench));prule=old.Exclusions(file_pin(olddev),file_pin(bench))
rd=json.loads(gzip.decompress((E/'rd0/rdiff.json.gz').read_bytes()))
bykey={tuple(r['key']):r for r in rd['N']}
summary={};absent=[]
for r in rd['P_absent']:
 k=r['key'];row=dict(dataset=k[0],scene=k[1],qid=k[2]);rule=nrule.matches(row);prior=prule.matches(row)
 absent.append(dict(**r,N_scene_matches=rule,P_scene_matches=prior))
summary['absent_total_by_dataset']=dict(Counter(r['key'][0] for r in absent))
summary['unlisted_source_x_rule']=[dict(source=s,rule=k,rows=v) for (s,k),v in Counter((r['key'][3],'+'.join(k for k,v in r['N_scene_matches'].items() if v) or 'unknown') for r in absent if not r['removal_list_sha256s']).items()]
summary['unlisted_old_scene_hits']=sum(any(r['P_scene_matches'].values()) for r in absent if not r['removal_list_sha256s'])
summary['matched_source_counts']=dict(Counter(str(r['key'][3]) for r in rd['N']))
summary['matched_new_scene_hits']=sum(any(nrule.matches(dict(dataset=r['key'][0],scene=r['key'][1])).values()) for r in rd['N'])
summary['ordinal_equal']=sum(r['i']==r['P']['i'] for r in rd['N'])
samples=[]
for s in z.load(E/'p_sample.json')['rows']:
 row=json.loads(s['row']);k=ps.key(row);nr=bykey.get(k)
 hypothetical=hashlib.sha256(rdmod.packed((nr['i'],s['row'],s['target']))).hexdigest() if nr else None
 samples.append(dict(i=s['i'],key=k,sample=s['class'],N_i=nr['i'] if nr else None,
    stored_row_target_identical_after_ordinal_change=hypothetical==nr['content_sha256'] if nr else None,
    source=k[3],kind=row.get('routing',{}).get('question_type'),N_scene_matches=nrule.matches(row),P_scene_matches=prule.matches(row)))
summary['sample_null_present']=sum(s['source'] is None and s['N_i'] is not None for s in samples)
summary['sample_null_bytes_proven_equal']=sum(s['source'] is None and s['stored_row_target_identical_after_ordinal_change'] is True for s in samples)
summary['sample_pool_present']=sum(s['source'] is not None and s['N_i'] is not None for s in samples)
summary['sample_pool_bytes_proven_different']=sum(s['source'] is not None and s['stored_row_target_identical_after_ordinal_change'] is False for s in samples)
summary['sample_absent_null_kinds']=dict(Counter(s['kind'] for s in samples if s['source'] is None and s['N_i'] is None))
summary['sample_source_x_scene']=dict(Counter(str((s['source'],'dev' if s['N_scene_matches']['dev'] else 'kept')) for s in samples))
write(D/'DIAG_COUNTS.json',summary);write(D/'SAMPLE_HASH_PROOFS.json',samples)
(D/'ABSENT_SCENE_MATCHES.json.gz').write_bytes(gzip.compress(ps.raw(dict(scope='Offline identity replay on P keys; not persisted N per-row build reasons',rows=absent)),mtime=0))
print(json.dumps(summary,indent=2))
# Map only the traceback's source hashes; the manifest discrepancy is separate.
hashes=['7df01d516786412a88c453fd2f9f703f7d6b99d1d1c143224e073b57c35949e7','ed09d425128122ae431da5cfeb240439c29c2555714f7bd97a5afbb289457006','99856996d726b051b394036afdee24ff5310b036715a751132d20fe9783e5207']
from student_pilot.source_seal import inventory
inv=inventory(T);write(D/'TRACEBACK_MAP.json',{h:[n for n,v in inv.items() if v==h] for h in hashes})
