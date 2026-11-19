#!/bin/bash
#SBATCH --partition=preempt
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=192G
#SBATCH --gres=none
#SBATCH --no-requeue
#SBATCH --output=/dev/null
#SBATCH --error=/dev/null
set -euo pipefail
umask 077
# RUN STEP OUT LIMIT_SECONDS [KH [ZIP [SHA]]]; set --job-name and --time at submission.
[[ $# -ge 4 && $# -le 7 ]] || exit 2
[[ ${SLURM_JOB_ID:-} =~ ^[0-9]+$ && ${SLURM_JOB_NAME:-} =~ ^a15_cot_ap[0-9a-f]{8}$ ]] || exit 2
[[ $1 =~ ^[0-9a-f]{8}$ && $2 =~ ^[1-9][0-9]*$ && $4 =~ ^[1-9][0-9]*$ ]] || exit 2
[[ $(hostname -s) == orchard-* ]] || exit 2
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export TZ=UTC LC_ALL=C
exec nice -n 19 ionice -c2 -n7 /usr/bin/python3 -B - "$@" <<'PY'
import contextlib, hashlib, json, os, re, resource, shutil, signal, subprocess, sys, tarfile, time
from pathlib import Path, PurePosixPath

AS='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'
AL='/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'
X=AS+'/ap/8865619b'; P='/project/community/jjyeung'; O=P+'/okh7'
BW=P+'/cp4tk_rt/kit/bwrap'; VP=P+'/c7d31ddd/venvs/rwtrain_torch211_cu129/bin/python'
DEFAULT_Z=O+'/h_6ed2c7aa/q2_67f8baf1.zip'
DEFAULT_H='f415c69d7f8adfb6e9483c1bf53deb6f01728689f3c33806c4bda540675c4fdc'

def require(ok, code):
    if not ok: raise ValueError(code)
def load(p):
    with open(p) as f: return json.load(f)
def dump(p,v):
    with open(p,'x') as f: json.dump(v,f,sort_keys=True); f.write('\n')
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(8<<20),b''): h.update(b)
    return h.hexdigest()
def safe(name):
    p=PurePosixPath(name)
    require(not p.is_absolute() and '..' not in p.parts, 'UNSAFE_MEMBER')
    return str(p)
def pick(t, name, dest):
    name=safe(name)
    matches=[m for m in t.getmembers() if safe(m.name)==name]
    require(len(matches)==1 and matches[0].isfile(), 'MEMBER_MISSING_OR_UNSAFE')
    dest.parent.mkdir(parents=True,exist_ok=True)
    with t.extractfile(matches[0]) as src, open(dest,'xb') as dst: shutil.copyfileobj(src,dst,8<<20)
def pin(local, public): return dict(path=public,sha256=sha(local))
def rp_value(cfgpath, boundpath, ckpath, public):
    cfg=load(cfgpath)
    return dict(config=pin(cfgpath,public[0]),binding=pin(boundpath,public[1]),
                preparation=cfg['preparation'],checkpoint=pin(ckpath,public[2]))

# Imported by the local test without starting a job.
def main():
    require(sys.version_info>=(3,9),'PYTHON_39_REQUIRED')
    run, ss, out, limit=sys.argv[1:5]; step=int(ss); limit=int(limit)
    kh=sys.argv[5] if len(sys.argv)>5 else O+{'673bc60f':'/x_69d2930d','6ed2c7aa':'/x_ee227714'}[run]
    zp=sys.argv[6] if len(sys.argv)>6 else DEFAULT_Z
    zh=sys.argv[7] if len(sys.argv)>7 else DEFAULT_H
    require(re.fullmatch('[0-9a-f]{64}',zh),'ZIP_SHA_REQUIRED')
    out=Path(out); require(out.parent.resolve()==Path(O) and re.fullmatch('pb_[0-9a-f]+',out.name),'OUT_INVALID')
    require(not out.exists() and not out.is_symlink(),'OUT_EXISTS')
    require(Path(kh).parent==Path(O) and re.fullmatch('x_[0-9a-f]+',Path(kh).name),'KH_INVALID')
    job=os.environ['SLURM_JOB_ID']; nl=Path('/tmp/jjyeung/pb_'+job)
    nl.parent.mkdir(mode=0o700,exist_ok=True)
    require(not nl.parent.is_symlink() and nl.parent.stat().st_uid==os.getuid(),'TMP_PARENT_INVALID')
    nl.mkdir(mode=0o700); out.mkdir(mode=0o700)
    os.chdir(nl)
    for k in ('HOME','TMPDIR','XDG_CACHE_HOME','CLOUDSDK_LOG_DIR'): os.environ[k]=str(nl)
    log=open(nl/'pb.log','x',buffering=1)
    report=dict(run=run,step=step,job=job,verdict='ERROR',phases={},hash_seconds=None,
                zip_sha256=zh,started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
    started=time.monotonic(); active=None; child=None
    def stop(sig,frame): raise TimeoutError('LIMIT_OR_SIGNAL')
    signal.signal(signal.SIGALRM,stop); signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
    signal.alarm(max(1,limit-20))
    @contextlib.contextmanager
    def phase(name):
        nonlocal active
        active=name; t=time.monotonic(); print(name, file=log)
        try: yield
        finally:
            report['phases'][name]=dict(seconds=time.monotonic()-t,minutes=(time.monotonic()-t)/60)
    def command(args, stdout=None, capture=False):
        nonlocal child
        child=subprocess.Popen([str(a) for a in args],stdout=subprocess.PIPE if capture else (stdout or log),
                               stderr=log,start_new_session=True)
        try:
            data=child.communicate()[0]
            require(child.returncode==0,'CHILD_RC_'+str(child.returncode))
            return data.decode() if capture else None
        finally:
            if child.poll() is None:
                os.killpg(child.pid,signal.SIGKILL); child.wait()
            child=None
    def copy(src,dst):
        require(str(src).startswith(P+'/'),'POOL_SOURCE_REQUIRED')
        with open(src,'rb') as a,open(dst,'xb') as b: shutil.copyfileobj(a,b,8<<20)
    def local(path):
        p=str(path)
        for prefix,target in [(X+'/runs/',nl/'runs'),(X+'/',nl/'x'),(AS+'/',nl/'u'),(AL+'/',nl/'u'),(P+'/c7d31ddd/',nl/'v')]:
            if p.startswith(prefix): return target/safe(p[len(prefix):])
        raise ValueError('UNRESOLVED_NAMESPACE')
    rr=nl/'runs'/run; xr=X+'/runs/'+run; mr=rr/('m'+ss)
    artifacts={}; slot_before=None
    try:
        with phase('preflight'):
            require(limit>=120,'LIMIT_TOO_SHORT')
            require(sha(BW)=='e318903862396f96de3df57264e0158682b952fd3fb53ac23d876413e7b30f71','BW_SHA')
            rs=Path(O)/'r'/run; a=load(rs/'A.json'); slot_before=a
            require(all(re.fullmatch('[0-9a-f]{64}',str(a.get(k,''))) for k in ('archive_sha256','manifest_sha256')),'SLOT_DIGEST_INVALID')
            require(a.get('slot')=='A' and a.get('verified') is True and a.get('content_check')=='c1-slot-check-v1','SLOT_INVALID')
            require(type(a.get('step')) is int and a['step']==step,'SLOT_STEP_MISMATCH')
            require(re.fullmatch(r'checkpoint_\d{6}(?:_[0-9a-f]+)?',a.get('checkpoint','')),'CHECKPOINT_INVALID')
            require(re.fullmatch('[0-9]+',str(a.get('job',''))),'SOURCE_JOB_INVALID')
            queued=command(['squeue','-h','-u',str(os.getuid()),'-o','%A'],capture=True).split()
            source_ids={str(a['job']),{'673bc60f':'171377','6ed2c7aa':'172660'}.get(run,'')}
            require(not source_ids.intersection(queued),'SOURCE_JOB_ACTIVE')
            ck=a['checkpoint']; marker=Path(kh)/'o'/('gcs_'+run+'_m'+ss+'.done')
            marker_text=marker.read_text(); obj,nb,eh=marker_text.split(); nb=int(nb)
            base='gs://cmu-gpucloud-jjyeung/q8/8865619b/'+run+'_m'+ss+'.tar'
            require(obj in (base,base[5:].split('/',1)[1],base.rsplit('/',1)[1]),'MARKER_OBJECT_MISMATCH')
            require(re.fullmatch('[0-9a-f]{64}',eh) and nb>0,'MARKER_INVALID')
            cur=load(Path(kh)/'k/0.json')
            sizes=[(rs/'A.tar').stat().st_size,nb,Path(cur['venv']['file']).stat().st_size]
            need=3*sum(sizes)+(150<<30)
            report.update(input_bytes=sizes,required_tmp_bytes=need,free_tmp_bytes=shutil.disk_usage(nl).free,source_job=str(a['job']))
            require(shutil.disk_usage(nl).free>=need,'TMP_SPACE')
            require((rs/'A.sha256').read_text().split()[0]==a['archive_sha256'],'SLOT_SHA_RECORD')
            require(sizes[0]==a['bytes'],'SLOT_SIZE')
            copy(rs/'A.json',nl/'A.json'); copy(rs/'A.sha256',nl/'A.sha256'); copy(marker,nl/'e.done')
        with phase('stage'):
            copy(rs/'A.tar',nl/'a.tar'); copy(cur['venv']['file'],nl/'v.tar'); copy(zp,nl/'q.zip')
            # The SDK writes only to a private copy of its configuration.
            gc=nl/'gc'; gc.mkdir()
            gcp=Path(P)/'gcloud'
            for name in ('active_config','credentials.db','access_tokens.db','application_default_credentials.json'):
                if (gcp/name).is_file(): copy(gcp/name,gc/name)
            (gc/'configurations').mkdir()
            for f in (gcp/'configurations').glob('config_*'):
                require(f.is_file() and not f.is_symlink(),'SDK_CONFIG_LINK')
                copy(f,gc/'configurations'/f.name)
            sdk=shutil.which('gcloud'); require(sdk is not None,'SDK_MISSING')
            net=[BW,'--ro-bind','/','/','--bind',nl,nl,'--bind',gc,gcp,'--dev','/dev','--proc','/proc',
                 '--unshare-user','--uid',str(os.getuid()),'--gid',str(os.getgid()),'--',
                 'env','CLOUDSDK_CONFIG='+str(gcp),'CLOUDSDK_CORE_DISABLE_USAGE_REPORTING=true',
                 'CLOUDSDK_CORE_DISABLE_FILE_LOGGING=true',sdk,'--quiet','storage','cat']
            with open(nl/'e.tar','xb') as dst:
                for i in range(4): command(net+[base+('.part%02d-of-04'%i)],stdout=dst)
        with phase('verify'):
            for file,want in [('a.tar',a['archive_sha256']),('e.tar',eh),('v.tar',cur['venv']['sha256']),('q.zip',zh)]:
                require(sha(nl/file)==want,'SHA_'+file)
            require((nl/'e.tar').stat().st_size==nb,'EXPORT_SIZE')
            require(load(rs/'A.json')==slot_before and marker.read_text()==marker_text
                    and (rs/'A.sha256').read_text().split()[0]==a['archive_sha256'],'INPUT_CHANGED')
        with phase('extract'):
            rr.mkdir(parents=True); mr.mkdir()
            with tarfile.open(nl/'a.tar') as t:
                pick(t,'binding.json',rr/'binding.json'); b=load(rr/'binding.json')
                prep_path=b['preparation']['path']; pp=local(prep_path)
                require(pp.is_relative_to(rr/'inputs'),'PREPARATION_LOCATION')
                cfgp=pp.parent.parent/'config.json'
                for dst in [cfgp,pp,rr/ck/'complete.json']: pick(t,str(dst.relative_to(rr)),dst)
                cfg=load(cfgp); prep=load(pp); complete=load(rr/ck/'complete.json')
                require(sha(rr/ck/'complete.json')==a['manifest_sha256'],'MANIFEST_SHA')
                require(complete['schema']=='c1-checkpoint-v1' and complete['step']==step and complete['binding']==b,'MANIFEST_BINDING')
                required=[*cfg['streams'].values(),*[v['indices'] for v in prep['streams'].values() if v.get('indices')]]
                if prep.get('model'): required.append(prep['model'])
                for p in required:
                    dst=local(p['path'])
                    if dst.is_relative_to(rr) and not dst.exists(): pick(t,str(dst.relative_to(rr)),dst)
                for name in complete['files']: pick(t,ck+'/'+safe(name),rr/ck/safe(name))
            with tarfile.open(nl/'e.tar') as t:
                pick(t,'m'+ss+'/artifact.json',mr/'artifact.json'); art=load(mr/'artifact.json')
                for key in ('heads','full_weights'):
                    dst=local(art[key]['path']); require(dst.is_relative_to(mr),'EXPORT_LOCATION')
                    pick(t,str(dst.relative_to(rr)),dst)
                wf=local(art['full_weights']['path']); weights=load(wf)
                for item in [weights['index'],*weights['files']]:
                    dst=wf.parent/safe(item['name']); pick(t,str(dst.relative_to(rr)),dst)
            vdir=nl/'v'/'venvs'; vdir.mkdir(parents=True)
            with tarfile.open(nl/'v.tar') as t:
                for m in t:
                    name=safe(m.name); dst=vdir/name
                    require(name=='.' or name.split('/')[0]=='rwtrain_torch211_cu129','VENV_LAYOUT')
                    if m.isdir(): dst.mkdir(parents=True,exist_ok=True); continue
                    dst.parent.mkdir(parents=True,exist_ok=True)
                    require(dst.parent.resolve().is_relative_to(vdir.resolve()),'VENV_ESCAPE')
                    if m.issym():
                        target=(dst.parent/m.linkname).resolve()
                        require(target.is_relative_to(vdir.resolve()) or re.fullmatch('/usr/bin/python3(?:[.][0-9]+)?',str(target)),'VENV_LINK')
                        dst.symlink_to(m.linkname)
                    elif m.isfile():
                        with t.extractfile(m) as src,open(dst,'xb') as dest: shutil.copyfileobj(src,dest,8<<20)
                        dst.chmod(m.mode & 0o755)
                    else: raise ValueError('VENV_MEMBER_TYPE')
        with phase('closure'):
            unresolved=[]
            for p in required:
                dst=local(p['path'])
                if dst.exists(): require(sha(dst)==p['sha256'],'PIN_SHA'); continue
                rel=p['path'].removeprefix(AS+'/').removeprefix(AL+'/')
                candidates=[]
                if p['path'].startswith(X+'/'): candidates.append(Path(kh)/safe(p['path'][len(X)+1:]))
                candidates.append(Path(kh)/'in_small'/safe(rel))
                extras=[e for e in cur.get('extra',[]) if local(e['dest'])==dst]
                dst.parent.mkdir(parents=True,exist_ok=True)
                if extras:
                    e=extras[-1]; require(e['sha256']==p['sha256'],'EXTRA_SHA')
                    with open(dst,'xb') as f:
                        for part in e['parts']:
                            require(part.startswith(P+'/'),'POOL_SOURCE_REQUIRED')
                            with open(part,'rb') as src: shutil.copyfileobj(src,f,8<<20)
                else:
                    found=next((f for f in candidates if f.is_file()),None)
                    if found: copy(found,dst)
                    else: unresolved.append((p,dst))
                if dst.exists(): require(sha(dst)==p['sha256'],'PIN_SHA')
            if unresolved:
                copy(cur['small']['file'],nl/'s.tar'); require(sha(nl/'s.tar')==cur['small']['sha256'],'SMALL_SHA')
                with tarfile.open(nl/'s.tar') as t:
                    names={safe(m.name):m for m in t.getmembers()}
                    for p,dst in unresolved:
                        rel=p['path'].removeprefix(AS+'/').removeprefix(AL+'/')
                        candidates=[(prefix+'/'+rel).lstrip('/') for prefix in (AS,AL)]
                        matches=[n for n in candidates if n in names]
                        require(bool(matches),'SOURCE_UNRESOLVED_RUN_SURVEY')
                        pick(t,matches[-1],dst); require(sha(dst)==p['sha256'],'PIN_SHA')
        with phase('view'):
            for d in ('x','u','v','w'): (nl/d).mkdir(exist_ok=True)
            ns=[BW,'--die-with-parent','--unshare-net','--ro-bind','/','/','--dev','/dev','--proc','/proc',
                '--tmpfs','/home','--ro-bind',nl/'u',AS,'--ro-bind',nl/'u',AL,
                '--ro-bind',nl/'x',X,'--ro-bind',nl/'runs',X+'/runs',
                '--ro-bind',nl/'v',P+'/c7d31ddd','--bind',nl/'w','/w',
                '--unshare-user','--uid',str(os.getuid()),'--gid',str(os.getgid()),'--chdir','/w','--',
                'env','-i','PATH=/usr/bin:/bin','HOME=/w','TMPDIR=/w','CUDA_VISIBLE_DEVICES=',
                'OMP_NUM_THREADS=1','MKL_NUM_THREADS=1','OPENBLAS_NUM_THREADS=1','PYTHONDONTWRITEBYTECODE=1',
                'SLURM_JOB_ID='+job,'PYTHONPATH='+str(nl/'q.zip'),VP,'-s','-B']
            public=[xr+'/'+str(cfgp.relative_to(rr)),xr+'/binding.json',xr+'/'+ck+'/complete.json']
            dump(nl/'w'/'RP.json',rp_value(cfgp,rr/'binding.json',rr/ck/'complete.json',public))
            artifacts['RP.json']=nl/'w'/'RP.json'
            require(cfg['preparation']==b['preparation'],'PREPARATION_BINDING')
            wrapper="""import json,runpy,sys,time
from student_pilot import p3_provenance as p
elapsed=0.; count=0; original=p.sha256
def measured(path):
 global elapsed,count
 t=time.monotonic()
 try:return original(path)
 finally:elapsed+=time.monotonic()-t;count+=1
p.sha256=measured
try:runpy.run_module('launch_r1.p_handover_receipt',run_name='__main__')
finally:
 with open('/w/h_time.json','x') as f:json.dump(dict(seconds=elapsed,calls=count),f)
"""
            (nl/'w'/'go.py').write_text(wrapper)
        with phase('receipt'):
            command(['/usr/bin/time','-v','-o',nl/'t.txt',*ns,'/w/go.py','--run-pins','/w/RP.json',
                     '--artifact',xr+'/m'+ss+'/artifact.json','--output','/w/h.json','--trainer-commit',b['trainer_commit']])
            h=load(nl/'w'/'h.json'); require(h['schema']=='p-handover-v1' and h['step']==step,'RECEIPT_INVALID')
            artifacts['h.json']=nl/'w'/'h.json'; report['verdict']='PASS'
    except BaseException as e:
        report.update(error=type(e).__name__+':'+str(e),failed_phase=active)
        print('ERROR',type(e).__name__,file=log)
    finally:
        signal.signal(signal.SIGALRM,signal.SIG_DFL)
        signal.alarm(max(1,int(limit-(time.monotonic()-started))))
        report['elapsed_seconds']=time.monotonic()-started
        report['stage_minutes']=sum(report['phases'].get(k,{}).get('minutes',0) for k in ('stage','closure'))
        if (nl/'w/h_time.json').exists():
            report['hash_seconds']=load(nl/'w/h_time.json')['seconds']
            report['hash_minutes']=report['hash_seconds']/60
        report['peak_rss_kib']=max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
        report['peak_rss_scope']='largest process, not aggregate cgroup'
        if (nl/'t.txt').exists():
            m=re.search(r'Maximum resident set size \(kbytes\): (\d+)',(nl/'t.txt').read_text())
            if m: report['receipt_peak_rss_kib']=int(m[1])
        report['files']={k:sha(v) for k,v in artifacts.items()}
        print(report['verdict'],file=log); log.close()
        t=time.monotonic()
        for name,src in {**artifacts,'pb.log':nl/'pb.log'}.items():
            with open(src,'rb') as a,open(out/name,'xb') as b: shutil.copyfileobj(a,b)
        report['elapsed_seconds']=time.monotonic()-started
        report['phases']['publish']=dict(seconds=time.monotonic()-t,minutes=(time.monotonic()-t)/60)
        dump(nl/'pb_report.json',report)
        with open(nl/'pb_report.json','rb') as a,open(out/'pb_report.json','xb') as b: shutil.copyfileobj(a,b)
        signal.alarm(0)
    return 0 if report['verdict']=='PASS' else 1

if __name__=='__main__': sys.exit(main())
PY
