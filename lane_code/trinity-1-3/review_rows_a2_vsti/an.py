import json,collections,numpy as np
res=json.load(open('rv_out.json'))
rows=[o for x in res for o in x['rows']]
print('rasters',len(res),'rows',len(rows))
e=collections.Counter(err.split(' ')[0] for o in rows for err in o['errors']);print('errors',e)
for o in rows:
    if o['errors']:print(o['qid'],o['t'],o['errors'][:3]);break
# conventions
cc=collections.Counter();gl=[];camy=[];above=[];fz=[]
for x in res:
    s=x['src'];ds=x['rows'][0]['ds']
    cc[(ds,s['my_factor'],s['my_layout'])]+=1
    gl.append(max(v[0] or 0 for k,v in s['conv'].items() if k.startswith('gl')))
    camy.append(s['camy_dot_z']);above.append(s['cam_minus_p1_z'])
    if 'floor_normal_z' in s:fz.append((s['floor_normal_z'],s['cam_above_floor_z']))
print(cc)
q=lambda a:np.round(np.quantile(a,[0,.01,.5,.99,1]),3)
print('max GL containment',q(gl));print('cam y . +Z',q(camy));print('cam height over p1',q(above))
fz=np.array(fz);print('floor-labelled scenes',len(fz),'normal|z|',q(fz[:,0]),'cam above floor',q(fz[:,1]))
# center-vs-closest disagreement
d=collections.defaultdict(collections.Counter)
for o in rows:d[o['t']][o['center_answer']==o['mine']]+=1
print('center-convention agreement',{t:f'{v[True]}/{sum(v.values())}' for t,v in d.items()})
# visibility in frame f
vis=collections.defaultdict(collections.Counter)
for o in rows:
    vis[o['t']]['all_visible' if all(o['vis_f']) else ('none' if not any(o['vis_f']) else 'some')]+=1
    vis[o['t']]['centres_in_image_all' if all(o['inimg']) else 'centre_out']+=1
    vis[o['t']]['all_first_seen<=f' if all(o['fs_lt_f']) else 'some_first_seen_after_f']+=1
for t,v in sorted(vis.items()):print(t,dict(v))
# answer visible?
