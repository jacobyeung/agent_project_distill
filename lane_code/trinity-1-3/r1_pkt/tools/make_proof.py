"""Derive the isolated production proof from the H1 driver."""
import argparse,base64,hashlib,inspect,json,zlib
from derive_deployment import validate_switches
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=ROOT/'out');parser.add_argument('--partition',choices=('advanced','general','bootstrap'));args=parser.parse_args();out=args.out
    partition=args.partition or json.loads((out/'BINDING.json').read_text())['proof_partition']
    if partition not in ('advanced','general','bootstrap'):raise ValueError('Invalid proof partition')
    text=(ROOT/'work/proof_parent.py').read_text()
    text=inspect.getsource(validate_switches)+'\n'+text
    needle="        cfg = load(kh/launch['config']['file'])"
    if text.count(needle)!=1:raise ValueError('Parent config boundary differs')
    text=text.replace(needle,needle+'\n        validate_switches(cfg)')
    text=text.replace("    result = dict(status='FAIL', rc=1, job=job, production_authorized=False,", "    result = dict(partition=os.environ.get('SLURM_JOB_PARTITION'),node=os.environ.get('SLURMD_NODENAME') or os.uname().nodename,status='FAIL', rc=1, job=job, production_authorized=False,")
    text=text.replace('        host_preflight()', "        allocation=proof_allocation(authority)\n        result.update(allocation)\n        host_preflight()")
    helper='''def proof_allocation(authority):
    partition=os.environ.get('SLURM_JOB_PARTITION')
    if partition not in ('advanced','general','bootstrap') or partition!=authority['partition']:raise ValueError('Proof partition differs')
    if partition not in authority.get('allowed_partitions',('advanced','general','bootstrap')):raise ValueError('Proof partition is not authorized')
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='':raise ValueError('Proof must run CPU-only')
    if os.environ.get('SLURM_GPUS_ON_NODE','0') not in ('','0'):raise ValueError('CPU proof allocated GPUs')
    return dict(partition=partition,node=os.environ.get('SLURMD_NODENAME') or os.uname().nodename)

'''
    text=text.replace('def main(authority):',helper+'def main(authority):')
    helper='''def directory_modes(work):
    bad=[]
    for directory,children,files in os.walk(work):
        path=Path(directory)
        if path.is_symlink() or stat.S_IMODE(path.stat().st_mode)!=0o700:bad.append(str(path))
    return dict(status='FAIL' if bad else 'PASS',bad=bad)

'''
    text=text.replace('def main(authority):',helper+'def main(authority):')

    text=text.replace("def host_preflight():", "def host_preflight():\n    inventory = {}")
    text=text.replace("    for name in ('/bin/bash', '/usr/bin/python3') + HOST_TOOLS:", "    for name in ('bash', 'python3', 'sed', 'head', 'gzip', 'nice', 'ionice', 'which', 'env') + HOST_TOOLS:")
    text=text.replace("            raise ValueError('Production host program unavailable: '+name)", "            raise ValueError('Production host program unavailable: '+name)\n        path = Path(shutil.which(name, path=HOST_PATH)).resolve()\n        inventory[name] = dict(path=str(path), sha256=sha(path))\n    inventory['driver'] = dict(path=str(Path(sys.executable).resolve()), sha256=sha(Path(sys.executable).resolve()))\n    return inventory")
    text=text.replace("        assert sha(bun/'jb.sh') == authority['wrapper_sha256']","        assert sha(bun/'jb.sh') == authority['wrapper_sha256']\n        for name,expected in authority['bundle_files'].items():\n            if sha(bun/name)!=expected:raise ValueError('Proof bundle differs: '+name)")
    text=text.replace('def create_work(work):','def create_work(work, run_key):')
    text=text.replace("'tmp/jjyeung/a_17c4ffa4'", "'tmp/jjyeung/a_'+run_key")
    text=text.replace("work/'tmp/jjyeung/a_17c4ffa4/root'", "work/('tmp/jjyeung/a_'+authority['run_key']+'/root')")
    text=text.replace('        host_preflight()', "        binaries = host_preflight()")
    text=text.replace('        create_work(work)', "        create_work(work, authority['run_key'])")
    text=text.replace("        physical = work/'tmp/jjyeung/a_17c4ffa4/runs/17c4ffa4'", "        physical = work/('tmp/jjyeung/a_'+authority['run_key']+'/runs/'+authority['run_key'])")
    text=text.replace("        rs = Path(launch['persistent_run_root'])", "        if launch['run_directory']!='/tmp/jjyeung/a_'+authority['run_key']+'/runs/'+authority['run_key']:raise ValueError('Run is outside its own temporary root')\n        if list((work/'slots').iterdir()) or (work/('tmp/jjyeung/a_'+authority['run_key']+'/root/.stamp')).exists():raise ValueError('Proof root is not empty')\n        rs = Path(launch['persistent_run_root'])")

    text=text.replace("        bw = kit_bwrap(kh)", "        bw = kit_bwrap(kh)\n        binaries['bwrap'] = dict(path=str(Path(bw).resolve()),sha256=sha(Path(bw).resolve()))")
    helper='''def export_plan(bundle,cfg,run_key):
    milestones=sorted(set(cfg['recipe']['milestones']))
    stopped=bool(cfg['recipe'].get('export_at_stop'))
    count=len(milestones)+int(stopped)
    if cfg['checkpoint_disk_guard']['planned_weight_exports']!=count:raise ValueError('Export disk count differs')
    names=['m'+str(i) for i in milestones]+(['mstop','mstopB','mstopC'] if stopped else [])
    expected=sorted('q8/8865619b/'+run_key+'_'+name+'.tar.part%02d-of-04'%i for name in names for i in range(4))
    if sorted((bundle/'e.txt').read_text().splitlines())!=expected:raise ValueError('Export destinations differ')
    return dict(planned_weight_exports=count,milestones=milestones,stop_fallback_names=3 if stopped else 0,reserved_part_destinations=len(expected))

'''
    text=text.replace('def main(authority):',helper+'def main(authority):')
    text=text.replace("        bw = kit_bwrap(kh)","        result['export_destinations']=export_plan(bun,cfg,authority['run_key'])\n        bw = kit_bwrap(kh)")
    helper='''def temporary_paths(args,kh,work):
    mounts=[]
    for i,arg in enumerate(args):
        if arg!='--bind':continue
        source=Path(args[i+1]);target=args[i+2]
        if source!=kh/'o' and not source.resolve().is_relative_to(work.resolve()):raise ValueError('Ambient writable dependency')
        mounts.append(dict(source=str(source),target=target))
    return dict(status='PASS',work_root=str(work),writable_mounts=mounts,
        external_receipt_directory=str(kh/'o'),read_only_inputs='Explicit kit, bundle, staged source parts and runtime binaries')

'''
    text=text.replace('def main(authority):',helper+'def main(authority):')
    anchor="        args = command(bw, kh, work, rs)"
    if text.count(anchor)!=1:raise ValueError("Parent command boundary differs")
    text=text.replace(anchor,anchor+"\n        paths=temporary_paths(args,kh,work)")
    text=text.replace("        result.update(config_identity=identity(cfg),", "        result.update(checks=dict(temporary_paths=paths,empty_root=dict(status='PASS',path=str(work)),runtime_binaries=dict(status='PASS',binaries=binaries)),config_identity=identity(cfg),")
    text=text.replace("        result.update(execute(args, script, kh/'o'/(job+'.proof.log'), lambda: verify_prepared(kh, physical)))", """        outcome=execute(args, script, kh/'o'/(job+'.proof.log'), lambda: verify_prepared(kh, physical))
        result.update(outcome)
        audit_path=physical/'inputs/a.json'
        if audit_path.exists():
            audit=load(audit_path)
            if audit['original_config_identity']!=authority['identity']:raise ValueError('Loader proof identity differs')
            if sha(physical/'inputs/l.json')!=audit['checks']['loader_audit']['pin']['sha256']:raise ValueError('Loader audit bytes differ')
            result['checks'].update(audit['checks'])
            result['absent_on_P']=audit['checks']['required_families']['absent_on_P']
        else:
            result['checks']['loader_audit']=dict(status='NOT_RUN')
        result['checks']['directory_modes']=directory_modes(work)
        required={'disk_plan','routing_selection','empty_root','temporary_paths','runtime_binaries','directory_modes','loader_audit','required_families'}
        if not required<=set(result['checks']) or any(result['checks'][k]['status']!='PASS' for k in required if k in result['checks']):
            result.update(status='FAIL',rc=result['rc'] or 1)
""")
    before="            + '\\n/bin/bash \"$ROOT/b/r.sh\" p 0\\n')"
    after="""            + '\\n/bin/bash "$ROOT/b/r.sh" p 0\\n'
            + 'export TK_KIT_HOME="$ROOT"\\nsource "$ROOT/b/c.sh"\\n'
            + 'export TK_RUNS_DIR="$NR"\\n'
            + 'export TK_JOBDIR="${S%/root}/jobs/${SLURM_JOB_ID:?}.proof"\\n'
            + 'umask 077\\nmkdir -p -m 700 "${TK_JOBDIR%/*}"\\nmkdir -m 700 "$TK_JOBDIR"\\n'
            + 'read -r proof_record proof_record_sha < <(tk_current record)\\n'
            + 'sha_is "$S/c7d31ddd/anyhost/$proof_record_sha.json" "$proof_record_sha"\\n'
            + 'export R1_RUNTIME_RECORD="$P/anyhost/$proof_record_sha.json"\\n'
            + 'tk_bwrap\\ntk_env\\ntk_pythonpath p\\n'
            + '"${BW[@]}" "$PILOT_VENV/bin/python" -B - "$X" <<P\\nimport json, os, sys\\nfrom pathlib import Path\\nfrom v import tree\\ncur = json.loads((Path(sys.argv[1])/"k/0.json").read_text())\\ntree({"path": cur["record"]["file"], "sha256": cur["record"]["sha256"]}, os.environ["TRAINER"], cur["commit"])\\nsys.path.insert(0, os.environ["TRAINER"])\\nfrom student_pilot.loader_audit import main\\nmain(sys.argv[1])\\nP\\n')"""
    if text.count(before)!=1:raise ValueError('Parent mode-p boundary differs')
    text=text.replace(before,after)
    if json.loads((out/'BINDING.json').read_text()).get('continuation'):
        helper='''def resume_fixture(kh,work):
    import importlib.util
    spec=importlib.util.spec_from_file_location('c0',kh/'b/c0.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result,_,_=module.fixture(work/'c0',load(kh/'k/a0.json'),load(kh/'k/7.json'))
    return result

'''
        text=text.replace('def main(authority):',helper+'def main(authority):')
        text=text.replace('        result.update(outcome)',"        result.update(outcome)\n        result['checks']['resume_pointer']=resume_fixture(kh,work)")
        text=text.replace("required={'disk_plan'","required={'resume_pointer','disk_plan'")
    text=text.replace('def main(authority):', (ROOT/'tools/proof_tail.py').read_text()+'\n\ndef main(authority, rehearsal_root=None):')
    text=text.replace("os.environ.get('SLURM_JOB_NAME') != authority['job_name']", "os.environ.get('SLURM_JOB_NAME') != ('a15_cot_ap05b8ac6a' if rehearsal_root else authority['job_name'])")
    text=text.replace("destination = kh/'o'/(job+'.proof.json')", "destination = kh/'o'/(job+('.rehearsal.json' if rehearsal_root else '.proof.json'))")
    text=text.replace("status='RUNNING', job=job", "status='REHEARSAL_RUNNING' if rehearsal_root else 'RUNNING', job=job")
    anchor="        script = namespace_probe(bw) + program((bun/'jb.sh').read_text(), (kh/'job.sh').read_text())"
    text=text.replace(anchor, anchor+"\n        if rehearsal_root:\n            if authority['partition']!='general':raise ValueError('Rehearsal requires general')\n            stage=Path(rehearsal_root)\n            if not stage.is_absolute() or stage.is_symlink() or not stage.is_dir():raise ValueError('Staged root unavailable')\n            stage=stage.resolve()\n            if not str(stage).startswith('/tmp/jjyeung/'):raise ValueError('Rehearsal requires node-local staged root')\n            script=rehearsal_program((bun/'jb.sh').read_text(), (kh/'job.sh').read_text(),kh,bw)")
    text=text.replace('        paths=temporary_paths(args,kh,work)', "        if rehearsal_root:\n            index=args.index('/bin/bash')\n            args[index:index]=['--ro-bind',str(stage),'/tmp/jjyeung/a_'+authority['run_key']+'/root']\n        paths=temporary_paths(args,kh,work)")
    start=text.index('        outcome=execute(args, script,')
    end=text.index('    except BaseException as exc:',start)
    original=text[start:end]
    text=text[:start]+"        if rehearsal_root:\n            result.update(rehearsal_execute(args,script,kh,work,job,authority['run_key']))\n        else:\n"+''.join('    '+line+'\n' for line in original.splitlines())+text[end:]
    anchor="    result.setdefault('finished_epoch', time.time())"
    text=text.replace(anchor,"    if rehearsal_root:\n        result.update(rehearsal=True,admission_executed=False,staged_source=str(rehearsal_root))\n        result.setdefault('steps',dict(preflight='FAIL'))\n        if result['status']!='REHEARSAL_OK':result.update(status='REHEARSAL_FAIL',rc=result['rc'] or 1)\n"+anchor)
    source=out/'proof/p.py';source.write_text(text)
    binding=json.loads((out/'BINDING.json').read_text());identity=binding['config_identity']
    blob=base64.b64encode(zlib.compress(text.encode(),9)).decode();digest=hashlib.sha256(text.encode()).hexdigest()
    script='''#!/bin/bash -p
#SBATCH -A mt01 -p PARTITION -N1 --ntasks=1 -c 48 --mem=800G -t 04:00:00
#SBATCH --no-requeue
set -euo pipefail
umask 077
export PATH=/usr/local/bin:/usr/bin:/bin CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
PY=$(command -v python3)
exec "$PY" -I -B - "$@" <<'P'
import base64,hashlib,json,sys,zlib
raw=zlib.decompress(base64.b64decode(BLOB))
if hashlib.sha256(raw).hexdigest()!=DIGEST:raise ValueError('Embedded source differs')
authority=json.load(open(sys.argv[1]))
if authority['identity']!=IDENTITY:raise ValueError('Configuration differs')
namespace={};exec(compile(raw,'p.py','exec'),namespace)
if len(sys.argv)==2:
    stage=None
elif len(sys.argv)==4 and sys.argv[2]=='--rehearsal':
    stage=sys.argv[3]
    if not stage:raise ValueError('Rehearsal staged root must be nonempty')
else:
    raise ValueError('Expected AUTHORITY [--rehearsal STAGED_ROOT]')
raise SystemExit(namespace['main'](authority, stage))
P
'''.replace('PARTITION',partition).replace('BLOB',repr(blob)).replace('DIGEST',repr(digest)).replace('IDENTITY',repr(identity))
    target=out/'proof'/('p_'+binding['run_key']+'.sh');target.write_text(script);target.chmod(0o700)
    print(json.dumps(dict(script=str(target),sha256=hashlib.sha256(script.encode()).hexdigest(),identity=identity)))
if __name__=='__main__':main()
