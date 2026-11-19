import json,sqlite3,collections
from pathlib import Path
from census import W,BASE,rules,status
c=json.load(open(W/'out/CENSUS.json')); rs,extra=rules(); wants={e['canonical']:(e['frame_indices'],e) for e in c['entries'] if not e['exclusions']};found=collections.defaultdict(list); counts=collections.Counter()
p=Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite');con=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True)
for raw, in con.execute('SELECT row FROM rows ORDER BY i'):
 r=json.loads(raw);can,_=rs.canonical(r)
 if can:can=can.replace('scannetppv2/','scannetpp/')
 if can not in wants:continue
 counts[can]+=1
 if r.get('student_input',{}).get('frame_indices')==wants[can][0] and len(found[can])<3:found[can].append(r)
con.close()
(W/'inputs/binding_sources.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for rr in found.values() for r in rr))
print('scenes with frame matches',len(found),collections.Counter(k.split('/')[0] for k in found))
print('large',[(can,wants[can][1]['measurement']['area_m2'],len(found[can]),counts[can]) for can in wants if wants[can][1]['measurement']['area_m2']>=40])
