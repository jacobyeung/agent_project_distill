import sqlite3,json
Q='/tmp/q_22c714e1_173626/s/aws/u/ap'
for f,cats in (('/1742c666/s/q127808/vxm_m4/rows.sqlite',('object_counting','object_rel_distance','object_abs_distance')),('/5e1d07a4/f/h/r11/rows.sqlite',('routing_trace',))):
  c=sqlite3.connect('file:'+Q+f+'?mode=ro&immutable=1',uri=True); seen=set()
  for (r,) in c.execute('select row from rows limit 5000'):
    d=json.loads(r)
    if d['category'] not in cats or (d['dataset'],d['category']) in seen: continue
    seen.add((d['dataset'],d['category'])); si=d['student_input']
    print('ROW',d['dataset'],d['category'],'scene',d['scene'],'qid',d['qid'],'answer',str(d.get('answer'))[:80])
    print('  SI keys',sorted(si.keys()))
    for k,v in si.items():
      if k in ('frames','frame_indices'): continue
      print('  SI',k,'=',json.dumps(v)[:400].replace('\n',' '))
    for k,v in d.items():
      if k not in ('student_input','target','pose_sample'): continue
      if k!='student_input': print('  ',k,'=',json.dumps(v)[:200])
