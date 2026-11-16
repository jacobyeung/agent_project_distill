"""Exercise render_full's exact legacy-direction and annotation-provider branches."""
from pathlib import Path
path=Path(__file__).resolve().parent/'render_arms.py'
exec(compile(path.read_text().split('families=list',1)[0],str(path),'exec'))

for typ in ('object_rel_direction_easy','object_rel_direction_medium','object_rel_direction_hard','absolute_direction_object'):
    for kind in ('landscape','nadir_positive'):
        for i in range(3):
            def direction(typ=typ,kind=kind,i=i):
                item=json.loads((W/'items.json').read_text())[f'{typ}/{kind}/{i}']
                clip=clip_for(kind,i)
                # This is the session selected by render_gaps_v314.prepare and
                # render_full.render_scan, before their native dispatcher call.
                session=gaps.session(backend,clip,typ)
                return P.render(item,session,lambda s:len(s.split()))
            capture('production_direction/'+typ,f'{kind}/{i}','render_gaps_v314.session -> derivgen.programs_v314.render',direction)

specs={} if args.arm=='base' else json.loads((W/'annotation_items.json').read_text())
for typ in ('object_abs_distance','object_rel_distance'):
    for kind in ('landscape','nadir_positive'):
        for i in range(3):
            key=f'{typ}/{kind}/{i}'
            def annotation(typ=typ,kind=kind,i=i,key=key):
                clip=clip_for(kind,i);geo=clip.geo
                geo.origin=np.zeros(3);geo.basis=np.eye(3)
                geo.obb={iid:dict(centroid=c,axesLengths=[.6,.4,.5],normalizedAxes=np.eye(3)) for iid,c in [(1,[-.8,2.,.1]),(2,[.9,2.7,.1]),(3,[0.,4.5,.1])]}
                def fresh():return D.make_session(backend,clip,[],B.AnnotationBoxProvider(),multi_instance=True)
                if args.arm=='base':
                    item=dict(qid='annotation/'+key,type=typ,question='Compare the chair, table and plant.',options=['A. table','B. plant'] if typ=='object_rel_distance' else [],roles=dict(target='chair',cands=['table','plant']) if typ=='object_rel_distance' else dict(a='chair',b='table'),gt_authority='synthetic native OBB authority')
                    D.prepare(item,clip,rule=B.RULE_GRID,multi_instance=True)
                    s=fresh();names=['chair','table','plant'] if typ=='object_rel_distance' else ['chair','table']
                    for n in names:s.execute(f'<ground obj="{n}" mode="box">')
                    s.execute('<gap a="chair"'+''.join(f' b="{n}"' for n in names[1:])+' rule="box_grid_5cm">')
                    values=B.replay_audit(s.events);item['gt_answer']=chr(65+int(np.argmin(values))) if typ=='object_rel_distance' else B.number(values[0],2)
                    specs[key]=clean(item)
                item=copy.deepcopy(specs[key]);D.prepare(item,clip,rule=B.RULE_GRID,multi_instance=True)
                return B.render(item,fresh(),lambda s:len(s.split()))
            capture('production_annotation/'+typ,f'{kind}/{i}','render_full.B.render + ground_v313_distance.prepare/make_session + AnnotationBoxProvider',annotation)
if args.arm=='base':(W/'annotation_items.json').write_text(json.dumps(specs,indent=2))

sys.path.insert(0,str(tree/'tests/headcall'))
for mode in ('HX','HA'):
    for i in range(3):
        def twin(mode=mode,i=i):
            from headcall.rows import prepare_row,twin_queries
            from rows_fixture import distance_row
            row=distance_row(qid=f'twin/{mode}/{i}')
            entry=dict(kind='queries',queries=twin_queries(row['head_calls']))
            pd=dict(uv=[[[0.,0.] for _ in range(8)] for _ in range(16)],depth=[[0.]*8 for _ in range(16)],mask=[[False]*8 for _ in range(16)])
            target=row['target'] if mode=='HX' else '\n</think>\n\n'+row['answer']
            return prepare_row(dict(qid=row['qid'],target=target,_headcall=entry,_camera=dict(point_depth=pd)))
        capture('headcall/queries_'+mode,f'fixture/{i}','headcall.rows.prepare_row',twin)

Path(args.output).write_text(json.dumps(dict(arm=args.arm,tree=str(tree),fixture_source=__file__,results=results),indent=2,allow_nan=False))
print(json.dumps(dict(arm=args.arm,rendered=sum(r['status']=='rendered' for r in results),refused=[(r['family'],r['variant'],r.get('error')) for r in results if r['status']!='rendered'])))
