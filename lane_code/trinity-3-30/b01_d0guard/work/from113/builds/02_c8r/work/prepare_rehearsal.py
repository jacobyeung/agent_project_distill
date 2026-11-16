from pathlib import Path
B=Path(__file__).resolve().parents[1];old=B.parent/'01_c8'
p=B/'out/rehearsal/run_rehearsal.py';t=(old/'out/rehearsal/run_rehearsal.py').read_text()
t=t.replace("PY=Path('/scratch/jjyeung/envs/vllm/bin/python')","PY=Path(sys.executable)")
t=t.replace('out/c8/','out/c8r/').replace('FAMILY_C8.json','FAMILY_C8R.json').replace('code_c8.tar','code_c8r.tar')
t=t.replace('9000000000','4000000000').replace('torch.set_num_threads(8)','torch.set_num_threads(1)\n    torch.set_num_interop_threads(1)')
t=t.replace("'--ro-bind',str(W),str(W),'--bind',str(B),str(B),",
    "'--ro-bind',str(B.parents[1]),str(B.parents[1]),'--ro-bind',str(W),str(W),'--bind',str(B),str(B),")
t=t.replace("str(W/'tree/student_pilot')", "str(W/'tree')")
a=t.index('def stage(dest):');z=t.index('\ndef namespace',a)
t=t[:a]+'''def stage(dest):
    family=load(FAMILY)
    prior=load(B.parent/'01_c8/out/c8/FAMILY_C8.json')
    oldcode=next(p for p in prior['assets']['small_objects'] if p['role']=='code')
    shared=B.parent/'01_c8/work/rehearsal_assets'/oldcode['sha256'][:16]
    if load(shared/'STAGED.json')['code_sha256']!=oldcode['sha256']:
        raise ValueError('Shared staging identity differs')
    for part in family['assets']['small_objects']:
        if part['role']!='code' and part!=next(x for x in prior['assets']['small_objects'] if x['role']==part['role']):
            raise ValueError('Shared input descriptor differs')
    if family['assets']['frames_inventory']!=prior['assets']['frames_inventory']:
        raise ValueError('Shared frame inventory differs')
    code=next(p for p in family['assets']['small_objects'] if p['role']=='code')
    path=B/'out/c8r/code_c8r.tar'
    if path.stat().st_size!=code['bytes'] or sha(path)!=code['sha256']:
        raise ValueError('New code object differs')
    root=B/'work/rehearsal_assets'/code['sha256'][:16]
    if not root.exists():
        root.mkdir(parents=True)
        extract(path,root,4000000000-owned_bytes(B))
        physical(root,LOGICAL/'runs').mkdir(parents=True,exist_ok=True)
    dump(dest/'STAGING.json',dict(shared=str(shared),code=str(root),shared_read_only=True))
    return shared
''' + t[z:]
t=t.replace('''    if not trainer.is_file():
        trainer.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(W/'obj'/Path(family['assets']['trainer_logical_archive']).name,trainer)
''','''    if not trainer.is_file():raise ValueError('Shared trainer is unavailable')
''')
t=t.replace('''    for inner in (W,B,PY.parent.parent,Path(family['assets']['tree_root'])):
        physical(root,inner).mkdir(parents=True,exist_ok=True)
''','')
t=t.replace("    mapped_runs=physical(root,run.parent);mapped_runs.mkdir(parents=True,exist_ok=True)",
    "    code=Path(load(dest/'STAGING.json')['code'])\n    mapped_runs=physical(code,run.parent)")
t=t.replace("    args+=['--bind',str(local_runs),str(mapped_runs),'--bind',str(local_runs),str(run.parent)]",
    "    code_part=next(p for p in family['assets']['small_objects'] if p['role']=='code')\n    for member in sorted(code_part['members']):\n        if not member.startswith('sj/'):raise ValueError('Unexpected code member root')\n        logical=Path('/scratch/jjyeung')/member[3:]\n        args+=['--ro-bind',str(code/member),str(logical)]\n    args+=['--bind',str(local_runs),str(run.parent)]")
t=t.replace("'--setenv','HF_HOME',str(root/'cache'),'--setenv','XDG_CACHE_HOME',str(root/'cache'),",
    "'--setenv','HF_HOME',str(dest/'cache'),'--setenv','XDG_CACHE_HOME',str(dest/'cache'),\n        '--setenv','TMPDIR',str(dest/'cache'),")
t=t.replace("    local_runs=dest/'runs';local_run=local_runs/token;local_run.mkdir(parents=True)",
    "    local_runs=dest/'runs';local_run=local_runs/token;local_run.mkdir(parents=True)\n    (dest/'cache').mkdir()")
t=t.replace("cov=coverage.Coverage(branch=True,data_file=str(covdir/'.coverage'),",
    "cov=coverage.Coverage(branch=True,data_file=str(covdir/'.coverage'),data_suffix=True,")
t=t.replace("        returned=results.publish(source,results.AUTHORIZED_POOL,cfg['token'],cfg['plan_sha256'],0)",
    "        results.write_test(results.AUTHORIZED_POOL,cfg['token'])\n        install_cloud_fixture(dest)\n        returned=results.publish(source,results.AUTHORIZED_POOL,cfg['token'],cfg['plan_sha256'],0,\n                                 mode=args.mode,cloud_config=cfg['assets']['gcloud_config'])")
t=t.replace("        cov.stop();cov.save()\n        cov.json_report(outfile=str(covdir/'coverage.json'))",
    "        cov.stop();cov.save()\n        combined=coverage.Coverage(branch=True,data_file=str(covdir/'.coverage'))\n        combined.combine(keep=True);combined.save()\n        combined.json_report(outfile=str(covdir/'coverage.json'))\n        outcome['coverage_combine']='coverage combine API, keep=True; one serving process'")
t=t.replace("    args=p.parse_args()","    p.add_argument('--shards',type=int,default=1)\n    args=p.parse_args()\n    if args.shards!=1:\n        p.error('Production run/merge has no shard protocol; use --shards 1. See out/SHARDING.md.')")
t=t.replace("    root=stage(dest)","    probe=subprocess.run(['/usr/bin/bwrap','--ro-bind','/','/','--unshare-net','/bin/true'],capture_output=True,text=True)\n    if probe.returncode:\n        dump(dest/'RESULT.json',dict(status='BLOCKED',fixture=True,whole_worker_complete=False,\n             reason='Namespace unavailable; no staging attempted',returncode=probe.returncode,stderr=probe.stderr))\n        return 2\n    root=stage(dest)")
t=t.replace("    absent=prerequisites()","    absent=prerequisites()")
z=t.index('def inside(args):')
t=t[:z]+'''def install_cloud_fixture(dest):
    bindir=dest/'bin';bindir.mkdir()
    cli=bindir/'gcloud'
    cli.write_text('#!/bin/sh\\nexec '+str(PY)+' -I -s -B '+str(B/'out/tests/fake_gcloud.py')+' "$@"\\n')
    cli.chmod(0o755)
    os.environ['PATH']=str(bindir)+':'+os.environ['PATH']
    os.environ['C8R_CLOUD_STORE']=str(dest/'cloud')

''' +t[z:]
p.write_text(t)
p=B/'out/rehearsal/cpu_boundary.py';t=(old/'out/rehearsal/cpu_boundary.py').read_text()
t=t.replace('out/c8/','out/c8r/').replace('FAMILY_C8.json','FAMILY_C8R.json')
t=t.replace("if N.load(rebound)!=N.load(family['worker_contract']['mask_cache']['path']):",
            "if rebound.read_bytes()!=Path(family['worker_contract']['mask_cache']['path']).read_bytes():")
t=t.replace('shipped draft receipt','shipped receipt').replace('The harness is unexecuted until the specified runtime and streamed inputs exist.',
    'The result record distinguishes completed runs from blocked namespace attempts.')
p.write_text(t)
