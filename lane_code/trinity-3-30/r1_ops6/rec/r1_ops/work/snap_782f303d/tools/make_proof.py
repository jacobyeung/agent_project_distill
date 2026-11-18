"""Derive the isolated production proof from the H1 driver."""
import argparse,base64,hashlib,json,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=ROOT/'out');parser.add_argument('--partition',choices=('advanced','general'));args=parser.parse_args();out=args.out
    partition=args.partition or json.loads((out/'BINDING.json').read_text())['proof_partition']
    if partition not in ('advanced','general'):raise ValueError('Invalid proof partition')
    text=(ROOT/'work/proof_parent.py').read_text()
    text=text.replace("    result = dict(status='FAIL', rc=1, job=job, production_authorized=False,", "    result = dict(partition=os.environ.get('SLURM_JOB_PARTITION'),node=os.environ.get('SLURMD_NODENAME') or os.uname().nodename,status='FAIL', rc=1, job=job, production_authorized=False,")
    text=text.replace('        host_preflight()', "        allocation=proof_allocation(authority)\n        result.update(allocation)\n        host_preflight()")
    helper='''def proof_allocation(authority):
    partition=os.environ.get('SLURM_JOB_PARTITION')
    if partition not in ('advanced','general') or partition!=authority['partition']:raise ValueError('Proof partition differs')
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='':raise ValueError('Proof must run CPU-only')
    if os.environ.get('SLURM_GPUS_ON_NODE','0') not in ('','0'):raise ValueError('CPU proof allocated GPUs')
    return dict(partition=partition,node=os.environ.get('SLURMD_NODENAME') or os.uname().nodename)

'''
    text=text.replace('def main(authority):',helper+'def main(authority):')
    text=text.replace("HOME='/home/jjyeung'", "HOME='/tmp/jjyeung'")
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
        bad=[]
        for directory,children,files in os.walk(work):
            path=Path(directory)
            if path.is_symlink() or stat.S_IMODE(path.stat().st_mode)!=0o700:bad.append(str(path))
        result['checks']['directory_modes']=dict(status='FAIL' if bad else 'PASS',bad=bad)
        required={'disk_plan','routing_selection','empty_root','temporary_paths','runtime_binaries','directory_modes','loader_audit','required_families'}
        if not required<=set(result['checks']) or any(result['checks'][k]['status']!='PASS' for k in required if k in result['checks']):
            result.update(status='FAIL',rc=result['rc'] or 1)
""")
    before="            + '\\n/bin/bash \"$ROOT/b/r.sh\" p 0\\n')"
    after="""            + '\\n/bin/bash "$ROOT/b/r.sh" p 0\\n'
            + 'export TK_KIT_HOME="$ROOT"\\nsource "$ROOT/b/c.sh"\\ntk_bwrap\\ntk_env\\ntk_pythonpath p\\n'
            + '"${BW[@]}" "$PILOT_VENV/bin/python" -B - "$X" <<P\\nfrom student_pilot.loader_audit import main\\nimport sys\\nmain(sys.argv[1])\\nP\\n')"""
    if text.count(before)!=1:raise ValueError('Parent mode-p boundary differs')
    text=text.replace(before,after)
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
exec "$PY" -I -B - "$1" <<'P'
import base64,hashlib,json,sys,zlib
raw=zlib.decompress(base64.b64decode(BLOB))
if hashlib.sha256(raw).hexdigest()!=DIGEST:raise ValueError('Embedded source differs')
authority=json.load(open(sys.argv[1]))
if authority['identity']!=IDENTITY:raise ValueError('Configuration differs')
namespace={};exec(compile(raw,'p.py','exec'),namespace)
raise SystemExit(namespace['main'](authority))
P
'''.replace('PARTITION',partition).replace('BLOB',repr(blob)).replace('DIGEST',repr(digest)).replace('IDENTITY',repr(identity))
    target=out/'proof'/('p_'+binding['run_key']+'.sh');target.write_text(script);target.chmod(0o700)
    print(json.dumps(dict(script=str(target),sha256=hashlib.sha256(script.encode()).hexdigest(),identity=identity)))
if __name__=='__main__':main()
