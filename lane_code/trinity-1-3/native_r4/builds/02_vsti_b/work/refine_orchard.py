from pathlib import Path
p=Path('code/o.py');s=p.read_text();start=s.index('        # The inherited stage mounts');end=s.index("        result=load(runroot/'RESULT.json')",start)
s=s[:start]+'''        # Proof sees the original inputs; the read sees only its frames, heads and tower.
        proof_ns=S.namespace(root,original)
        proof_ns+=['--bind',str(runroot),'/r','--ro-bind',str(root/'c'),'/x','--ro-bind',str(root/'d'),'/d',
                   '--bind',str(root/'shm'),'/dev/shm']
        from venue import namespace,FSW,AP
        bindings=[(root/'fsw',FSW,False),(root/'m/ap',AP,False),
                  (S.physical(root,original['assets']['tree_root']),original['assets']['tree_root'],False),
                  (root,root,False),(root/'c','/x',False),(root/'a','/a',False),
                  (root/'b','/b',False),(root/'d','/d',False)]
        # Authenticated runtime overlays use physical paths under the job-local root.
        read_ns=namespace(root,bindings,gpu=0)
        tail=[runtime['python']['path'],'-I','-s','-B',worker['bootstrap'],'--spec',worker['runtime'],'--']
        env=J.environment(root);env.pop('PYTHONPATH',None);env['PYTHONDONTWRITEBYTECODE']='1'
        budget=Budget(config['deadline_utc']);gpu_started=time.monotonic()
        phases=[(read_ns, '/x/a.py',['--config',str(root/'w.json'),'--deadline-utc',config['deadline_utc'],'--phase','prepare'])]
        if not resume:
            phases.append((proof_ns,'/x/p.py',['--reference','/d/a.json','--request','/d/native/paired/request.json',
                                            '--spec','/d/s.json','--out','/r/p']))
        phases.append((read_ns,'/x/a.py',['--config',str(root/'w.json'),'--deadline-utc',config['deadline_utc'],'--phase','read']))
        with (root/'b.log').open('w') as stream:
            for prefix,entry,args in phases:
                remaining=min(budget.remaining(),21600-(time.monotonic()-gpu_started))
                if remaining<=0:raise TimeoutError('deadline before next phase')
                result=subprocess.run(prefix+tail+[entry]+args,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=remaining)
                rc=result.returncode
                if rc:raise RuntimeError('worker failed; see b.log')
''' + s[end:]
# Do not expose proof payload or raw caches through the read's /d mount; it gets an explicit four-file input directory.
s=s.replace("        dump(root/'d/s.json',spec)","        dump(root/'d/s.json',spec)\n        (root/'e').mkdir()\n        for n in ('c.json','d.json','e.json','s.json'):(root/'e'/n).write_bytes((root/'d'/n).read_bytes())")
s=s.replace("(root/'b','/b',False),(root/'d','/d',False)","(root/'b','/b',False),(root/'e','/d',False)")
p.write_text(s)
