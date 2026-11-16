from pathlib import Path
p=Path('tests/rehearse.py');s=p.read_text()
s=s.replace("# The source is retained so the exact fixture changes can be audited.",'''if '--done' in sys.argv:
    source=source.replace("    artifact=physical(root,config['spec']['artifact']['path'])", """    config['spec']['step']=200
    config['spec']['artifact']['path']=str(J.FSW/'ap/8865619b/runs/359fcc3c/m200/artifact.json')
    artifact=physical(root,config['spec']['artifact']['path'])""")
    source=source.replace("    base,bm,export,ap=F.models(fixture,artifact,real_base)", """    base,bm,export,ap=F.models(fixture,artifact,real_base)
    avalue=json.loads(ap.read_text());avalue['step']=200;F.js(ap,avalue)
    (export/'heads.pt').write_bytes(b'fixture')""")
    source=source.replace("'m544/'+str(p.relative_to(export))", "'m200/'+str(p.relative_to(export))")
    source=source.replace("{'m/ap/90da7ac2/m/base_manifest.json':bm.read_bytes()}", "{'m/ap/90da7ac2/m/base_manifest.json':bm.read_bytes(), **{'sj/orch_cd/legs1_reads/out/'+n:(ROOT/'reader/out'/n).read_bytes() for n in ('common.py','export_check.py')}}")
    source=source.replace("binding['export']=dict(kind='fixture',sha256=F.sha(ap)", "binding['export']=dict(kind='fixture',sha256=export_tar['sha256']")
    source=source.replace("config.update(x0=binding['binding_sha256'],x1=F.sha(ap),x2=0)", "config.update(x0=binding['binding_sha256'],x1=export_tar['sha256'],x2=1,x3=export_tar['bytes'])")
    source=source.replace("        with (fixture/'e.tar').open('rb') as stream:yield stream", """        raw=(fixture/'e.tar').read_bytes();n=len(raw)//4
        idx=int(argv[-1].split('.part')[1][:2])
        yield io.BytesIO(raw[idx*n:(idx+1)*n] if idx<3 else raw[idx*n:])""")
    source=source.replace("        if any(str(x).endswith('prove_prompts.py')", """        if '--export' in argv:
            argv=list(argv);argv[2]=str(ROOT/'reader/out/export_check.py')
            argv[argv.index('--export')+1]=str(artifact)
            with patch.object(J.subprocess,'run',original_run),patch.object(J.subprocess,'Popen',original_popen):
                return original_run(argv,**kwargs)
        if any(str(x).endswith('prove_prompts.py')""")
    source=source.replace("    with ExitStack() as stack:", """    import export_stage as E,s1
    receipts=fixture/'receipt';receipts.mkdir()
    (receipts/'gcs_359fcc3c_m200.done').write_text('q8/8865619b/359fcc3c_m200.tar '+str(export_tar['bytes'])+' '+export_tar['sha256']+'\\n')
    def local_path(value):
        return receipts if str(value)=='/project/community/jjyeung/okh7/x_f5c353f7/o' else Path(value)
    with ExitStack() as stack:
        stack.enter_context(patch.object(E,'Path',local_path))
        stack.enter_context(patch.object(gate,'Path',local_path))
        stack.enter_context(patch.object(E,'writable',lambda v:Path(v).resolve()))
        stack.enter_context(patch.object(E.T,'writable',lambda v:Path(v).resolve()))
        stack.enter_context(patch.object(s1,'MIN_FREE',0))
        stack.enter_context(patch.object(s1,'stage_videos',S.stage_videos))
""")
    source=source.replace("    B.dump(packet/'CONFIG.json',config)", "    B.dump(packet/'CONFIG.json',json.loads(B.boot_files(packet/'BATCH.sh')['bootstrap/CONFIG.json']))")
# The source is retained so the exact fixture changes can be audited.''')
s=s.replace("('rehearsal_'+key+'_source.py')", "('rehearsal_'+key+('_done' if '--done' in sys.argv else '')+'_source.py')")
s=s.replace("('coverage_'+key+'.json')", "('coverage_'+key+('_done' if '--done' in sys.argv else '')+'.json')")
p.write_text(s)
