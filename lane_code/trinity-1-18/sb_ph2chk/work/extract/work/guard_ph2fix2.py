"""Replay reviewer attacks on retained fresh copies; no launches, deletion, or process termination."""
import hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; KIT=ROOT/'sb_mask_phrase'; BASE=ROOT/'work/ph2rev_probes/replays'
BASE.mkdir(parents=True,exist_ok=True)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def snap(root):
    return {str(p.relative_to(root)):(p.lstat().st_size,p.lstat().st_mtime_ns,os.readlink(p) if p.is_symlink() else sha(p) if p.is_file() else 'directory') for p in root.rglob('*')}
def prepare(kind):
    base=Path(tempfile.mkdtemp(prefix=kind+'_',dir=BASE)); kit=base/'sb_mask_phrase'
    (kit/'part2').mkdir(parents=True);(kit/'out/part2').mkdir(parents=True);(kit/'work').mkdir()
    for p in (KIT/'part2').glob('*'):
        if p.is_file(): shutil.copyfile(p,kit/'part2'/p.name)
    (kit/'run.sh').write_text((KIT/'run.sh').read_text().replace(str(KIT),str(kit)))
    (base/'payload').symlink_to(ROOT/'payload',target_is_directory=True)
    bars=kit/'part2/BARS_PART2.json'; p2=kit/'out/part2'
    if kind=='missing_bars': bars.rename(bars.with_suffix('.saved'))
    elif kind=='altered_bars': bars.write_bytes(bars.read_bytes()+b' ')
    elif kind=='bars_symlink_same_bytes':
        target=kit/'work/bars_copy.json'; bars.rename(target);bars.symlink_to(target)
    elif kind=='dangling_symlink': (p2/'PER_ITEM_PART2.jsonl').symlink_to(kit/'work/absent.jsonl')
    elif kind in ('dir_symlink','dangling_dir_symlink'):
        target=kit/'work/elsewhere'
        if kind=='dir_symlink':
            target.mkdir();(target/'PER_ITEM_PART2.jsonl').write_text('{}')
        (p2/'linked').symlink_to(target,target_is_directory=True)
    elif kind=='file_symlink':
        target=kit/'work/file.json';target.write_text('{}');(p2/'linked').symlink_to(target)
    elif kind=='output_dir_symlink':
        target=kit/'work/target';p2.rename(target);p2.symlink_to(target,target_is_directory=True)
    elif kind!='clean':
        paths={'per_item':p2/'PER_ITEM_PART2.jsonl','deep_json':p2/'a/b/c/x.json','hidden_json':p2/'.hidden.json',
               'upper_JSON':p2/'scores.JSON','csv_scores':p2/'per_item_part2.csv','decision':p2/'DECISION_PART2.json',
               'tmp_suffix':p2/'PER_ITEM_PART2.jsonl.tmp','mixed_jsonl':p2/'score.JsOnL','tsv_scores':p2/'score.TSV',
               'gz_capture':kit/'work/part2_caps/arkitscenes__41048124.json.gz',
               'killed':kit/'out/pool_part2/KILLED.json','stop':kit/'out/pool_part2/STOP.json'}
        if kind in paths:
            p=paths[kind];p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{}')
    return base,kit
cpu='/scratch/jjyeung/envs/p1cpu/bin/python'
results={};controls={}
scenarios=list(json.loads((ROOT/'work/ph2rev_probes/GUARD_ATTACK.json').read_text()))
scenarios += ['dangling_dir_symlink','file_symlink','output_dir_symlink','mixed_jsonl','tsv_scores']
for kind in scenarios:
    base,kit=prepare(kind)
    commands={
        'gate_aggregate':[cpu,'-B','part2/gate.py','aggregate'],
        'gate_capture':[cpu,'-B','part2/gate.py','capture'],
        'gate_pass':[cpu,'-B','part2/gate.py','pass'],
        'run.sh price aggregate':['bash','run.sh','part2/price.py','aggregate'],
        'price.py aggregate (no run.sh)':[cpu,'-B','part2/price.py','aggregate'],
        'launch_part2.sh capture':['bash','part2/launch_part2.sh','capture','arkitscenes/41048124'],
        'sam3_pass.py pass':[str(ROOT/'payload/environment/bin/python'),'-B','part2/sam3_pass.py','pass'],
        'launch_gpu.sh':['bash','part2/launch_gpu.sh','--node-local','0']}
    extra={}
    if kind=='clean': commands={k:v for k,v in commands.items() if k.startswith('gate_')}
    if kind=='gz_capture': commands={k:v for k,v in commands.items() if k in ('gate_capture','gate_pass','launch_part2.sh capture','sam3_pass.py pass','launch_gpu.sh')}
    if kind.startswith('fixture_escape'):
        commands={'gate_fixture':[cpu,'-B','part2/gate.py','fixture']}
        extra={'PART2_FIXTURE_DIR':'../out/part2' if kind.endswith('dotdot') else str(kit/'out/part2')}
    results[kind]={}
    for name,cmd in commands.items():
        before=snap(base)
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PART2_GO='1',PYTHONDONTWRITEBYTECODE='1',PATH='/usr/bin:/bin',
                 OPENSSL_CONF=str(ROOT/'payload/environment/ssl/openssl.cnf'),**extra)
        r=subprocess.run(cmd,cwd=kit,env=env,text=True,capture_output=True)
        after=snap(base)
        writes=sorted(set(before)^set(after)|{k for k in before.keys()&after.keys() if before[k]!=after[k]})
        refused=r.returncode!=0 and 'REFUSED' in r.stderr+r.stdout
        if kind=='clean': assert r.returncode==0 and not writes
        else: assert refused and not writes,(kind,name,r.returncode,r.stderr,writes)
        results[kind][name]=dict(command=cmd,returncode=r.returncode,refused=refused,writes=writes,message=r.stderr.strip())
    print(kind,len(commands),'PASS',flush=True)
inputs=[Path(__file__),ROOT/'work/ph2rev_probes/GUARD_ATTACK.json',ROOT/'work/ph2rev_probes/guard_attack.py',KIT/'run.sh',*sorted((KIT/'part2').glob('*.py')),*sorted((KIT/'part2').glob('*.sh'))]
record=dict(status='PASS',results=results,refusal_count=sum(r['refused'] for rs in results.values() for r in rs.values()),writes=0,
            controls='Clean gates accept; gz_capture is a legitimate aggregate input, so producer entry points must refuse it.',
            input_sha256={str(p):sha(p) for p in inputs})
(ROOT/'out/GUARD_PH2FIX2.json').write_text(json.dumps(record,indent=1)+'\n')
