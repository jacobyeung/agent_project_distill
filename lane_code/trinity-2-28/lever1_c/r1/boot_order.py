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
    # Runtime groups are the template's original environment/interpreter archives.
    # Input 2 supplies v/py and v/site; input 4 supplies the tiny policy receipt.
    before="    for i,a in enumerate(inputs['archives']):\n        dest=archives/('a'+str(i))"
    replacement="""    from orchard_h10.boot import launch, environment_archive
    for i in (2,4):
        receipts['a'+str(i)]=environment_archive(inputs['archives'][i],root,S)
    for name in ('vnice','terminator'):
        if S.sha(J.physical(root,inputs['policy'][name]))!=assets[name+'_sha256']:raise ValueError('E86')
    pre_bytes=payload['bytes']+bwrap['bytes']+sum(p[1] for g in assets['groups'] for p in g)+sum(p['bytes'] for i in (2,4) for p in inputs['archives'][i]['parts'])
    launch(root,cfg,inputs,J,pre_bytes,time.monotonic()-started)
    for i,a in enumerate(inputs['archives']):
        if i==4:continue
        dest=archives/('a'+str(i))"""
    s=B.once(s,before,replacement)
    s=B.once(s,"extract(S,stream,root/a['destination'],a['expanded_bytes'],inputs['retain_roots'],dest,index)","extract(S,stream,root/a['destination'],a['expanded_bytes'],[k for k in inputs['retain_roots'] if i!=2 or k not in ('v','q')],dest,index)")
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
