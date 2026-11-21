import sys, json, os, glob, collections, sqlite3, ast, csv, re
W=sys.argv[1]; T=W+'/t'; L=W+'/lists'
sys.dont_write_bytecode=True; sys.path.insert(0,T)
from student_pilot.p3_provenance import load, pinned, sha256
from student_pilot import r1_persisted
cfgp=json.load(open(W+'/cfgpart.json'))
paths={os.path.basename(p):p for p in glob.glob(L+'/*')}
empty=W+'/empty_e3b0'; open(empty,'w').close(); paths['e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855']=empty
B18='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w18/work/build18/inputs/'
for p in glob.glob(B18+'*.json'): paths.setdefault(os.path.basename(p)[:-5],p)
out=json.load(open(W+'/out601.json')); nei=[o for o in out if o['cls']=='NEITHER']
ROWS='/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'
c=sqlite3.connect('file:'+ROWS+'?mode=ro',uri=True)
rows=[json.loads(c.execute('SELECT row FROM rows WHERE i=?',(o['i'],)).fetchone()[0]) for o in nei]
print('rows',len(rows))
P=lambda s:{'path':'u/'+s,'sha256':s}
res=collections.defaultdict(collections.Counter)
with r1_persisted.scope(paths):
    from student_pilot.s1_exclusions import Exclusions
    ex=Exclusions(P('a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5'),P('3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970'))
    for r in rows:
        m=ex.matches(r); res['dev+benchmark scene filter (s1_exclusions.Exclusions)'][json.dumps({k:bool(v) for k,v in m.items()})]+=1
    try:
        from student_pilot import carrier_c1_routing as routing
        from student_pilot.carrier_c1_run import excluded_row
        lists=dict(exclusions='dafa4a9c8ffd1e063e0a98c5ae6087d911b74f864932e530f24d45b816cca6fb',pose_exclusions='600ef69de0674fb15c8972f3b64f0bd19e682a5a1ca19ab01e8d41279d064295',report_exclusions='99e6eed6186602832a1ca15176c4d21ab67ba24e87a15dd0cad02cac6ee13688')
        sets={k:routing.load_exclusions(P(v)) for k,v in lists.items()}
        bench=routing.load_exclusions(P('3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970'))
        print('list sizes',{k:len(v) for k,v in sets.items()},'bench',len(bench))
        for r in rows:
            hit,rep=excluded_row(r, sets['exclusions'], sets['report_exclusions'], 'vqa'); res['excluded_row(exclusions, report_exclusions) incl R0 reserve'][str((hit,rep))]+=1
            hit2,_=excluded_row(r, sets['exclusions']|sets['pose_exclusions'], set(), 'vqa'); res['excluded_row(exclusions|pose_exclusions)'][str(hit2)]+=1
            hit3,_=excluded_row(r, bench, set(), 'vqa'); res['excluded_row(benchmark_scene_exclusions)'][str(hit3)]+=1
    except Exception as e: print('excluded_row ERR',repr(e)[:400])
    q=load(pinned(P('66c427e2262331be2e0c598f2ecc39087f3a722a5155caaf1ab84a89c8cd0f6f')))
    vq=set(q.get('vqa',[])); res['exclude_qids[vqa]'][str(sum(r['qid'] in vq for r in rows))]+=1
    from student_pilot.row_removals import Removals
    rem=Removals(cfgp['remove_files'])
    for r in rows: res['remove_files match (file index list)'][str([cfgp['remove_files'][i]['sha256'][:8] for i in rem.match(r)])]+=1
    # K1 / R0 rooms with the tree's room authority
    try:
        from student_pilot.r1_rooms import Rooms, AUTHORITY
        ra=load(pinned(cfgp['ra'])); pins=ra['authority']
        pins={k:{'path':paths.get(v['sha256'],v['path']),'sha256':v['sha256']} for k,v in pins.items()}
        rooms=Rooms(pins)
        st=collections.Counter(); venues={}
        for r in rows:
            s,can,how=rooms.status(r); st[(s,how)]+=1; venues[r['dataset']+'/'+r['scene']]=(can,rooms.room(can) if can else None)
        res['r1_rooms.Rooms.status (K1 held-out / R0)'].update({str(k):v for k,v in st.items()})
        b=json.load(open(paths['3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970']))
        pg=set(b['physical_groups']); bs=set(b['scenes']); bt=set(b['rung1_tokens'])
        for s,(can,room) in sorted(venues.items()):
            print('SCENEROOM',s,can,room,'bench_group',room in pg,'bench_scene',can in bs or s in bs,'bench_token',s in bt or s.split('/')[1] in bt,'k1',room in rooms.k1,'r0',room in rooms.r0)
    except Exception as e: print('Rooms ERR',repr(e)[:400])
    # K1 lists by canonical
    for s in ('1c7c930d1a533a3b18b08486bc2c2a9b49086b0809492963498b369ac8be45a2','43853165f921d077eab92baaf83f29a69cd4f3efef789249bb8db99893853cf6','d2fd6208d7df49ab872b9536a1748d80c392f91a59135b099bc0bc38fff13a8f','6add0ad53515e14e6adb1e192ed002ec0ddd22b6c6bd112ccb756d1f8be48d8c','d21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1'):
        can={json.loads(l).get('canonical') for l in open(paths[s]) if l.strip()}; room={json.loads(l).get('room') for l in open(paths[s]) if l.strip()}
        mine={r['provenance']['canonical'] for r in rows}
        res['K1 list canonical overlap '+s[:8]][str(len(mine&can))]+=1
# whole-store sanity of removals (all 204,413 rows)
rem2=Removals(cfgp['remove_files']) if False else None
for k,v in res.items(): print('CHECK',k,dict(v))
print('DONE')
