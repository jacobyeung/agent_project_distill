"""Place the worker import gate between runtime and bulk staging."""
import json


def closure(audit):
    modules=set();symbols=set()
    for path in audit['reachable_via']:
        item=audit['files'][path]
        if not path.startswith('outer/') and item['module'] not in ('8','orchard_h10.entry'):
            modules.add(item['module'])
    for edge in audit['edges']:
        if edge['status'] in ('stdlib','environment','delivered','delivered_namespace'):
            modules.add(edge['name'])
            if edge['kind']=='from':
                symbols.update((edge['name'],s) for s in edge['symbols'] if s!='*')
        for child in edge.get('child_modules',[]):
            if child['status'].startswith('delivered'):modules.add(child['name'])
    modules.update(('keyword','email._encoded_words','importlib.readers','importlib.resources.readers',
                    'xml.sax.expatreader','xml.sax.xmlreader','orchard_h10.boot'))
    return dict(modules=sorted(modules),symbols=[list(v) for v in sorted(symbols)])


def patch(nf,pf,B,here):
    audit=json.loads((here/'out/IMPORT_AUDIT.json').read_text())
    manifest=closure(audit)
    pf['g/3.json']=B.jd(manifest)
    pf['orchard_h10/boot.py']=(here/'runtime/boot.py').read_bytes()
    s=pf['orchard_h10/job.py'].decode()
    s=B.once(s,"    root=Path(root); receipts={}; archives=root/'a';archives.mkdir()", "    started=time.monotonic()\n    root=Path(root); receipts={}; archives=root/'a';archives.mkdir()")
    # a4 (input 3), not a2 (input 2), supplies v/py and v/site.
    s=B.once(s,"    for i,group in enumerate(assets['groups']):", "    from orchard_h10.boot import launch, environment_archive, interpreter_archive, PYTHON_PREFIX\n    for i,group in enumerate(assets['groups']):\n        if i==0:\n            receipts['0']=interpreter_archive(group,root,S)\n            continue\n        if i!=1:continue")
    before="    for i,a in enumerate(inputs['archives']):\n        dest=archives/('a'+str(i))"
    replacement="""    for i in (3,4):
        receipts['a'+str(i)]=environment_archive(inputs['archives'][i],root,S)
    for name in ('vnice','terminator'):
        if S.sha(J.physical(root,inputs['policy'][name]))!=assets[name+'_sha256']:raise ValueError('E86')
    pre_bytes=payload['bytes']+bwrap['bytes']+sum(p[1] for g in assets['groups'][:2] for p in g)+sum(p['bytes'] for i in (3,4) for p in inputs['archives'][i]['parts'])
    launch(root,cfg,inputs,J,pre_bytes,time.monotonic()-started)
    for i,group in enumerate(assets['groups']):
        if i==1:continue
        parts=[dict(path=p,bytes=n,sha256=h) for p,n,h in group]
        dest=archives/str(i)
        receipts[str(i)]=S.copy_parts(parts,dest,lambda p:Path(p['path']).open('rb'))
        S.room(root,dest.stat().st_size)
        S.unpack(dest,root,links=True,exclude_prefix=PYTHON_PREFIX if i==0 else None)
    for i,a in enumerate(inputs['archives']):
        if i in (3,4):continue
        dest=archives/('a'+str(i))"""
    s=B.once(s,before,replacement)
    stage=pf['orchard_h10/vendor/orchard_stage.py'].decode()
    stage=B.once(stage,'frame_offsets=None):','frame_offsets=None, retain_prefix=None, exclude_prefix=None):')
    stage=B.once(stage,"            target = destination/str(path)", "            if retain_prefix is not None and str(path)!=retain_prefix and not str(path).startswith(retain_prefix+'/'):\n                continue\n            if exclude_prefix is not None and (str(path)==exclude_prefix or str(path).startswith(exclude_prefix+'/')):\n                continue\n            target = destination/str(path)")
    pf['orchard_h10/vendor/orchard_stage.py']=stage.encode()
    pf['orchard_h10/job.py']=s.encode()
    s=pf['orchard_h10/entry.py'].decode()
    s=B.once(s,"elif action==3:\n    from g.w import run\n    result=run(cfg['config'],cfg['stop_at'])", "elif action==3:\n    if cfg.get('boot'):\n        from orchard_h10.boot import check\n        check(cfg)\n        raise SystemExit(0)\n    from g.w import run\n    result=run(cfg['config'],cfg['stop_at'])")
    s=B.once(s,"else:raise ValueError('Invalid dispatch')", "elif action==4:\n    from orchard_h10.boot import worker\n    worker(cfg)\nelse:raise ValueError('Invalid dispatch')")
    pf['orchard_h10/entry.py']=s.encode()
    # Keep CPU boot failures visible in the supervisor's authenticated return.
    s=nf['a/5.py'].decode()
    s=B.once(s,"    except Exception as e:\n        print", "    except Exception as e:\n        import traceback\n        if os.environ.get('SLURM_JOB_ID','').isdigit():traceback.print_exc()\n        print")
    s=B.once(s,"write(results/'CPU.json',dict(passed=True,", "write(results/'CPU.json',dict(boot=json.loads(J.physical(root,cfg['logical']+'/r/metadata/25.json').read_text()),passed=True,")
    nf['a/5.py']=s.encode()
    return manifest
