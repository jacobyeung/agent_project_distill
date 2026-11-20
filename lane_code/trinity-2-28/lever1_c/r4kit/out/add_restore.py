from pathlib import Path
p=Path('tests/test_fixes.py');s=p.read_text()
a=s.index('        def preparation(*args,**kw):');b=s.index('        processor=types.SimpleNamespace',a)
s=s[:a]+'''        # Build a tiny authenticated export; the real restore verifies every
        # hash/size and writes its normal metadata through the opaque Path view.
        base=d/'b';base.mkdir();weights=d/'m400/full_weights';weights.mkdir(parents=True)
        def put(path,value):
            path.parent.mkdir(parents=True,exist_ok=True)
            raw=B.jd(value);path.write_bytes(C.pack(raw));return dict(bytes=len(raw),sha256=B.digest(raw))
        asset_names=('config.json','tokenizer.json','tokenizer_config.json','preprocessor_config.json')
        assets={}
        for name in asset_names:
            (base/name).write_bytes(b'{}');assets[name]=B.digest(b'{}')
        original=B.jd(dict(schema='p3-model-input-v1',base_identity='a',files=assets))
        archive=d/'o/0.tgz';archive.parent.mkdir();archive.write_bytes(B.archive({'model.json':original}))
        (weights/'0.bin').write_bytes(b'0')
        index=dict(weight_map={'x':'0.bin'})
        ix=put(weights/'0.json',index)
        full=dict(schema='full-ft-export-v1',dtype='bfloat16',files=[dict(name='0.bin',bytes=1,sha256=B.digest(b'0'))],
                  index=dict(name='0.json',**ix),tensor_count=1)
        fp=put(weights/'full_weights.json',full)
        (d/'m400/heads.pt').write_bytes(b'0')
        artifact=dict(config_sha256='a'*64,base_identity='a',frame_layout='duplicate',
                      full_weights=fp,heads=dict(sha256=B.digest(b'0')))
        ap=put(d/'m400/artifact.json',artifact)
        receipt=dict(config_sha256='a'*64,frame_layout='duplicate',camera={},depth={},
                     model=dict(path='/a',sha256=B.digest(original)))
        rp=put(d/'p0/receipt.json',receipt)
        config=dict(base_identity='a',frame_layout='duplicate',preparation=dict(path='/a',sha256=rp['sha256']))
        cp=put(d/'p0/config.json',config)
        data_receipt=dict(status='PREPARED',schema='s1-in-job-data-v1',config=dict(path='/b',sha256=cp['sha256']),
                          preparation=config['preparation'],real_frames_verified=True,rehearsal=False)
        dp=put(d/'p0/data_receipt.json',data_receipt)
        pins=dict(artifact=ap,preparation={name:dict(path='p0/'+filename,source_path=source,**pin) for name,filename,source,pin in
            [('config','config.json','/b',cp),('receipt','receipt.json','/a',rp),('data_receipt','data_receipt.json','/c',dp)]})
        for name,path in [('full_weights',weights/'full_weights.json'),('artifact',d/'m400/artifact.json'),
                          ('base_config',base/'config.json'),('original_model',archive)]:
            cfg['inputs']['files'][name]['path']=str(path)
        C.store(p/'2.json',cfg)
        real_stage=stage_restore.stage
        def preparation(*args,**kw):
            kw['export_pins']=pins
            return real_stage(*args,**kw)
''' +s[b:]
s=s.replace("patch.object(trainer,'processor_for_receipt',return_value=processor),", "patch.object(stage_restore,'prove_depth',return_value=dict(passed=True)), \\\n             patch.object(trainer,'processor_for_receipt',return_value=processor),")
s=s.replace("doubles=['external weight preparation','processor construction','RGB processor']", "doubles=['tiny authenticated export inputs','head-shape proof','processor construction','RGB processor']")
s=s.replace("real=['opaque importer','runtime.run'", "real=['stage_restore.stage','opaque importer','runtime.run'")
p.write_text(s)
