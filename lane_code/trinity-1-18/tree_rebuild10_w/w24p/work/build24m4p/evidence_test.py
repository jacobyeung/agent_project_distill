import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import gzip, importlib.util
from collections import Counter
sp=importlib.util.spec_from_file_location('nd_evidence',L/'out/rcj/nd.py');nd=importlib.util.module_from_spec(sp);sp.loader.exec_module(nd)
root=D/('evidence_'+str(time.time_ns()));q=root/'q';(q/'u').mkdir(parents=True);(root/'s').symlink_to(T,target_is_directory=True)
cfg=z.load(kit('n')/'k/n.json');write(q/'n.json',cfg)
for pin in [*cfg['remove_files'],cfg['dev_scene_exclusions']]:
 h=pin['sha256'];p=T/'student_pilot/r2_dev_merged.json' if h==nd.DEV else input_file(h)
 assert z.sha(p)==h
 if not (q/'u'/h).exists():(q/'u'/h).symlink_to(p)
rem,scenes,state=nd.native_rules(q/'selection/rows.sqlite')
E=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173680/173680')
summary=z.load(E/'rd0/rdiff_summary.json');detail=E/'rd0/rdiff.json.gz'
assert summary['rdiff_sha256']==z.sha(detail)
assert summary['inputs']['P']['sha256']==nd.GATE
assert summary['tree']['row_removals_sha256']==z.sha(T/'student_pilot/row_removals.py')
assert [{k:v for k,v in p.items() if k!='path'} for p in summary['removal_files']]==state['removal_files']
data=json.loads(gzip.decompress(detail.read_bytes()));counts=Counter();rows=[]
for entry in data['P_absent']:
 ds,scene,qid,src=entry['key'];r=dict(dataset=ds,scene=scene,qid=qid,label_row_keys=entry['removal_keys'])
 if src:r['s1_source']=dict(name=src)
 a=nd.attribution(r,rem,scenes)
 assert a['removal_list_sha256s']==entry['removal_list_sha256s']
 assert a['attribution']!='unattributed'
 counts[(src,a['attribution'])]+=1;rows.append(dict(key=entry['key'],**a))
kept=sum(r['key'][3]=='U_Faithful' for r in data['N'])
assert kept==718 and len(rows)==4797
assert sum(r['attribution']=='scene' for r in rows)==4768
assert sum(r['attribution']=='list' for r in rows)==29
write(D/'ABSENCE_EVIDENCE_TEST.json',dict(status='PASS',absent=len(rows),kept_U_Faithful=kept,
 counts=[dict(source=s,attribution=a,rows=n) for (s,a),n in counts.items()],state=state,
 scope='Authenticated 173680 absent-key and removal-key evidence; native predicates and all pinned files. This is not a full database content comparison.'))
(D/'ABSENCE_EVIDENCE_24M4P.json.gz').write_bytes(gzip.compress(nd.raw(dict(rows=rows)),mtime=0))
print('Native pinned attribution: 4768 merged-scene + 29 listed; 718 U_Faithful kept.')
