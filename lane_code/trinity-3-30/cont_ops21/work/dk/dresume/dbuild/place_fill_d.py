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
import make_items_d


def read(p): return json.loads(Path(p).read_text())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(1024**2),b''):h.update(chunk)
    return h.hexdigest()


def check_part(path,pin):
    if path.stat().st_size!=pin['bytes'] or sha(path)!=pin['sha256']:
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
    m=json.loads(pf['items/dist580.json'])
    make_items_d.validate(m,json.loads(pf['items/room134.json']),set(pf['auth/R0_DEV_ROOMS.txt'].decode().splitlines()))
    assert hashlib.sha256(pf['items/dist580.json']).hexdigest()==report['items_sha256']
    return pf


def run(stage):
    stage=Path(stage).resolve();report=read(stage/'BUILD.json')['D'];binding=read(stage/'binding.json')
    if sha(stage/'binding.json')!=report['binding_sha256']:raise ValueError('Binding changed after build')
    if binding['step']==400:
        expected='/project/community/jjyeung/okh7/x_ee227714/o/gcs_6ed2c7aa_m400.done'
        if binding.get('run')!='6ed2c7aa' or binding.get('done')!=expected:
            raise ValueError('Unreviewed step-400 receipt binding')
        if os.environ.get('DONE_FROM',expected)!=expected:
            raise ValueError('Step 400 requires the sealed x_ee227714 done path')
        if not os.environ.get('REUSE_PARTS_FROM'):
            raise ValueError('Step 400 requires REUSE_PARTS_FROM')
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
    prep=os.environ.get('PREP_FROM') or reuse
    if not prep and binding['step']==200:
        prep='/project/community/jjyeung/okh7/a15_cot_apd72cdcff1e22a/a/e'
    for key,n in (('config','7'),('receipt','8'),('data_receipt','9')):
        if prep:
            raw=(Path(prep)/n).read_bytes()
        else:
            candidates=[v for k,v in pf.items() if k.endswith('.json') and hashlib.sha256(v).hexdigest()==binding['preparation_sha256'][key]]
            if not candidates:raise ValueError('Set PREP_FROM to a directory containing pinned preparation files 7,8,9')
            raw=candidates[0]
        assert hashlib.sha256(raw).hexdigest()==binding['preparation_sha256'][key],key
        (e/n).write_bytes(raw)
    fields=[binding['object'],str(binding['archive_bytes']),binding['archive_sha256']]
    done=os.environ.get('DONE_FROM') or (binding['done'] if binding['step']==400 else None)
    if done:
        if Path(done).read_text().split()!=fields:raise ValueError('External receipt differs from sealed binding')
    elif prep and (Path(prep)/'5').exists():
        if (Path(prep)/'5').read_text().split()!=fields:raise ValueError('Reuse receipt differs')
    # This is a declaration of sealed archive pins, not a claimed upstream completion receipt.
    # a/4.py verifies these bytes and the whole SHA256 while scanning all four parts.
    (e/'5').write_text(' '.join(fields)+'\n')
    if binding['step']==400:
        (e/'5').write_bytes(Path(done).read_bytes())
        prepared={k:read(e/n) for k,n in [('config','7'),('receipt','8'),('data_receipt','9')]}
        assert prepared['config']['base_identity']==binding['base_identity']
        assert prepared['receipt']['config_sha256']==binding['config_sha256']
        assert prepared['config']['frame_layout']==prepared['receipt']['frame_layout']==binding['frame_layout']
        for i,pin in enumerate(binding['parts']):check_part(Path(reuse)/str(i),pin)
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
            except OSError:
                if binding['step']==400:raise
                shutil.copyfile(str(source),str(dest))
            if dest.stat().st_size!=pin['bytes']:raise ValueError('Linked/copied size differs')
        else:
            partial=e/(str(i)+'.partial')
            argv=['gsutil','-o','Boto:num_retries=0','-o','Boto:metadata_service_num_attempts=1',
                  '-o','GSUtil:parallel_process_count=1','-o','GSUtil:parallel_thread_count=1',
                  '-o','GSUtil:sliced_object_download_threshold=0','-o','GSUtil:sliced_object_download_max_components=1',
                  '-q','cp','gs://cmu-gpucloud-jjyeung/'+binding['object']+'.part0%d-of-04'%i,str(partial)]
            subprocess.run(argv,check=True,env=env)
            check_part(partial,pin);partial.rename(dest)
        print('Verified part',i,flush=True)
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
    with (stage/'dry_D.json').open('w') as out:
        subprocess.run(['/usr/bin/python3','-I','-s','-B',str(stage/'dryres_d.py'),str(package/'a/1.json'),
                        str(package/'a/0.json'),sha(package/'a/6')],stdout=out,check=True)
    subprocess.run(['/usr/bin/python3','-I','-s','-B','3.py','check','--gpus','1','--time',report['walltime']],
                   cwd=str(package),env=dict(os.environ,CUDA_VISIBLE_DEVICES=''),check=True)
    (package/'a/10.json').write_text(json.dumps(dict(passed=True,inputs_sha256=sha(package/'a/1.json'),
         export_sha256=sha(package/'a/export.json')),sort_keys=True)+'\n')
    (package/'a/1.txt').write_text('0\n')
    print(json.dumps(dict(filled=str(package),dry_passed=True,submitted=False,walltime=report['walltime'])))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage');run(p.parse_args().stage)
