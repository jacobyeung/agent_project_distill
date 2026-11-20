"""Derive a pinned geometry-only job from the authenticated T1 delivery."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
import sys
from pathlib import Path
import collections
import gzip
import hashlib
import importlib
import json
import tarfile
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
BASE=Path('/scratch/jjyeung/orch_n30/cont_ops24_c')
GB=BASE/'gbuild'
sys.path.insert(0,str(GB/'gpkg'))
B=importlib.import_module('build')
T1_SHA='fe9f10b875283b02e3c376b69c3601a4086312ac56ba77fbebedce4eb21e51b7'
PARENT_SHA='ef9575f1eb53d4b603592d6cd94e0bdd07e0a83e69c720c97b4191dadbe4542e'


def reference():
    path=BASE/'cap/t1.gz'
    with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==T1_SHA
    first={};prim={};rep=[];timings=[]
    with gzip.open(path,'rt') as f:
        for line in f:
            r=json.loads(line)
            if r['pass_index']==0:
                if r['geometry']:
                    first.setdefault(r['capture'],r['item_id'])
                    prim[r['item_id']]={k:r[k] for k in ('capture','geometry')}
                timings.append({k:r[k] for k in ('item_id','seconds','timings')})
            else:rep.append(r)
    fields=('scale','camera_to_world_metric','camera_to_world_unscaled','K','canvas_to_source')
    differences=[dict(item_id=r['item_id'],**{k:float(np.max(np.abs(np.asarray(r['geometry'][k])-np.asarray(prim[r['item_id']]['geometry'][k])))) for k in fields}) for r in rep]
    assert len(first)==60 and len(rep)==10
    bounds={k:2*max(r[k] for r in differences) for k in fields}
    p=json.loads((BASE/'cap/t1ret/PARITY.json').read_text());assert p['trusted'] is True
    result=dict(schema=1,capture_sha256=T1_SHA,representatives=list(first.values()),geometry=prim,
                bounds=bounds,repeat_deviations=differences,gap_atol_m=p['gap_atol_m'])
    selected=[r for r in timings if r['item_id'] in first.values()]
    replay_s=sum(r['seconds'] for r in selected)
    forecast=dict(t1_first_per_capture_replay_s=replay_s,t1_first_per_capture_tower_s=sum(r['timings'].get('g3t_s',0) for r in selected),
        captures=60,t1_replay_minutes=replay_s/60,
        worker_forecast_minutes=(replay_s+360+60)/60,allocation_planning_minutes=(replay_s+360+60+600+240)/60,
        shared_load_allowance_s=360,indexed_staging_monitor_allowance_s=60,
        worker_cap_s=1800,allocation_s=3000,worker_margin_s=1800-replay_s-420,
        allocation_margin_s=3000-replay_s-420-600-240,
        staging_allowance_s=600,publication_allowance_s=240,allowances_measured=False,
        worker_cap_reason='Forecast 1425.01s leaves 374.99s within 1800s; with 600s staging and 240s publication a capped worker fits in 2640s, leaving 360s of the allocation. No evidence requires 35 minutes.',
        deadline_offsets_s=dict(worker_latest_stop=3000-270,staging_stop=3000-240,capture_publication_stop=3000-90,normal_publication_stop=3000-10,failure_receipt_stop=3000-2),
        float16_depth_bytes=60*32*51*51*2,lossless_depth_plane_bytes=60*32*51*51*10,
        compressed_return_forecast_bytes=40_000_000,compressed_return_conservative_bytes=80_000_000,return_cap_bytes=1_000_000_000,
        caveat='T1 replay is 16.75 min, including SAM/linking. Add 6 min shared loading and 1 min indexed RGB/telemetry inside worker, plus 10 min shared archive staging and 4 min publication. All allowances are unmeasured; no first-output or GPU wall-time guarantee.')
    return result,forecast


def build(out=HERE/'out',scripts=HERE/'orchard'):
    raw=(GB/'out2/t1/delivery.tgz').read_bytes();assert B.sha(raw)==PARENT_SHA
    nf={m.name:d for m,d in B.read_tar(raw)};original=dict(nf)
    entries=B.read_tar(nf['0.tgz']);pf={m.name:d for m,d in entries};before=dict(pf)
    pub=json.loads(nf['0.json']);plan=json.loads(pf['9.json']);oldtoken=plan['token']
    assert oldtoken=='a52c1dcfae7bb'
    token='a6f198d3c7b20'
    ref,forecast=reference()
    pf['g/t.py']=(HERE/'runtime/t.py').read_bytes();pf['g/w.py']=(HERE/'runtime/w.py').read_bytes()
    pf['g/d.py']=(HERE/'depth_format.py').read_bytes();pf['g/8.json']=B.jd(ref)
    pf['g/d.py']=pf['g/d.py'].replace(b"        trial=self.codec.copy()",b"        import j\n        data=j.pack(data)\n        trial=self.codec.copy()")
    nf['a/5.py']=nf['a/5.py'].replace(b"with (results/'0.log').open('wb') as log:", b"with open('/dev/null','wb') as log:").replace(b"with (results/'1.log').open('wb') as log:", b"with open('/dev/null','wb') as log:")
    nf['a/5.py']=B.once(nf['a/5.py'], b"if __name__=='__main__':main()", b"if __name__=='__main__':\n    try:main()\n    except Exception as e:\n        print('E40:'+type(e).__name__.encode().hex())\n        raise SystemExit(1)")
    nf['3.py']=B.once(nf['3.py'], b"    exec(compile(t.extractfile('8.py').read(),__file__,'exec'))", b"    try:exec(compile(t.extractfile('8.py').read(),__file__,'exec'))\n    except Exception as e:\n        print('E41:'+type(e).__name__.encode().hex())\n        raise SystemExit(1)")
    pf['orchard_h10/vendor/orchard_results.py']=pf['orchard_h10/vendor/orchard_results.py'].replace(b'str(error)',b"'E38:'+type(error).__name__.encode().hex()")
    pf['orchard_h10/budget.py']=(HERE/'runtime/budget.py').read_bytes()
    pf['orchard_h10/e.py']=(HERE/'runtime/e.py').read_bytes()
    pf['orchard_h10/s.py']=(HERE/'runtime/s.py').read_bytes()
    pf['g/m.py']=(HERE/'runtime/m.py').read_bytes()
    # Keep serving sources and assets byte-identical. Only the capture worker,
    # resource signal, operator deadline and publication cap change.
    common=pf['orchard_h10/common.py'].decode()
    common=B.once(common,"'--time='+walltime, '--signal=B:USR1@1800'","'--exclude=orchard-community-4', '--time='+walltime, '--signal=B:USR1@120'")
    common=B.once(common,'not 2400 <= limit','not 3000 <= limit')
    common=B.once(common,'at least 40 minutes','at least 50 minutes')
    pf['orchard_h10/common.py']=common.encode()
    job=pf['orchard_h10/job.py'].decode().replace('1_900_000_000','1_000_000_000')
    job=job.replace("with (out/'logs/0.log').open('wb') as log:","with open('/dev/null','wb') as log:").replace("with (out/'logs/1.log').open('wb') as log:","with open('/dev/null','wb') as log:")
    job=job.replace("failed=str(error);","failed='E98:'+type(error).__name__.encode().hex();")
    job=job.replace("    except Exception as error:\n        failed=", "    except Exception as error:\n        from orchard_h10.e import exception\n        exception(out/'metadata/9.json',error)\n        failed=")
    job=job.replace("    failed=None;summary=None;pool_ready=False", "    from orchard_h10.e import capture\n    failed=None;summary=None;pool_ready=False")
    job=job.replace("with open('/dev/null','wb') as log:", "with capture(out/'metadata/11.json') as log:",1)
    job=job.replace("with open('/dev/null','wb') as log:", "with capture(out/'metadata/12.json') as log:")
    job=job.replace("result['error'] = type(error).__name__+': '+str(error)", "result['error'] = 'E36:'+type(error).__name__.encode().hex()")
    job=job.replace("    failed=None;summary=None;pool_ready=False", "    from orchard_h10.budget import window, finish, WORK_RESERVE\n    scope=window(end-WORK_RESERVE,R)\n    failed=None;summary=None;pool_ready=False")
    job=job.replace("        write(out/'metadata/STORAGE.json'", "        scope.__enter__()\n        write(out/'metadata/STORAGE.json'")
    job=job.replace("    finally:\n        if summary", "    finally:\n        scope.__exit__(None,None,None)\n        if summary")
    start=job.index('        try:\n            upload_capture(')
    stop=job.index('        # The template marks',start)
    job=job[:start]+"        if pool_ready:\n            finish(root,cfg,out,return_token,R,end,upload_capture,write,failed)\n"+job[stop:]
    pf['orchard_h10/job.py']=job.encode()
    op=nf['a/6.py'].decode()
    op=B.once(op,"stop_at = end-max(config.get('stop_margin',1800), 5100)","stop_at = min(end-270, clock()+1800)")
    op=op.replace("    # Reserve two 1800 s transfers, a 60 s describe, and the parent's normal return margin.","    # Allow 30 seconds to reap, then 240 seconds for bounded publication.")
    op=op.replace('timeout=max(1, stop_at-clock()+180)','timeout=max(.001, stop_at-clock())')
    op=op.replace('process.wait(timeout=30)','process.wait(timeout=max(.001,min(20,end-245-clock())))')
    op=op.replace('process.wait()','process.wait(timeout=max(.001,min(5,end-240-clock())))')
    op=op.replace("failure = type(error).__name__+': '+str(error)","failure = 'E37:'+type(error).__name__.encode().hex()")
    op=op.replace("    from orchard_h10.runner import environment", "    from orchard_h10.e import capture, exception\n    from orchard_h10.runner import environment")
    op=op.replace("    except Exception as error:\n        failure", "    except Exception as error:\n        exception(out/'metadata/10.json',error)\n        failure")
    op=op.replace('def prepare(config):', '''def prepare(config):
    global Path
    import sys
    sys.path.insert(0,str(Path(config['package'])))
    import l
    Path=l.install(config['package']).Path''')
    # All worker stdout/stderr (including third-party warnings) stays off public logs.
    op=B.once(op,"with (out/'logs/3.log').open('ab') as log:","with capture(out/'metadata/8.json') as log:")
    op=B.once(op,"    # Exercise the actual tower socket and selector with CPU weight doubles.","    from g.d import decode, encode\n    import numpy as np\n    from types import SimpleNamespace\n    synthetic=SimpleNamespace(depth_grid=np.ones((32,51,51)),grid_uv=np.linspace(0,1000,51))\n    assert np.array_equal(decode(encode(synthetic,{}))[0],synthetic.depth_grid)\n    # Exercise the actual tower socket and selector with CPU weight doubles.")
    op=B.once(op,"    from g.d import decode, encode", "    from student_pilot.g3t_online import VENDOR, vendor_digest\n    from student_pilot.tower_read import SOURCE_SHA256\n    from student_pilot.c1r_ref import source_import\n    if vendor_digest()!=SOURCE_SHA256:raise ValueError('E53')\n    source_import(VENDOR)\n    from g.d import decode, encode")
    nf['a/6.py']=op.encode()
    # 50 minutes accommodates staging. The worker itself has a 30-minute cap.
    for n in ('3.py','SUBMIT.cmd'):
        nf[n]=nf[n].replace(b'05:00:00',b'00:50:00')
    entry=pf['orchard_h10/entry.py'].decode()
    entry=entry.replace('from orchard_h10.common import install_process_guard', 'import l\nPath=l.install(p).Path\nfrom orchard_h10.common import install_process_guard')
    pf['orchard_h10/entry.py']=entry.encode()
    runner=pf['orchard_h10/runner.py']
    # Copy stored JSON bytes through ordinary file handles: the resource Path
    # deliberately decodes JSON for consumers and must not service this copy.
    runner=B.once(runner,b'    raw=source.read_bytes()',
                  b"    with open(source,'rb') as stream:raw=stream.read()")
    runner=B.once(runner,b"            if dest.read_bytes()!=raw:raise ValueError('Item input changed')",
                  b"            with open(dest,'rb') as stream:stored=stream.read()\n            if stored!=raw:raise ValueError('Item input changed')")
    # The job copies this executable into its result tree; keep its source in
    # opaque storage too, while preserving the exact dispatch program.
    runner=B.once(runner,b"        (root/'5.py').write_bytes((Path(__file__).parent/'entry.py').read_bytes())",
                  b"        code=(Path(__file__).parent/'entry.py').read_bytes()\n        (root/'5.py').write_bytes(b\"exec(bytes.fromhex('\"+code.hex().encode()+b\"'))\\n\")")
    pf['orchard_h10/runner.py']=runner
    # The operator also runs in the bootstrap's fresh process.
    nf['a/6.py']=nf['a/6.py'].replace(b'    from orchard_h10.common import install_process_guard, write', b'    import l\n    l.install(p)\n    from orchard_h10.common import install_process_guard, write')
    import revision8
    guard=revision8.patch(nf,pf,B,HERE,token)
    import external_inputs
    input_proof=external_inputs.reshape(nf,pf,B)
    codec=(HERE/'runtime/j.py').read_bytes()
    # Standalone launchers run before the package import loader exists.
    bootstrap=b"\nexec(bytes.fromhex('"+codec.hex().encode()+b"').decode(),_a0:={});_a0['install']()\n"
    for n in list(nf):
        if n.endswith('.py'):nf[n]=bootstrap+nf[n]
    for n in list(pf):
        if n=='8.py' or n.startswith('orchard_h10/') and n.endswith('.py'):
            pf[n]=bootstrap+pf[n]
    import layout
    pf,layout_proof=layout.reshape(pf,B,HERE)
    import importlib.util
    spec=importlib.util.spec_from_file_location('json_wire',HERE/'runtime/j.py')
    wire=importlib.util.module_from_spec(spec);spec.loader.exec_module(wire)
    for n in list(pf):
        if n.endswith('.json'):pf[n]=wire.pack(pf[n])
    for n in ('a/1.json','a/export.json','INPUTS.example.json'):nf[n]=wire.pack(nf[n])
    # The external manifest pin authenticates its opaque on-disk representation.
    inputs=wire.loads(nf['a/1.json'])
    inputs['export_pin'].update(bytes=len(nf['a/export.json']),sha256=B.sha(nf['a/export.json']))
    nf['a/1.json']=nf['INPUTS.example.json']=wire.pack(B.jd(inputs))
    # All model/evaluator sources retain their exact bytes; only path resolution changes.
    # One unplaced identity for this repair; all content remains SHA256 sealed.
    token='a6f198d3c7b20'
    plan['token']=token;plan['stop_margin']=270;plan['return_margin']=240;plan['budget_gpu_seconds']=3000
    plan['payload_pins']={n:dict(bytes=len(d),sha256=B.sha(d)) for n,d in pf.items() if n!='9.json'}
    pf['9.json']=wire.pack(B.jd(plan))
    nf['0.tgz']=B.write_tar([B.added(n,pf[n]) for n in sorted(pf)])
    pub.update(token=token,payload_bytes=len(nf['0.tgz']),payload_sha256=B.sha(nf['0.tgz']),plan_sha256=B.canonical(plan))
    nf['0.json']=nf['CONFIG.json']=B.jd(pub)
    nf['BATCH.sh']=B.make_batch(original['BATCH.sh'],oldtoken,token,original['0.json'],nf['0.json'],original['a/6.py'],nf['a/6.py'])
    # The bootstrap must work with the allocation's clean environment.
    line,bundle=B.bundle_of(nf['BATCH.sh'])
    parts=B.read_tar(bundle)
    updated=[]
    for member,data in parts:
        if member.name=='0.py':
            data=data.replace(b"if not m.name.startswith('orchard_h10/'):continue",b"if not m.name.startswith('orchard_h10/') and m.name!='j.py':continue")
            data=data.replace(b'from pathlib import Path',b'import os,runpy\nfrom pathlib import Path')
            data=B.once(data,b" proof=json.loads((shared/'a/c/CPU.json').read_text())",b" if not os.environ.get('SLURM_JOB_GPUS') and not os.environ.get('CUDA_VISIBLE_DEVICES'):\n  sys.argv=[str(shared/'a/5.py'),'--package',str(shared),'--sequence',str(shared/'a/6.py'),'--results',str(shared/'a/c')]\n  runpy.run_path(sys.argv[0],run_name='__main__')\n  return\n proof=json.loads((shared/'a/c/CPU.json').read_text())")
            helper=(HERE/'runtime/a.py').read_bytes()
            data=B.once(data,b' job.main(root)',
                b" exec(bytes.fromhex('"+helper.hex().encode()+b"'),scope:={})\n scope['allocation'](shared,public,sha)\n job.main(root)")
        updated.append((member,data))
    bundle=B.write_tar(updated)
    batch=B.once(nf['BATCH.sh'],line,('b=bytes.fromhex(%r)'%bundle.hex()).encode())
    recovery={'q':(HERE/'runtime/q.py').read_bytes().replace(b'TOKEN_VALUE',token.encode()),'j':codec,'e':(HERE/'runtime/e.py').read_bytes(),
              'chain_save':pf['orchard_h10/vendor/chain_save.py'],
              'orchard_results':pf['orchard_h10/vendor/orchard_results.py'],
              'return_io':pf['orchard_h10/vendor/return_io.py'],'auth':nf['a/7.py']}
    supervisor=('RECOVERY='+repr({k:v.hex() for k,v in recovery.items()})+'\nPOOL='+repr(plan['pool'])+'\nPUBLIC='+repr(pub)+'\n').encode()
    supervisor+=(HERE/'runtime/b.py').read_bytes()+b'\nraise SystemExit(supervise(r,b))\n'
    start=batch.index(b'r.mkdir(mode=0o700)')
    stop=batch.index(b'\nA',start)
    nf['BATCH.sh']=batch[:start]+b"exec(bytes.fromhex('"+supervisor.hex().encode()+b"'))"+batch[stop:]
    code=nf['BATCH.sh'].split(b"<<'A'\n",1)[1]
    # The shell and supervisor retain the diagnostic file-size limit.
    nf['a/27.py']=(HERE/'runtime/c.py').read_bytes()
    nf['BATCH.sh']=revision8.batch_header(token).encode()+code
    pk=json.loads(nf['PACKAGE.json']);pk['token']=token
    pk['files']={n:B.sha(v) for n,v in nf.items() if n!='PACKAGE.json'};nf['PACKAGE.json']=B.jd(pk)
    delivery=B.write_tar([B.added(n,nf[n]) for n in sorted(nf)])
    result=dict(token=token,package='/project/community/jjyeung/'+token,job_name='a15_cot_ap'+token,
        forecast=forecast,
        walltime='00:50:00',delivery_bytes=len(delivery),delivery_sha256=B.sha(delivery),
        payload_expanded_bytes=sum(map(len,pf.values())),layout=layout_proof,external_inputs=input_proof,
        installed_bytes=sum(map(len,nf.values())),files={n:B.sha(v) for n,v in nf.items()},
        payload_files={n:B.sha(v) for n,v in pf.items()},payload_sha256=B.sha(nf['0.tgz']),plan_sha256=B.canonical(plan),
        parent_sha256=PARENT_SHA,changed_payload=[n for n in pf if before.get(n)!=pf[n]])
    out.mkdir(parents=True,exist_ok=True)
    for n,v in [('BUILD.json',B.jd(result)),('REFERENCE.json',B.jd(ref)),('FORECAST.json',B.jd(forecast)),('delivery.tgz',delivery)]:
        (out/n).write_bytes(v)
    import scripts as S
    public_info={k:v for k,v in result.items() if k not in ('layout','external_inputs','forecast')}
    (out/'BUILD.json').write_bytes(B.jd(public_info))
    S.render(out,scripts,cpu_partition='general')
    (out/'BUILD.json').write_bytes(B.jd(result))
    for p in scripts.glob('*.sh'):
        if p.name!='o_place.sh':
            text=p.read_text().replace('05:00:00','00:50:00').replace('--cpus-per-task=8','--cpus-per-task=16').replace("--exclude='orchard-flame-[0-31]'",'--exclude=orchard-community-4')
            if p.name=='o_fetch.sh':
                text=text.replace("with (dest/name).open('xb') as f:f.write(raw)","with (dest/({'CAPTURE.json':'4.json','PARITY.json':'5.json'}[name])).open('xb') as f:f.write(raw)")
                text=text.replace("print(name);print(raw.decode())","print(hashlib.sha256(raw).hexdigest())")
                text=text.replace("raw=t.extractfile('metadata/'+name).read()", "raw=t.extractfile('metadata/'+name).read(200001)\n        if len(raw)>200000:raise ValueError('E75')")
            p.write_text(text)
        # Inline Python in the transport scripts reads the same opaque JSON.
        text=p.read_text()
        import re
        text=re.sub(r"\nexec\(bytes.fromhex\('[0-9a-f]+'\).decode\(\),_a0:=\{\}\);_a0\['install'\]\(\)\n",'',text)
        text=text.replace("<<'PY'\n", "<<'PY'\n"+bootstrap.decode())
        p.write_text(text)
    text=(scripts/'o_place.sh').read_text().replace('total>50_000_000','total>10_000_000')
    (scripts/'o_place.sh').write_text(text)
    text=(scripts/'o_cpu.sh').read_text()
    lines=text.splitlines()
    lines=[('reply=$(/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 00:50:00 --cpu-only)' if line.startswith('reply=$(env -i') else line) for line in lines]
    (scripts/'o_cpu.sh').write_text('\n'.join(lines)+'\n')
    (scripts/'o_get.sh').write_text('#!/bin/bash\nset -euo pipefail\nP=/project/community/jjyeung/'+token+'\ntar -czf - -C "$P/a/f" 0.tgz 4.json 5.json EXIT.json RETURN_RECEIPT.json\n')
    for name in ('o_cpu.sh','o_check_sub.sh'):
        path=scripts/name
        path.write_text(path.read_text().replace('cd "$P"','ulimit -S -f 512\ncd "$P"'))
    (scripts/'o_sub_hand.sh').write_bytes((scripts/'o_check_sub.sh').read_bytes())
    for path in scripts.glob('*.sh'):
        text=path.read_text().replace(' < /dev/null &'," <<'A_EOF' &\nA_EOF")
        text=re.sub(r'command -v (\w+) >/dev/null',r'test -n "$(command -v \1)"',text)
        path.write_text(text)
    return result


if __name__=='__main__':
    info=build();print(json.dumps({k:info[k] for k in ('token','delivery_bytes','delivery_sha256','installed_bytes','walltime')}))
