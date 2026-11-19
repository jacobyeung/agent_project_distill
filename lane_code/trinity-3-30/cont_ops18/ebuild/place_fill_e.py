"""Orchard-only placement/fill driver. Never submits a job; never retries a transfer."""
import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from build_support import read_tar, bundle_of


def read(p): return json.loads(Path(p).read_text())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(1024**2),b''):h.update(chunk)
    return h.hexdigest()


def check_part(path,pin):
    if path.stat().st_size!=pin['bytes'] or ('sha256' in pin and sha(path)!=pin['sha256']):
        raise ValueError('Part differs: '+str(path))


def metadata(package, report, binding):
    pk=read(package/'PACKAGE.json');pub=read(package/'0.json')
    assert package.name=='a15_cot_ap'+pub['token']== 'a15_cot_ap'+report['token']
    for n,h in pk['files'].items():assert sha(package/n)==h,n
    pf=dict((m.name,d) for m,d in read_tar((package/'0.tgz').read_bytes()))
    plan=json.loads(pf['9.json'])
    assert hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()).hexdigest()==pub['plan_sha256']
    assert sha(package/'0.tgz')==pub['payload_sha256']
    assert plan['export_binding']==report['export_binding']
    assert all(binding[k]==v for k,v in plan['export_binding'].items())
    for n,pin in plan['payload_pins'].items():
        assert pin==dict(bytes=len(pf[n]),sha256=hashlib.sha256(pf[n]).hexdigest()),n
    bundle=dict((m.name,d) for m,d in read_tar(bundle_of((package/'BATCH.sh').read_bytes())[1]))
    assert bundle['0.json']==(package/'0.json').read_bytes() and bundle['7.py']==(package/'a/6.py').read_bytes()
    assert read(package/'a/0.json')['types']==['object_abs_distance']
    assert read(package/'a/1.json')=={'pending':True}
    m=json.loads(pf['items/devs1_routed.json'])
    assert m['name']=='devs1_routed' and m['count']==636
    assert len([r for r in m['items'] if r['question_type']=='object_abs_distance'])==150
    assert hashlib.sha256(pf['items/devs1_routed.json']).hexdigest()==report['items_sha256']
    return pf


def run(stage):
    stage=Path(stage).resolve();report=read(stage/'BUILD.json')['E'];binding=read(stage/'binding.json')
    if sha(stage/'binding.json')!=report['binding_sha256']:raise ValueError('Binding changed after build')
    package=Path(report['package']);delivery=Path(report['delivery_dir'])/'1.tgz'
    if not str(package).startswith('/project/community/jjyeung/okh7/a15_cot_ap'):
        raise ValueError('Placement requires the Orchard project namespace')
    if sha(delivery)!=report['delivery_sha256']:raise ValueError('Delivery differs')
    package.mkdir(mode=0o700)
    for m,d in read_tar(delivery.read_bytes()):
        if Path(m.name).is_absolute() or '..' in Path(m.name).parts:raise ValueError('Unsafe delivery')
        path=package/m.name;path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        with path.open('xb') as f:f.write(d)
        path.chmod(m.mode)
    (package/'a').chmod(0o700);pf=metadata(package,report,binding)
    e=package/'a/e';e.mkdir(mode=0o700)
    reuse=os.environ.get('REUSE_PARTS_FROM')
    prep=os.environ.get('PREP_FROM')
    prepared={}
    for key,n in (('config','7'),('receipt','8'),('data_receipt','9')):
        path=Path(binding['prep_paths'][key])
        if prep:
            root=Path(prep)
            # Accept numbered fill files, a preparation directory, or the D0 inputs root.
            candidates=[root/n, root/('prepared/s1_receipt.json' if key=='receipt' else 'config.json' if key=='config' else 'data_receipt.json')]
            candidates.append(root/Path(binding['prep_paths'][key]).relative_to('/project/community/jjyeung/okh7/x_f5c353f7/runs/359fcc3c/inputs'))
            matches=[p for p in candidates if p.is_file()]
            if not matches:raise ValueError('PREP_FROM lacks '+key)
            path=matches[0]
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=binding['preparation_sha256'][key]:raise ValueError('Preparation hash differs: '+key)
        prepared[key]=json.loads(raw);(e/n).write_bytes(raw)
    cfg=prepared['config'];rec=prepared['receipt']
    if cfg.get('base_identity')!=binding['base_identity']:raise ValueError('D0 base identity differs')
    if rec.get('config_sha256')!=binding['config_sha256']:raise ValueError('D0 config identity differs')
    if cfg.get('frame_layout')!=binding['frame_layout'] or rec.get('frame_layout')!=binding['frame_layout']:
        raise ValueError('D0 frame layout differs')
    fields=[binding['object'],str(binding['archive_bytes']),binding['archive_sha256']]
    done=Path(os.environ.get('DONE_FROM',binding['done']))
    if done.read_text().split()!=fields:raise ValueError('Upstream receipt differs from sealed binding')
    (e/'5').write_bytes(done.read_bytes())
    claim=os.environ.get('CLAIM_FROM')
    if claim and Path(claim).read_text().strip()!=binding['member_directory']:
        raise ValueError('Claim member differs')
    env=dict(os.environ,TZ='UTC',CLOUDSDK_CONFIG=os.environ.get('CLOUDSDK_CONFIG','/project/community/jjyeung/gcloud'),
             CLOUDSDK_CORE_DISABLE_PROMPTS='1')
    for i,pin in enumerate(binding['parts']):
        dest=e/str(i)
        if reuse:
            source=Path(reuse)/str(i);check_part(source,pin)
            try:os.link(str(source),str(dest))
            except OSError:shutil.copyfile(str(source),str(dest))
            if dest.stat().st_size!=pin['bytes']:raise ValueError('Linked/copied size differs')
        else:
            partial=e/(str(i)+'.partial')
            argv=['gsutil','-o','Boto:num_retries=0','-o','Boto:metadata_service_num_attempts=1',
                  '-o','GSUtil:parallel_process_count=1','-o','GSUtil:parallel_thread_count=1',
                  '-o','GSUtil:sliced_object_download_threshold=0','-o','GSUtil:sliced_object_download_max_components=1',
                  '-q','cp',pin['uri'],str(partial)]
            subprocess.run(argv,check=True,env=env)
            check_part(partial,pin);partial.rename(dest)
        print('Staged part',i,'(whole-archive authentication follows)',flush=True)
    subprocess.run(['/usr/bin/python3','-I','-s','-B',str(package/'a/4.py'),'--parts']+
        [str(e/str(i)) for i in range(4)]+['--done',str(e/'5'),'--object',binding['object'],
        '--config',str(e/'7'),'--receipt',str(e/'8'),'--data-receipt',str(e/'9'),
        '--lineage',binding['lineage'],'--step',str(binding['step']),'--out',str(package/'a/export.json'),
        '--prep-tar',str(package/'a/6'),'--base-inputs',str(package/'a/0.json'),'--inputs-out',str(package/'a/1.json')],check=True)
    filled=read(package/'a/1.json');base=read(package/'a/0.json');export=read(package/'a/export.json')
    assert len(filled['archives'])==len(base['archives'])+1
    assert filled['archives'][1:-1]==base['archives'][1:]
    assert filled['types']==['object_abs_distance']
    for key in ('run','step','member_directory','object','config_sha256','lineage'):
        assert export[key]==binding[key],key
    with (stage/'dry_E.json').open('w') as out:
        subprocess.run(['/usr/bin/python3','-I','-s','-B',str(stage/'dryres_e.py'),str(package/'a/1.json'),
                        str(package/'a/0.json'),sha(package/'a/6')],stdout=out,check=True)
    subprocess.run(['/usr/bin/python3','-I','-s','-B','3.py','check','--gpus','1','--time',report['walltime']],
                   cwd=str(package),env=dict(os.environ,CUDA_VISIBLE_DEVICES=''),check=True)
    (package/'a/10.json').write_text(json.dumps(dict(passed=True,inputs_sha256=sha(package/'a/1.json'),
         export_sha256=sha(package/'a/export.json')),sort_keys=True)+'\n')
    (package/'a/1.txt').write_text('0\n')
    print(json.dumps(dict(filled=str(package),dry_passed=True,submitted=False,walltime=report['walltime'])))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage');run(p.parse_args().stage)
