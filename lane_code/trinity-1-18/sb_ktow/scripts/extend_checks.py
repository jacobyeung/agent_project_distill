from pathlib import Path
p=Path('code/dryrun.py');s=p.read_text()
s=s.replace("m=manifest();selected=[];ar=[];errors=[]", "m=manifest();selected=[];ar=[];errors=[]\n from replay import price,load_selector\n from e2e_reader.geometry import from_npz\n head=load_selector()")
needle="ar.append(dict(capture=c['canonical'],status='PASS' if clean(a)==clean(b) and clean(da)==clean(db) and all(v==0 for v in differences.values()) else 'FAIL',differences=differences,pose=a,depth=da))"
replace="""geo=from_npz(capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'geometry.npz');cache=read_json(capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'candidates.json')
   dist={}
   for arm in ('A0','A2'):
    kwargs=dict(cache=cache,gt=gt if arm=='A2' else None,head=head)
    left=price(c,geo,**kwargs);right=price(c,geo,**kwargs)
    dist[arm]=dict(status='PASS' if clean(left)==clean(right) else 'FAIL',rows=len(left),differences=[0. if x['prediction']==y['prediction'] else None for x,y in zip(left,right)],responses=[x['response'] for x in left])
   ar.append(dict(capture=c['canonical'],status='PASS' if clean(a)==clean(b) and clean(da)==clean(db) and all(v==0 for v in differences.values()) and all(v['status']=='PASS' for v in dist.values()) else 'FAIL',differences=differences,pose=a,depth=da,distance=dist))"""
assert needle in s;s=s.replace(needle,replace)
p.write_text(s)
# Enforce named source identity and input shape at the camera interchange boundary.
p=Path('code/evaluate.py');s=p.read_text().replace("if len(d['items'])!=450:raise ValueError('Camera parity requires all 450 routed items')", """if len(d['items'])!=450:raise ValueError('Camera parity requires all 450 routed items')
 if len({x['id'] for x in d['items']})!=450:raise ValueError('Duplicate camera item IDs')
 for x in d['items']:
  if np.asarray(x['raw_pose32']).shape!=(32,9) or np.asarray(x['depth32']).shape!=(32,51,51):raise ValueError('Missing stored 32-frame pose/depth arrays')
  if len(x['anchor_slots'])!=32:raise ValueError('Camera LM frame map differs')""")
p.write_text(s)
# Preflight remains CPU-only, and one process is launched per part.
p=Path('code/runner.py');s=p.read_text().replace("signal.signal(signal.SIGALRM,stop);signal.alarm(seconds)","signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop);signal.alarm(seconds)")
p.write_text(s)
