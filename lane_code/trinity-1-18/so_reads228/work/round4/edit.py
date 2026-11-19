from pathlib import Path
import json,gzip,hashlib,sys,subprocess
K=Path('/scratch/jjyeung/orch_n30/so_reads228/work/round4/kit')
sys.path.insert(0,str(K))
from common228 import canonical,sha
from runtime_registry228 import list_headers
plan=json.loads((K/'STAGE_PLAN.json').read_text());stage=Path(plan['stage_root']);root=stage/'private_rt'
plan['private_runtime']=str(root)
receipt_names={
 'sj/orch_cd/devs1_direct':[],
 'sj/orch_cd/rv_merge_fix':['A10b/src/orchard_h10/vendor/trace_runtime.py'],
 'sj/orch_cd/legs1_reads':['A10b/src/orchard_h10/vendor/trace_runtime.py','A10b/src/orchard_h10/vendor/export_stage.py'],
 'sj/envs/p1cpu':['A10b/src/orchard_h10/vendor/orchard_stage.py'],
 'sj/uv-python/cpython-3.12.13-linux-x86_64-gnu':['A10b/src/orchard_h10/vendor/orchard_stage.py'],
 'm/ap/90da7ac2':['A10b/src/orchard_h10/vendor/ORCHARD_ASSETS.json'],
 'm/ap/19252904':['evidence/q/env.json','A10b/src/orchard_h10/vendor/orchard_stage.py'],
 'fsw':[], 'x/pull.py':[], 'x/need_frames.txt':[]}
registry={}
for name,receipts in receipt_names.items():
 kind='record_only' if name.startswith('x/') else 'runtime'
 if name.startswith('sj/'):dest='/scratch/jjyeung/'+name[3:]
 elif name.startswith('m/ap/'):dest='/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/'+name[5:]
 elif name=='fsw':dest='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'
 else:dest=None
 receipts=['A10b/src/orchard_h10/vendor/orchard_job.py']+receipts if kind=='runtime' else receipts
 registry[name]=dict(kind=kind,host_path=str(root/name),namespace_path=dest,members=0,
  receipts=[dict(path=p,bytes=(K/p).stat().st_size,sha256=sha(K/p)) for p in receipts],
  basis=('Package namespace and cited receipts; membership cross-checked against coordinator lists.' if receipts else
         'Coordinator runtime lists and fix4 ruling; no package receipt for this staging helper.'),
  bind_evidence=None if kind=='record_only' else 'A10b/src/orchard_h10/vendor/orchard_job.py:128-131')
 if name=='sj/orch_cd/devs1_direct':registry[name]['basis']='Coordinator runtime list supplies this subtree; package SJ bind supplies its in-namespace path. No narrower package receipt was found.'
registry['sj/uv-python/cpython-3.12.13-linux-x86_64-gnu']['additional_namespace_path']='/home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu'
plan['runtime_registry']=registry
listing_base=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts/r228_lists/runtime')
(K/'evidence/runtime').mkdir(exist_ok=True)
summary={};total=0
for group in plan['runtime_archives']:
 name=group['id'];path=K/'evidence/runtime'/(name+'.list')
 path.write_bytes(gzip.open(listing_base/(name+'.list.gz'),'rb').read())
 rows=list_headers(path);expanded=sum(r['bytes'] for r in rows if r['type']=='0');total+=expanded
 group.update(destination=str(root),namespace_map={n:str(root/n) for n in registry},expanded_bytes=expanded,
   member_list=dict(path=str(path.relative_to(K)),bytes=path.stat().st_size,sha256=sha(path)),member_headers_sha256=canonical(rows))
 counts={}
 for row in rows:
  found=[p for p in registry if row['name']==p or row['name'].startswith(p+'/')]
  assert found,row
  prefix=max(found,key=len);counts[prefix]=counts.get(prefix,0)+1;registry[prefix]['members']+=1
 summary[name]=dict(members=len(rows),expanded_file_bytes=expanded,namespaces=counts,list_sha256=sha(path),source_gzip_sha256=sha(listing_base/(name+'.list.gz')))
plan['budget']['runtime_expanded_bytes']=total
plan['budget']['estimated_peak_bytes']+=total-plan['budget']['runtime_expanded_allowance_bytes']
plan['budget']['basis']='Input/runtime part pins and expanded runtime sizes read from coordinator tar lists; 5 GB code/cache/return allowance is estimated. Includes the shared SAM3 conservatively; it is never read. Runtime refusal cap remains 40 GB; actual footprint counts private_rt.'
plan['environment']['local_base_env']=str(root/'m/ap/19252904/e')
plan['environment']['local_base_python']=str(root/'sj/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12')
plan['environment']['control_python']=plan['environment']['local_base_python']
plan['environment']['namespace']['runtime_root']=str(root)
text=json.dumps(plan,indent=2,sort_keys=True)+'\n';text=text.replace('/reads228/kit/','/reads228/kit2/')
(K/'STAGE_PLAN.json').write_text(text)
(K/'RUNTIME_LISTS.json').write_text(json.dumps(dict(groups=summary,total_members=sum(v['members'] for v in summary.values()),expanded_file_bytes=total),indent=2,sort_keys=True)+'\n')
p=K/'stage228.py';s=p.read_text()
s=s.replace("result[part['path']]=local(part['target'])", "result[part['path']]=local(part['target'])")
a=s.index('    # Scan only the runtime trees named by archives')
b=s.index('    products=prepare_products',a)
s=s[:a]+"    if plan.get('private_runtime'):roots.add(plan['private_runtime'])\n"+s[b:]
s=s.replace("roots=[host_path(logical,plan),STAGE,root,HERE]", "roots=[host_path(logical,plan),STAGE,root,HERE]\n    if plan.get('private_runtime'):roots.append(plan['private_runtime'])")
s=s.replace("runtime_members=extraction['runtime_members'])", "runtime_members=extraction['runtime_members'],\n                non_runtime_namespaces=[dict(namespace=n,**row) for n,row in plan.get('runtime_registry',{}).items() if row['kind']=='record_only'])")
s=s.replace('from runtime228 import extract_runtime\n', 'from runtime228 import extract_runtimes\n        from runtime_registry228 import validate_registry\n')
s=s.replace("        result=dict(files={},groups={});total=0\n", "        registry=validate_registry(plan)\n        print(utc()+' preflight all runtime archives (no extraction writes)',file=sys.stderr)\n")
a=s.index("        for group in plan['runtime_archives']:\n            print(utc()+' extracting '")
b=s.index("        write(STAGE/'RUNTIME_EXTRACTION.json',result)",a)
s=s[:a]+"        try:\n            result=extract_runtimes(plan['runtime_archives'],mapping,limit=limit)\n        except (Refusal,OSError,ValueError) as error:\n            write(STAGE/'STAGE_CHECK.json',dict(passed=False,phase='runtime_extraction',error=str(error),\n                private_runtime=plan['private_runtime'],registry=registry,utc=utc()))\n            raise\n        result.update(plan_sha256=sha(HERE/'STAGE_PLAN.json'),registry=registry,utc=utc())\n"+s[b:]
p.write_text(s)
p=K/'namespace228.py';s=p.read_text()
s=s.replace("root=local(Path(plan['stage_root'])/'runtime')", "root=local(plan.get('private_runtime',Path(plan['stage_root'])/'private_rt'))")
s=s.replace("    if not (root/'sj').is_symlink() or (root/'sj').resolve()!=Path('/scratch/jjyeung'):\n        raise Refusal('Run --check-namespace to establish the package sj bind')", "    if (root/'sj').is_symlink() or not (root/'sj').is_dir():\n        raise Refusal('Private runtime sj must be a real directory')")
s=s.replace("    # Keep the package binds; overlay only its logical root with this kit's private copy.\n    argv[0]=str(BWRAP)", "    # Keep package runtime binds. Expose only named control paths, never private_rt/x.\n    argv[0]=str(BWRAP)\n    for path in [HERE]+[Path(plan['stage_root'])/n for n in ('prepare','operator_probe','namespace_probe')]:\n        path=local(path)\n        if path.is_symlink():raise Refusal('Control bind is a symlink')\n        argv+=['--bind',str(path),str(path)]\n    argv+=['--chdir',str(HERE)]")
s=s.replace("    return namespace_command(plan)+[inputs['python'],'-B','-I',str(HERE/'operator228.py')]+list(args)", "    argv=namespace_command(plan)\n    if args and args[0]=='--execute':\n        out=local(Path(args[1]).parent.parent)\n        if not out.is_dir() or out.is_symlink():raise Refusal('Operator output must be a real directory')\n        argv+=['--bind',str(out),str(out)]\n    return argv+[inputs['python'],'-B','-I',str(HERE/'operator228.py')]+list(args)")
a=s.index("    sj=root/'sj'",s.index('def check_namespace'));b=s.index('    if plan.get(\'private_logical\'):',a)
s=s[:a]+"    for name in ('sj','fsw','m/ap'):\n        path=root/name\n        if path.is_symlink():raise Refusal('Private runtime namespace source is a symlink')\n        path.mkdir(parents=True,exist_ok=True)\n    for name in ('prepare','operator_probe','namespace_probe'):\n        path=local(Path(plan['stage_root'])/name)\n        if path.is_symlink():raise Refusal('Control source is a symlink')\n        path.mkdir(parents=True,exist_ok=True)\n"+s[b:]
s=s.replace("mappings.extend(((AP,Path(plan['stage_root'])/'runtime/m/ap'),(FSW,Path(plan['stage_root'])/'runtime/fsw')))","runtime=Path(plan.get('private_runtime',Path(plan['stage_root'])/'private_rt'))\n        mappings.extend(((str(plan['stage_root']),Path(plan['stage_root'])),\n                         (AP,runtime/'m/ap'),(FSW,runtime/'fsw'),('/scratch/jjyeung',runtime/'sj')))")
p.write_text(s)
p=K/'operator228.py';s=p.read_text().replace("    from orchard_h10 import runner", "    from orchard_h10.common import install_process_guard\n    install_process_guard(out)\n    from orchard_h10 import runner");p.write_text(s)
for name in ('coordinator228.sh','run228.sh','read228.sh','compare228.sh'):
 p=K/name;s=p.read_text().replace('/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12',plan['environment']['local_base_python'])
 s=s.replace('/reads228/kit','/reads228/kit2');p.write_text(s)
p=K/'tests/run_tests.sh';s=p.read_text().replace('work/round3/test_runs','work/round4/test_runs')
s=s.replace('nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$test_dir/test_bootstrap36.py"', '''bootstrap_python=/scratch/jjyeung/envs/p1cpu/bin/python
if [[ -x /usr/bin/python3 ]] && /usr/bin/python3 -I -s -B -c 'import sys; sys.exit(sys.version_info[:3] != (3,6,8))'; then
  bootstrap_python=/usr/bin/python3
fi
nice -n 10 "$bootstrap_python" -I -s -B -c 'import sys; print("bootstrap interpreter: " + sys.version)'
nice -n 10 "$bootstrap_python" -I -s -B "$test_dir/test_bootstrap36.py"''')
s+='\ndate -u\nnice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -S -B "$test_dir/test_target_refusal.py"\n';p.write_text(s)
print(json.dumps(dict(runtime_expanded_file_bytes=total,members=sum(x['members'] for x in summary.values()),estimated_peak_bytes=plan['budget']['estimated_peak_bytes']),sort_keys=True))
Path('/scratch/jjyeung/orch_n30/so_reads228/work/STATUS.md').write_text(subprocess.check_output(['date','-u'],text=True)+'Implementing fix4 under work/round4/kit. out_round3 preserves delivery. Runtime registry derives bind destinations from sealed namespace and receipts; all-member preflight precedes every runtime write. Target runtime bodies remain unavailable locally.\n')
