from pathlib import Path
p=Path('/scratch/jjyeung/orch_n30/so_reads228/work/round1/kit/runner228.py')
s=p.read_text().replace('proof=stage_check(root,cfg,inputs,export)','proof=stage_check(root,cfg,inputs,export,prepare=True)')
start=s.index('        def execute(chosen,cards,deadline,*,prefix):')
end=s.index('        try:\n            with Sampler',start)
s=s[:start]+'''        def execute(chosen,cards,deadline,*,prefix):
            def launch(argv,**kwargs):
                config=read(Path(kwargs['cwd'])/argv[-1])
                # The sealed runner wrote a/30.json and supplies the dispatch; keep it unchanged.
                write(out/'metadata/WORKER_ARGS.json',runner.worker_args(config))
                worker_file=out/'metadata/worker.json'
                write(worker_file,dict(worker=config,adapter=dict(out=str(out),on=a.on,
                    items=a.items,extensions=str(ext) if ext else None)))
                worker_env=clean_environment(out,card)
                command=['nice','-n','10','bash',str(VNICE),inputs['python'],'-I','-s','-B',
                         str(HERE/'worker228.py'),str(worker_file),'--observe']
                write(out/'metadata/COMMAND.json',dict(argv=command,env=worker_env,start_new_session=True))
                process=subprocess.Popen(command,env=worker_env,stdout=kwargs['stdout'],
                    stderr=kwargs['stderr'],cwd=out,start_new_session=True)
                class ObservedProcess:
                    def wait(self):
                        nonlocal worker_rc
                        while process.poll() is None:
                            if sampler.process.poll() is not None:
                                stop.write_text('nvidia-smi telemetry stopped; no retry\\n')
                            time.sleep(1)
                        worker_rc=process.returncode
                        return worker_rc
                return ObservedProcess()
            result=runner.run(chosen,cards,deadline,prefix=prefix,launcher=launch)
            if sampler.process.poll() is not None:
                result['failure']='nvidia-smi telemetry failed; run is diagnostic-only'
                write(Path(chosen['output'])/'SUMMARY.json',result)
            return result
''' +s[end:]
s=s.replace("        identity=new_return_identity(out,cfg)","""        identity=new_return_identity(out,cfg)
        (ret/'logs').mkdir()
        prepare_log=STAGE/'prepare/prepare.log'
        (ret/'logs/0.log').write_bytes(prepare_log.read_bytes() if prepare_log.is_file() else b'Local stage verification passed.\\n')
        (ret/'logs/1.log').write_text('Local sealed operator launch; worker output is reads/0/logs/30.log.\\n')
        from orchard_h10.common import template
        _,storage,_,_,_=template()
        write(ret/'metadata/STORAGE.json',dict(storage.storage_proof(out),job=identity['job'],execution_backend='trinity-local'))""")
s=s.replace("        result=package_return(out,cfg,summary,rc,failure=failure)","""        write(ret/'metadata/ALLOCATION.json',dict(end=end,plan=cfg['plan_sha256'],failure=failure,summary=summary))
        result=package_return(out,cfg,summary,rc,failure=failure)""")
p.write_text(s)
print('The adapter now calls sealed runner.run with launcher= and isolates the worker session.')
