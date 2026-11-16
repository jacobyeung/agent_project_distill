import sqlite3,json,collections,sys
S='/scratch/jjyeung/orch_n30/rows_rebuild3/out/rows/d0_v5/vqa/rows.sqlite'
con=sqlite3.connect(f'file:{S}?mode=ro&immutable=1',uri=True)
print([r for r in con.execute("select name,sql from sqlite_master")])
pins=collections.defaultdict(set); qt=collections.Counter(); sc=collections.defaultdict(set)
ex={}
for i,row,t in con.execute('select i,row,target from rows'):
    d=json.loads(row); a=d['dataset']+'/'+d['scene']
    pins[a].add(tuple(d['student_input']['frame_indices'])); qt[(d['dataset'],d['question_type'])]+=1; sc[d['dataset']].add(d['scene'])
    if d['dataset'] not in ex: ex[d['dataset']]=(d['scene'],d.get('license'),d['student_input'].get('total_num_frames'),d['student_input'].get('fps'))
print({k:len(v) for k,v in sc.items()}); print(ex)
print('scenes with >1 pin set',sum(len(v)>1 for v in pins.values()), 'of',len(pins))
for k,v in sorted(qt.items()): print(k,v)
json.dump({a:[list(p) for p in v] for a,v in pins.items()},open('v5_scene_pins.json','w'))
