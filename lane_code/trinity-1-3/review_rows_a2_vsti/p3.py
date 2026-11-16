import numpy as np,json,sqlite3,collections,csv,sys
db=sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_a2/vsti/out/vsti_rel_v3/rows.sqlite?mode=ro',uri=True)
rows=[json.loads(t) for (t,) in db.execute('select row from rows order by i')]
meta={r['video_id']:r for r in csv.DictReader(open('/scratch/jjyeung/orch_n30/b12_cntapp/work/auth/arkit_3dod_metadata.csv'))}
seen=set()
for r in rows:
    p=r['provenance'];key=(r['dataset'],p['raster'].split('/')[-3])
    sky=meta.get(p['canonical'].split('/')[1],{}).get('sky_direction') if r['dataset']=='d3' else None
    key=key+(sky,)
    if key in seen:continue
    seen.add(key)
    z=np.load(p['raster'])
    print('==',key,p['raster'])
    for k in z.files:
        a=z[k];print('  ',k,a.dtype,a.shape, a.ravel()[:4] if a.size<200 or k in('K',) else '')
    c=z['c2w'];print('  camy_world median',np.median(c[:,:3,1],0).round(2),'camx',np.median(c[:,:3,0],0).round(2),'camz',np.median(c[:,:3,2],0).round(2))
