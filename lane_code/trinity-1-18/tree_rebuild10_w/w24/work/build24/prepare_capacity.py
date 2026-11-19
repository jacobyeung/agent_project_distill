from pathlib import Path
L=Path(__file__).resolve().parents[2];D=L/'work/build24'
s=(L.parent/'w23/work/build23/native23.py').read_text().replace("work/build23", "work/build24").replace('from capacity23 import','from capacity24 import')
s=s.replace("prior=load(B/'inputs/config.json')", "prior=load(L/'work/build22/inputs/config.json')")
s=s.replace("cfg['recipe']=C.recipe_for(cfg)\n    streams={}", """cfg['r1_training'].update({k:prior['r1_training'][k] for k in
        ('launch22','v7_k1_removal','v7_k1_union','wording_exclusion','camera_wording_exclusion') if k in prior['r1_training']})
    cfg['r1_training']['not_present_slots']=['0','1']
    cfg['recipe']=C.recipe_for(cfg)
    streams={} """)
s=s.replace("if not (directory/'receipt.json').exists():\n            if (directory/'rows.sqlite').exists():(directory/'rows.sqlite').write_bytes(b'')", "if not (directory/'receipt.json').exists() or not (directory/'rows.sqlite').exists():\n            if (directory/'rows.sqlite').exists():raise ValueError('Incomplete fixture store requires retained-state review')")
s=s.replace("cfg['r1_training'].pop('routing_inputs')", """cfg['r1_training'].pop('routing_inputs')
    cfg['r1_training']['row_sources']=write(O/'row_sources.json',{})
    cfg['r1_training'].pop('source_membership',None)""")
s=s.replace("from student_pilot.r1_rooms import census\n    audit,_=census(cfg)", """from student_pilot.r1_rooms import census
    from fixture_twins import bind
    bind(cfg,O)
    audit,_=census(cfg)""")
s=s.replace("root/'checkpoint'", "root/'checkpoint_000600'")
s=s.replace("for step in (400,600):", "for step in (600,400):")
s=s.replace("sources['units']['source']=", "sources['units']={}\n    sources['units']['source']=")
s=s.replace("guard('host')\n            with patch.dict", """staged={p.name:str(p) for folder in ('build21','build22') for p in (L/'work'/folder/'upload/u').glob('*') if p.is_file()}
            stack.enter_context(P.scope(staged))
            guard('host')
            with patch.dict""")
s=s.replace("from capacity24 import guard, population, pose_manifests", "from capacity24 import guard, population, pose_manifests")
(D/'native24.py').write_text(s)
s=(L.parent/'w23/work/build23/capacity23.py').read_text().replace('work/build23','work/build24').replace('current>2_900_000_000','current>5_700_000_000')
s=s.replace("value=dict(row,qid=stream+str(i));f.write", "value=dict(row,qid=stream+str(i));f.write")
# Append named removal controls to synthetic VQA input. The native producer must drop them.
s=s.replace("print('source',stream,count,path.stat().st_size,flush=True)", """if stream=='vqa':
        cfg=json.loads((L/'work/build22/inputs/config.json').read_text())
        rows=json.loads(Path(cfg['remove_files'][-1]['path']).read_text())['rows']
        with path.open('a') as f:
            for item in rows:f.write(json.dumps(dict(row,qid=item['qid']),separators=(',',':'))+'\\n')
    print('source',stream,count,path.stat().st_size,flush=True)""")
(D/'capacity24.py').write_text(s)
print('Capacity harness prepared with synthetic twins and all real removal-list pins.')
