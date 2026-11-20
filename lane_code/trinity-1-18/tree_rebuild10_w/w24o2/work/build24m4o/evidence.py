import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import gzip,tarfile,difflib
from collections import Counter
from student_pilot.p3_provenance import digest
h='e5be8157d855b4c9f611876b7fde5d0c7d8bd11def319e15c00e37daef2c3536'
archive=L/'work/build24m4h/p.tar'
archive_sha=z.sha(archive)
pf={};text={}
with tarfile.open(archive) as t:
    for m in t:
        assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
        raw=t.extractfile(m).read();pf[m.name]=hashlib.sha256(raw).hexdigest()
        if m.name.startswith(('student_pilot/','trace_format/','launch_r1/')):
            p=D/'p_tree'/m.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            if m.name.endswith('.py'):text[m.name]=raw.decode()
assert digest(pf).startswith('b83a8a35')
write(D/'P_TREE.json',dict(archive=str(archive.relative_to(L)),sha256=archive_sha,kit_archive_sha256=h,tree=digest(pf),files=pf,qualification='Local tar serialization differs from the staged archive pin; every member is authenticated by the exact P tree inventory digest.'))
changed={n:dict(P=pf.get(n),N=z.sha(T/n) if (T/n).is_file() else None) for n in text if pf.get(n)!=(z.sha(T/n) if (T/n).is_file() else None)}
write(D/'P_CHANGED.json',changed)
for n in ('s1_routing','s1_exclusions','s1_scene_census','s1_pool','carrier_c1_routing','training_contract'):
    name='student_pilot/'+n+'.py'
    diff=''.join(difflib.unified_diff(text.get(name,'').splitlines(True),(T/name).read_text().splitlines(True),fromfile='P/'+name,tofile='C/'+name))
    (D/(n+'.diff')).write_text(diff)
rd=json.loads(gzip.decompress((E/'rd0/rdiff.json.gz').read_bytes()))
print('P_TREE',digest(pf),'N',len(rd['N']),'ABSENT',len(rd['P_absent']))
print('FIRST_N',rd['N'][0])
print('FIRST_ABSENT',rd['P_absent'][0])
unlisted=[r for r in rd['P_absent'] if not r['removal_list_sha256s']]
counts=dict(unlisted_sources=dict(Counter(str(r['key'][3]) for r in unlisted)),unlisted_datasets=dict(Counter(r['key'][0] for r in unlisted)),same_i=sum(r['i']==r['P']['i'] for r in rd['N']))
print('COUNTS',counts);write(D/'RD_COUNTS.json',counts)
ps=z.load(E/'p_sample.json');rows=[dict(s,parsed=json.loads(s['row'])) for s in ps['rows']]
write(D/'P_SAMPLE_OVERVIEW.json',[dict(i=s['i'],sample=s['class'],qid=s['parsed'].get('qid'),source=s['parsed'].get('s1_source'),kind=s['parsed'].get('routing',{}).get('question_type'),keys=list(s['parsed'])) for s in rows])
print('PS_CLASSES',Counter(s['class'] for s in rows))
print('NULL_SAMPLES',[(s['i'],s['parsed']['qid'],s['parsed']['routing']['question_type'],s['class']) for s in rows if not s['parsed'].get('s1_source')])
for name in ('k_b1m.json','k_b1r.json','k_b3r.json'):
    v=z.load(E/name);print(name,'keys',list(v))
    if name=='k_b1m.json':
        print('P_TYPES',json.dumps(v['types']));print('P_COMPAT',json.dumps(v['legacy_compatibility']));print('P_FILTERS',json.dumps(v['source_scene_exclusions']['sources']))
log=[]
for s in (E/'job.log').read_text().splitlines():
    try: v=json.loads(s)
    except ValueError: continue
    if isinstance(v,dict) and 'pool_source' in v:
        log.append(v)
write(D/'LOG_SOURCES.json',log)
print('LOG_SOURCES',[(r['pool_source'],r.get('retained'),r.get('counts')) for r in log])
print('DIFF_LINES',[(n,len((D/(n+'.diff')).read_text().splitlines())) for n in ('s1_routing','s1_exclusions','s1_scene_census','s1_pool','carrier_c1_routing','training_contract')])
