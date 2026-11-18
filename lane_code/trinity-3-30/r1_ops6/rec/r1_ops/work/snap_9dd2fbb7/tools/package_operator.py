"""Emit only neutral deployment filenames; keep research reports local."""
import argparse,hashlib,io,json,os,tarfile
from pathlib import Path
from rebind import ROOT,H,AS,enc,sha,load,write
from canary_gate import add_canary

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=ROOT/'out');a=p.parse_args()
    os.umask(0o077);out=a.out;binding=load(out/'BINDING.json');token=binding['store_key'];run=binding['run_key']
    package=out/'operator';package.mkdir(exist_ok=True,mode=0o700)
    # The operator archive contains no store bytes; staging reads the pinned Orchard copy.
    mapping={out/'config.json':'config.json',out/'BINDING.json':'BINDING.json',out/'r1p_code.tar':'t.tar',
        ROOT/'tools/derive_deployment.py':'d.py',ROOT/'tools/seal_proof.py':'p.py',
        ROOT/'tools/unit_binding.py':'u.py',ROOT/'tools/selection_check.py':'q.py',ROOT/'tools/selection_parent.py':'qp.py',
        H/'payload/v.py':'v.py',H/'build/fx/k/0.json':'b0.json',
        out/'proof/selection/r.json':'proof/selection/r.json',out/'proof/selection/q.json':'proof/selection/q.json',
        out/'proof'/('p_'+run+'.sh'):'p_'+run+'.sh'}
    if binding.get('unit_binding'):
        mapping.update({out/'units'/n:n for n in ('u.gz','i.json','m.json','u.json')})
    record_paths=[out/'records'/n for n in binding['record_files']]
    mapping.update({p:'records/'+p.name for p in record_paths})
    for src,name in mapping.items():
        dest=package/name;dest.parent.mkdir(parents=True,exist_ok=True,mode=0o700);dest.write_bytes(src.read_bytes())
    (package/'q.py').write_text((package/'q.py').read_text().replace('import selection_parent','import qp as selection_parent').replace('from unit_binding import regenerate','from u import regenerate'))
    # cur.extra resolves these opaque files directly in the bundle.
    for path in record_paths:(package/path.name).write_bytes(path.read_bytes())
    (package/'s.json').write_bytes((out/'proof/selection/r.json').read_bytes())
    wrapper=(H/'payload/jb.sh').read_text().replace('17c4ffa4',run).replace('x_3fdda0fb','x_'+token).replace('/r/39504485','/r/'+run)
    wrapper=wrapper.replace('i_1be16f28','i_'+token).replace('x_07ca49df/k/0.json','i_'+token+'/b0.json')
    milestones=['m100','m200','mstop','mstopB','mstopC']
    previous='["m1", "m50", "m100", "m200", "m400", "m600", "m800", "m1000", "mstop", "mstopB", "mstopC"]'
    if wrapper.count(previous)!=1:raise ValueError('Inherited export preflight differs')
    wrapper=wrapper.replace(previous,json.dumps(milestones))
    (package/'jb.sh').write_text(wrapper)
    objects=''.join('q8/8865619b/'+run+'_'+m+'.tar.part%02d-of-04\n'%i for m in milestones for i in range(4));(package/'e.txt').write_text(objects)
    assert len(objects.splitlines())==20 and '17c4ffa4' not in objects
    config=load(out/'config.json');launch=load(H/'build/fx/k/launch.json');launch['in_job_admission']['directory']=config['output']+'/inputs'
    contract=hashlib.sha256(enc(launch['in_job_admission']).encode()).hexdigest()
    ids=dict(identity=binding['config_identity'],contract=contract,job_name=binding['job_name'],run_key=run,
             kh='/project/community/jjyeung/okh7/x_'+token,bun='/project/community/jjyeung/okh7/i_'+token)
    write(package/'ids.json',ids)
    submit=(H/'payload/s.sh').read_text().replace('i_1be16f28','i_'+token).replace('x_3fdda0fb','x_'+token).replace('a15_cot_ap5ee9da63',binding['job_name'])
    needle="assert proof.get('prepared_seals') and proof.get('real_job_reuse') is False"
    submit=submit.replace(needle,needle+"\nfor name in ('disk_plan','routing_selection','empty_root','temporary_paths','runtime_binaries','directory_modes','loader_audit','required_families'):\n assert proof.get('checks',{}).get(name,{}).get('status')=='PASS', name")
    if submit.count('python3 -B - ')!=1:raise ValueError('Inherited submit gate invocation differs')
    submit=submit.replace('python3 -B - ', 'env -u PYTHONOPTIMIZE python3 -I -B - ')
    (package/'s.sh').write_text(add_canary(submit))
    # No GO, review, staging, archive attestation or content certificate is manufactured.
    names=sorted(set(mapping.values())|{p.name for p in record_paths}|{'s.json','jb.sh','e.txt','ids.json','s.sh'})
    (package/'sums.txt').write_text(''.join(sha(package/n)+'  '+n+'\n' for n in names))
    forbidden=('r1p','h1','vqa','qwen','scannet','vsi','distill','recovery','units','room','model')
    if any(any(word in n.lower() for word in forbidden) for n in names):raise ValueError('Descriptive deployment filename')
    for n in ('jb.sh','s.sh','p_'+run+'.sh'):
        import subprocess
        subprocess.run(['bash','-n',str(package/n)],check=True)
    archive_bytes=io.BytesIO()
    with tarfile.open(fileobj=archive_bytes,mode='w') as tf:
        for n in sorted(names+['sums.txt']):
            raw=(package/n).read_bytes();info=tarfile.TarInfo(n);info.size=len(raw);info.mode=0o700 if n.endswith('.sh') else 0o600
            tf.addfile(info,io.BytesIO(raw))
    payload=archive_bytes.getvalue()
    # Proof-only changes preserve config paths and use a distinct content name.
    archive=out/('p_'+hashlib.sha256(payload).hexdigest()[:8]+'.tar')
    if archive.exists():
        if archive.read_bytes()!=payload:raise ValueError('Refusing to overwrite an existing packet archive')
    else:
        with archive.open('xb') as handle:handle.write(payload)
    write(out/'OPERATOR.json',dict(archive=archive.name,sha256=sha(archive),bundle=ids['bun'],kit=ids['kh'],job_name=ids['job_name'],
        contract=contract,wrapper_sha256=sha(package/'jb.sh'),proof_script='p_'+run+'.sh',
        public_filename_scan='PASS',private_content_scan='REQUIRES_INDEPENDENT_REVIEW',production_authorized=False))
    print(enc(dict(archive=str(archive),sha256=sha(archive),bundle=ids['bun'],kit=ids['kh'])))
if __name__=='__main__':main()
