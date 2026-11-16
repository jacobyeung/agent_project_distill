"""Exercise batch bootstrap, staging, chain, worker, budgets and publishing on CPU."""
import argparse
import base64
from contextlib import contextmanager,ExitStack,redirect_stdout,redirect_stderr
import copy
import io
import json
import os
from pathlib import Path
import re
import runpy
import sys
import uuid
from unittest.mock import patch
ROOT=Path('/scratch/jjyeung/orch_n30/b07_offread/builds/R/kit/vsi')
for d in ('launcher','reader','reader/evaluator','cohort','proof'):sys.path.insert(0,str(ROOT/d))
import fixtures as F


def unpack(raw):
    import tarfile
    from xnames import logical_path
    with tarfile.open(fileobj=io.BytesIO(raw)) as tf:return {logical_path(m.name):tf.extractfile(m).read() for m in tf}


def run(work,real_base=None,real_videos=False):
    import orchard_launcher as L,orchard_job as J,orchard_stage as S,orchard_results as R
    import official_adapter as A,official_score as O,frame_plan,chain,data
    import fakes
    work=Path(work).absolute();work.mkdir(parents=True,exist_ok=False)
    token='a'+uuid.uuid4().hex[:12];job='900000';root=work/('a_'+job+'_'+token)
    import xnames
    descriptor=os.open(ROOT.parents[1],os.O_RDONLY|os.O_DIRECTORY)
    owner=ROOT.parents[1]
    roots=[owner/'kit',owner/'tests',owner/'out',Path('/scratch/jjyeung/orch_n30/b07_offread/kit/offkit')]
    held=[descriptor]
    for base in roots:
        fd=os.open(base,os.O_RDONLY|os.O_DIRECTORY);held.append(fd)
        alias='/proc/'+str(os.getpid())+'/fd/'+str(fd)
        entries=[base]+list(base.rglob('*')) if base.name!='out' else [base]+list(base.glob('*.json'))
        for entry in entries:
            xnames._ALIASES[xnames._key(str(entry))]=alias+'/'+str(entry.relative_to(base))
    xnames.install(work)
    all_rows=O.read_rows(ROOT/'cohort/meta_5130.jsonl');chosen=F.select(all_rows);chosen_ids={str(r['id']) for r in chosen}
    manifest=json.loads((ROOT/'cohort/MEDIA_MANIFEST.json').read_text());by_rel={r['relative_path']:r for r in manifest}
    fixture_media={};plan_videos={};small_manifest=[]
    for i,rel in enumerate(sorted({r['dataset']+'/'+r['scene_name']+'.mp4' for r in chosen})):
        source=Path(by_rel[rel]['alias_path']) if real_videos else F.video(work/(str(i)+'.mp4'),i)
        if real_videos and F.sha(source)!=by_rel[rel]['sha256']:raise ValueError('Real video pin differs')
        fixture_media[rel]=source
        plan_videos[rel]=frame_plan.one(source)
        small_manifest.append(dict(by_rel[rel],sha256=F.sha(source)))
    # Preparation checks production membership and hashes. These unexecuted entries
    # are fixture descriptors, never asserted as observed production frame plans.
    template=next(iter(plan_videos.values()))
    prep_plan=dict(mode='decode',videos={r['relative_path']:dict(template,sha256=r['sha256']) for r in manifest})
    F.js(work/'p0.json',prep_plan)
    config=L.prepare(token,work/'prepared',work/'p0.json',mode='production')
    original_config=copy.deepcopy(config)
    script=(work/'prepared/BATCH.sh').read_text()
    raw=bytes.fromhex(re.search(r"^raw=bytes.fromhex\('([^']+)'",script,re.M)[1])
    boot=unpack(raw);payload=unpack(boot['bootstrap/payload.tar.gz'])
    physical=J.physical
    logical_package=config['spec']['package'];package=physical(root,logical_package)
    artifact=physical(root,config['spec']['artifact']['path'])
    fixture=work/'f';fixture.mkdir()
    base,bm,export,ap=F.models(fixture,artifact,real_base)
    pfx=str(physical(Path('/'),logical_package).relative_to('/'))+'/'
    payload[pfx+'cohort/MEDIA_MANIFEST.json']=(json.dumps(small_manifest)+'\n').encode()
    payload[pfx+'cohort/COHORT_OFFICIAL6.jsonl']=''.join(json.dumps(r)+'\n' for r in chosen).encode()
    payload[pfx+'cohort/FRAME_PLAN.json']=(json.dumps(dict(schema=1,mode='decode',videos=plan_videos))+'\n').encode()
    export_tar=F.archive(fixture/'e.tar',{'m544/'+str(p.relative_to(export)):p.read_bytes() for p in export.rglob('*') if p.is_file()})
    transport=dict(parts=[dict(name='fixture',generation='1',bytes=export_tar['bytes'],sha256=export_tar['sha256'])],
                   archive_sha256=export_tar['sha256'],archive_bytes=export_tar['bytes'])
    payload[pfx+'TRANSPORT.json']=(json.dumps(transport)+'\n').encode()
    groups=[]
    for i,files in enumerate(({'m/ap/90da7ac2/m/base_manifest.json':bm.read_bytes()}, {'a1.json':b'{}'}, {'a2.json':b'{}'})):
        pin=F.archive(fixture/f'r{i}.tar',files);groups.append([[pin['path'],pin['bytes'],pin['sha256']]])
    base_tar=F.archive(fixture/'b.tar',{'a/b/c/'+p.name:p.read_bytes() for p in base.iterdir()})
    camera=F.archive(fixture/'c.tar',{'a3.json':b'{}'})
    (fixture/'bwrap').write_bytes(b'fixture');(fixture/'cloud').mkdir()
    config['assets'].update(groups=groups,camera_archive=camera,base_archive=base_tar['path'],base_archive_bytes=base_tar['bytes'],
        base_manifest=dict(path=str(J.AP/'90da7ac2/m/base_manifest.json'),sha256=F.sha(bm)),
        bwrap_pin=dict(path=str(fixture/'bwrap'),bytes=7,sha256=F.sha(fixture/'bwrap')),gcloud_config=str(fixture/'cloud'))
    config['spec']['artifact']=dict(kind='c1_export',path=str(artifact),sha256=F.sha(ap))
    config['spec']['models']=dict(base=dict(kind='snapshot',path=str(root/'m/ap/85fc3486'),
        manifest=dict(path=str(root/'m/ap/90da7ac2/m/base_manifest.json'),sha256=F.sha(bm))),cp1m200=config['spec']['artifact'])
    config['spec'].update(run=str(physical(root,config['spec']['run'])),package=str(package))
    config['spec']['inputs'].update(rows=str(physical(root,config['spec']['inputs']['rows'])),video_root=str(work/'videos'),frame_plan=str(package/'cohort/FRAME_PLAN.json'))
    config['release']['transport']['path']=str(package/'TRANSPORT.json')
    config['bootstrap_parent']=str(work)
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'kit'))
    import rebind as B
    binding=B.bind('vsibench5130' if ROOT.name=='vsi' else 'revsi999t32','step544','direct', ledger=work/'official.jsonl')
    binding['export']=dict(kind='fixture',sha256=F.sha(ap),label='CPU fixture with synthetic answers')
    binding['binding_sha256']=B.binding_sha256(binding)
    config.update(x0=binding['binding_sha256'],x1=F.sha(ap),x2=0)
    config['plan_sha256']=L.canonical(config['spec'])
    boot['bootstrap/payload.tar.gz']=L.tar_bytes(payload)
    config['payload_sha256']=S.hashlib.sha256(boot['bootstrap/payload.tar.gz']).hexdigest()
    config['payload_pins']={n:S.hashlib.sha256(b).hexdigest() for n,b in payload.items()}
    boot['bootstrap/ORCHARD_ASSETS.json']=(json.dumps(config['assets'])+'\n').encode()
    config['launcher_pins']['ORCHARD_ASSETS.json']=S.hashlib.sha256(boot['bootstrap/ORCHARD_ASSETS.json']).hexdigest()
    review=dict(config['launcher_review'],code_pins_sha256=L.canonical(config['launcher_pins']))
    boot['bootstrap/REVIEW.json']=(json.dumps(review)+'\n').encode()
    config['launcher_review_pin']['sha256']=S.hashlib.sha256(boot['bootstrap/REVIEW.json']).hexdigest()
    boot['bootstrap/CONFIG.json']=(json.dumps(config)+'\n').encode()
    script=L.render_batch(L.tar_bytes(boot),token,str(work));L.validate_batch(script,config)
    (work/'BATCH.sh').write_text(script)
    # Dataset names exist only in this local test fixture tree.
    for rel,path in fixture_media.items():
        target=work/'videos'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.symlink_to(path)
    processor=None
    if real_base:
        from transformers import AutoProcessor
        processor=AutoProcessor.from_pretrained(real_base,local_files_only=True)
    processor,engine=fakes.install(processor);engine.selected=sorted(chosen_ids)
    original_tasks=data.tasks_for
    original_loader=data.official_rows
    def subset(spec,roots):return [r for r in original_loader(spec,roots) if r['example_id'] in chosen_ids]
    def membership(cfg):
        ts=A.tasks(cfg)
        if {r['example_id'] for r in ts}!=chosen_ids:raise ValueError('Proof membership differs')
        return ts
    original_score=O.score_run
    def score(dest,cohort,output,**kwargs):return original_score(dest,package/'cohort/COHORT_OFFICIAL6.jsonl',output,allow_partial=True)
    original_run=J.subprocess.run
    original_popen=J.subprocess.Popen
    def command(argv,**kwargs):
        if argv[0]=='nvidia-smi':
            text='0, GPU-fixture, NVIDIA H100 80GB HBM3, 0, 0\n' if '--query-gpu=' in argv[1] else ''
            return J.subprocess.CompletedProcess(argv,0,text,'')
        if argv[0]=='pgrep':return J.subprocess.CompletedProcess(argv,1,'','')
        if any(str(x).endswith('prove_prompts.py') for x in argv):
            target=argv[argv.index('--output')+1]
            with patch.object(J.subprocess,'run',original_run),patch.object(J.subprocess,'Popen',original_popen):
                return original_run([sys.executable,'-B',str(Path(__file__).resolve().parent/'parity_fixture.py'),str(ROOT),target],capture_output=True)
        raise ValueError('Unexpected fixture command: '+str(argv))
    @contextmanager
    def cloud(argv,env,log):
        if argv[:3]!=['gcloud','storage','cat']:raise ValueError('Unexpected fixture process')
        with (fixture/'e.tar').open('rb') as stream:yield stream
    publish=R.publish
    pool=work/'pool'
    def publish_local(source,unused,token,plan,code,**kw):return publish(source,pool,token,plan,code,synthetic=False,rate=4*1024**2,**kw)
    pool_operation=R.pool_operation
    def local_pool(*args,**kwargs):
        with patch.object(J.subprocess,'run',original_run),patch.object(J.subprocess,'Popen',original_popen):
            return pool_operation(*args,**kwargs)
    config['pool']=str(pool)
    boot['bootstrap/CONFIG.json']=(json.dumps(config)+'\n').encode()
    script=L.render_batch(L.tar_bytes(boot),token,str(work))
    class Child:
        def __init__(self,cmd,**kw):
            self.pid=999999;self.returncode=None
            log=io.StringIO()
            try:
                with redirect_stdout(log),redirect_stderr(log),patch.object(sys,'argv',['chain.py','--config',str(root/'bootstrap/CONFIG.json')]):
                    import gate
                    gate.run(json.loads((root/'bootstrap/CONFIG.json').read_text()),root)
                self.returncode=0
            except BaseException:
                import traceback
                traceback.print_exc(file=log);self.returncode=1
            kw['stdout'].write(log.getvalue().encode())
        def wait(self,**kw):return self.returncode
        def poll(self):return self.returncode
    def mapped(r,p):return Path(p) if Path(p).is_relative_to(work) else physical(r,p)
    # The actual mount-id check and filesystem policy execute against a fixture mount table.
    storage=J.storage_proof
    def local_storage(path,job=None):
        text='123 1 8:1 /job_tmp/900000 /tmp rw - ext4 /dev/fixture rw\n'
        # Use /tmp as the policy probe; the test's bytes remain under work/kit.
        with patch.object(J,'active_mount',return_value=dict(mount_id=123,probe_path=str(path))):
            result=storage('/tmp',mountinfo=text,job=job)
        result['fixture_path']=str(path);return result
    def execv(executable,argv):
        with patch.object(sys,'argv',['orchard_job.py','--root',str(root),'--config',str(root/'bootstrap/CONFIG.json')]):
            try:J.main()
            except SystemExit as e:
                if e.code:raise RuntimeError('Fixture job failed; inspect '+str(root/'chain.log'))
    def utility(spec,script,args,python=None):
        if Path(script).name=='phase_b.py':
            env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
            with patch.object(J.subprocess,'run',original_run),patch.object(J.subprocess,'Popen',original_popen):
                original_run([sys.executable,'-B',str(ROOT/'launcher/trace_runtime.py'),'--root',str(root),
                    '--config',str(root/'bootstrap/CONFIG.json'),'--script',str(script),*map(str,args)],check=True,env=env)
        elif args[0]=='plan':
            result=frame_plan.compute(spec['inputs']['video_root'],package/'cohort/MEDIA_MANIFEST.json')
            F.js(Path(args[args.index('--output')+1]),result)
        elif args[0]=='frames':
            import frame_stage
            result=frame_stage.stage(args[args.index('--input')+1],args[args.index('--output')+1],16)
            if result['errors']:raise ValueError('Frame stage has errors')
        elif Path(script).name=='prove_prompts.py':
            out=Path(args[args.index('--output')+1]);out.mkdir()
            raise AssertionError('Production must use the bootstrap parity proof')
        else:raise ValueError('Unexpected fixture utility')
    def fixture_tasks(spec,roots):
        rows=original_tasks(spec,roots)
        return [dict(r,answer='3',ground_truth='3',released_answer='3') for r in rows if r['example_id'] in chosen_ids]
    def fixture_membership(cfg):
        ts=A.tasks(cfg)
        assert {t['example_id'] for t in ts}==chosen_ids
        return ts
    import gate
    real_namespace=J.namespace
    namespace_checks=[]
    def checked_namespace(*args):
        argv=real_namespace(*args)
        with patch.object(J.subprocess,'run',original_run),patch.object(J.subprocess,'Popen',original_popen):
            mapped=original_run(['/bin/echo',*argv],capture_output=True,text=True,check=True).stdout.split()
        for arg in mapped:xnames.scan(arg)
        shell=(package/'vllm_isolated.sh').read_text()
        import shlex
        target=shlex.split(shell.splitlines()[1])[1]
        assert target.startswith(str(J.AP)+'/')
        assert str(J.AP) in mapped
        namespace_checks.append(dict(argv=mapped,exec_target=target,root=str(args[0]),passed=True))
        return argv
    with ExitStack() as stack:
        stack.enter_context(patch.object(data,'tasks_for',fixture_tasks))
        stack.enter_context(patch.object(A,'membership',fixture_membership))

        for obj,name,value in [(fakes,'install_engine',lambda ids:setattr(engine,'selected',ids)),(chain,'utility',utility),(A,'HERE',package/'reader'),(A,'EXPORT_SHA',F.sha(ap)),(A,'BASE_SHA',F.sha(bm)),(O,'score_run',score),(S,'MIN_FREE',0),
            (S,'video_source',lambda row:fixture_media[row['relative_path']]),(S,'question_source',lambda:ROOT/'cohort/meta_5130.jsonl'),
            (S,'process_stream',cloud),(J,'physical',mapped),(J,'storage_proof',local_storage),
            (J,'namespace',checked_namespace),(R,'pool_operation',local_pool),(R,'upload',lambda *a:dict(verified=False,fixture=True,error='No local GCS access')),(R,'publish',publish_local),(R,'AUTHORIZED_POOL',pool),
            (J.subprocess,'run',command),(J.subprocess,'Popen',Child),(os,'execv',execv)]:stack.enter_context(patch.object(obj,name,value))
        stack.enter_context(patch.dict(os.environ,dict(A_JOB_CONFIG=str(root/'bootstrap/CONFIG.json'),SLURM_JOB_ID=job,CUDA_VISIBLE_DEVICES='0',USER=os.environ.get('USER','jjyeung'))))
        body=script.split("<<'P0'\n",1)[1].rsplit('\nP0',1)[0]
        trace_source=work/'_bootstrap_current.py'
        trace_source.write_text(body+'\n')
        cwd=Path.cwd()
        try:exec(compile(body,str(trace_source),'exec'),{'__name__':'__main__'})
        finally:os.chdir(cwd)
    receipt=json.loads((pool/token/'EXIT.json').read_text())
    if receipt['status']!='COMPLETE':raise AssertionError(receipt)
    source_root=Path(config['spec']['run'])
    reports={arm:json.loads((source_root/'report'/(arm+'.json')).read_text()) for arm in ('ON16k','B2048','B4096')}
    diagnostics={arm:dict(errors=sum(len(g['errors']) for g in report['groups'].values()),
        source_capped=sum(g['source_capped'] for g in report['groups'].values()),
        continuation_capped=sum(g['continuation_capped'] for g in report['groups'].values()),
        unparsed=sum(g['unparsed'] for g in report['groups'].values())) for arm,report in reports.items()}
    if diagnostics['B2048']['errors']!=1 or diagnostics['B4096']['errors']!=0 or diagnostics['B4096']['continuation_capped']!=1:
        raise ValueError('Expected continuation error/cap fixture did not execute: '+str(diagnostics))
    if any(d['source_capped']!=1 for d in diagnostics.values()) or diagnostics['B2048']['unparsed']<1:
        raise ValueError('Source cap/unparsed fixture did not execute')
    for arm,report in reports.items():
        if {r['id'] for r in report['rows']}!=chosen_ids or any(g['items']!=(4 if k=='object_rel_direction' else 2) for k,g in report['groups'].items()):
            raise ValueError('Proof arm membership differs')
    result=dict(passed=True,items=14,phase_b_items=20,diagnostics=diagnostics,datasets=sorted({r['dataset'] for r in chosen}),
        real_videos=real_videos,real_processor=bool(real_base),packet_decode_equal=all(p['packet_equals_decode'] for p in plan_videos.values()),
        job_root=str(root),pool=str(pool/token),archive_bytes=receipt['archive']['bytes'],
        synthetic=True,production_membership=4008,proof_membership=sorted(chosen_ids),
        boundaries=['vLLM engine','nvidia-smi','small runtime/base/export fixtures','local mount/namespace/process bridge','14 official items and 20 dev smoke items','local publish pool'])
    result['namespace_checks']=namespace_checks
    result['config_mode']=config['mode']
    result['phase_b_items']=0
    result['real_processor']=False
    result['boundaries']=['Local archive, media, namespace, GPU and process transports are stand-ins.',
        'The task provider supplies the fixed accepted proof subset with constant synthetic answers.',
        'The engine and tokenizer are fakes; the pre-decode parity proof uses a fixed chat-template stand-in.']
    result['config']=config
    packet=work/'packet';packet.mkdir()
    (packet/'BATCH.sh').write_text(script)
    B.dump(packet/'CONFIG.json',config)
    B.dump(packet/'BINDING.json',binding)
    B.dump(packet/'BATCH.pin.json',dict(sha256=B.sha256_file(packet/'BATCH.sh'),config_sha256=B.sha256_file(packet/'CONFIG.json')))
    from types import SimpleNamespace as NS
    result['fetch']=B.fetch(NS(destination=packet,return_dir=pool/token))
    result['reports']=B.report(NS(destination=packet,return_dir=None,accepted_return=False))
    result['fixture_packet']=str(packet)
    F.js(work/'RESULT.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--real-base');p.add_argument('--real-videos',action='store_true')
    a=p.parse_args();print(json.dumps(run(a.work,a.real_base,a.real_videos)))
