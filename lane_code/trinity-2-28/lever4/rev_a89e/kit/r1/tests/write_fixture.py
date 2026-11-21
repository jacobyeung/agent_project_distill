"""Bind remote staging and model work to tiny local inputs for the CPU entry."""
import json
import os
from pathlib import Path
import sys
import tempfile


def configure(job,package,root,case):
    from orchard_h10 import common,export_pins
    S,J,R,I,A=job.template()
    job.check_inputs=lambda value,*args,**kw:value
    export_pins.load=lambda *args:{}
    J.storage_proof=lambda *args,**kw:dict(filesystem='ext4',fixture=True)
    work=root/'34';work.mkdir()
    tempfile.mkdtemp=lambda **kw:str(work)
    cfg=common.read_config(package)
    def stage(r,c,inputs,*args):
        (r/'a').mkdir()
        metadata=J.physical(r,c['logical']+'/r/metadata');metadata.mkdir(parents=True)
        boot=dict(passed=True,job=os.environ['SLURM_JOB_ID'],plan=c['plan_sha256'],fixture=True)
        common.write(metadata/'25.json',boot);common.write(package/'a/25.json',boot)
        d=J.physical(r,c['logical']+'/d');d.mkdir(parents=True)
        common.write(d/'READY.json',dict(fixture=True))
        common.write(d/'settings.json',dict(stage1_select_rule='null_argmax',perception_memo='off',
                     perception_memo_modules=['g3t'],perception_memo_verify_ids=[]))
        # The operator's own bound, as the measured model run would record it.
        import runpy
        memory=runpy.run_path(str(package/'a/6.py'),run_name='write_fixture')['memory_bound']()
        common.write(metadata/'MEMORY.json',memory)
        if case=='write_budget':
            pool=r/'wpool';pool.mkdir();(pool/(c['token']+'.0')).write_text('11999990')
    job.stage=stage
    def unit_receipts():
        # The operator's real-unit receipts, shaped as cpu_unit/g.w.run write them.
        meta=J.physical(work,cfg['logical']+'/r/metadata')
        names=['bind','first_model','load','prefill','record']
        stages=[dict(name=n,seconds=1.,elapsed_s=float(i+1),peak_rss_bytes=1) for i,n in enumerate(names)]
        stages[2].update(step=544,dtypes=['torch.bfloat16','torch.float32'],locations=['cpu'],parameters=1)
        unit=dict(passed=True,status='complete',mode='cpu',failure=None,completed=1,stages=stages,
                  checks=dict(clean=True,grid=dict(shape=[32,51,51],dtype='float16',finite=True),
                              scale=dict(value=1.5,finite=True),K=dict(shape=[32,3,3],finite=True),prefills=1,decode_steps=0),
                  admission=dict(reason='first_unit'),environment=dict(threads=16,cuda_visible=''),unit=dict(threads=16))
        if case=='write_unit_fail':
            unit.update(passed=False,status='failed',failure='E99:52756e74696d654572726f72',stages=stages[:1],
                        error='RuntimeError: injected CPU unit failure')
        common.write(meta/'33.json',unit)
        common.write(meta/'34.json',dict(returncode=0 if case!='write_unit_fail' else 1,stopped=None,
                     memory=dict(over=False,limit_bytes=1,guarded_bytes=0),action=3,phases=[]))
    def model(argv,**kw):
        if argv[-1].endswith('/1.json'):
            # GPUs visible to the CPU operator dispatch (the CPU check must see none).
            seen={k:os.environ.get(k) for k in ('SLURM_JOB_GPUS','SLURM_STEP_GPUS','SLURM_GPUS_ON_NODE','GPU_DEVICE_ORDINAL','CUDA_VISIBLE_DEVICES')}
            seen['dispatch_cuda_visible']=(kw.get('env') or {}).get('CUDA_VISIBLE_DEVICES')
            (root/'gpu_env.json').write_text(json.dumps(seen))
            unit_receipts()
        if argv[-1].endswith('/0.json'):
            evidence=work/'wpool'/cfg['token']/'.wtest'
            if case=='write_size':
                with evidence.open('ab') as stream:stream.write(b'x')
            if case=='write_hash':
                with evidence.open('r+b') as stream:
                    first=stream.read(1);stream.seek(0);stream.write(bytes([first[0]^1]))
            if case=='write_late':raise RuntimeError('injected post-guard preparation failure')
            if case=='write_settings':
                d=J.physical(work,cfg['logical']+'/d')
                value=json.loads((d/'settings.json').read_text());value['perception_memo']='bad'
                common.write(d/'settings.json',value)
        return None
    common.checked_run=model
    if case=='write_receipt':
        original=R.write_test
        def corrupt(*args):
            value=original(*args);value['bytes']+=1;return value
        R.write_test=corrupt
    if case=='write_old':
        import runpy
        original=runpy.run_path
        def old(path,*args,**kw):
            if str(path)==str(package/'a/5.py'):
                path=Path(__file__).resolve().parents[1]/'out/WT_OLD_5.py'
            return original(str(path),*args,**kw)
        runpy.run_path=old
