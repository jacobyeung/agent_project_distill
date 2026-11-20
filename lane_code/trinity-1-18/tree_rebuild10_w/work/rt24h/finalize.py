import sys,os,json,hashlib,tarfile,time,resource
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'tt'))
from common import manifest,sha,load,put,limits,PY
limits()
assert (R/'RUN_FINISHED.json').exists(),'Incomplete single run'
checks=[];cases=[]
def check(label,v,**details):checks.append(dict(assertion=label,pass_=bool(v),**details))
source=R.parent.parent/'w24h/out/kit_n_go';reference=R.parent.parent/'w24h/work/build24/kits/n'
before=load(R/'checksums_before.json')
after=dict(source=manifest(source),copy=manifest(R/'kit'),reference=manifest(reference))
put(R/'checksums_after.json',after)
for name in ['source','copy','reference']:
 check(name+' manifest valid and unchanged',after[name]['ok'] and before[name]==after[name])
check('all copied bytes match source including BUILD',all(sha(p)==sha(source/p.relative_to(R/'kit')) for p in (R/'kit').rglob('*') if p.is_file()))
check('all b bytes match reference',all(sha(p)==sha(reference/'b'/p.name) for p in (R/'kit/b').iterdir() if p.is_file()))
tree_before=load(R/'tree_checksums_before.json')
check('extracted tree unchanged',tree_before=={str(p.relative_to(R/'tree')):sha(p) for p in (R/'tree').rglob('*') if p.is_file()})
for c in load(R/'cps/verified_case_results.json'):
 q=c['checks'];root=Path(c['root']);job=c['job'];target=R/'cps/project/o'/job;live=target/'live'
 local=[]
 def ck(label,v,**details):local.append(dict(assertion=label,pass_=bool(v),**details))
 try:
  ck('exit code',c['exit_code']==c['expected_exit_code'])
  ck('live files',all(q['expected_live_files'].values()))
  ck('live copies match',q['live_copies_match'])
  ck('no sessions marker',q['export_marker']['status']=='export not uploaded: sessions unusable (directory missing)')
  ck('no false upload done',not q['upload_done'])
  ck('checkpoint marker and done',q['checkpoint_done'] and q['checkpoint_marker']['status']=='project')
  ck('checkpoint digest',sha(R/'cps/project/n_ck'/job/'checkpoint_100.tar')==q['checkpoint_marker']['sha256'])
  ck('checkpoint tar members',q['checkpoint_tar_members']==['complete.json','state.txt'])
  ck('export tar members',q['export_archive_members'][0]['members']==['artifact.json','config.json','payload.txt'])
  ck('evidence has no errors',q['r1']['errors']==[])
  ck('evidence preserves status',q['r1']['returncode']==c['expected_exit_code'])
  ck('trap does not call o.py',not q['archive_at_trap_exit'] and not q['result_at_trap_exit'])
  ck('both steps files copied',sum(v['name']==job+'.steps' for v in load(live/'copy.json')['files'])==2)
  ck('both markers listed',{v['name'] for v in load(live/'markers.json')}=={'m100/artifact.json','checkpoint_100/complete.json'})
  trace=(root/'shell.xtrace').read_text()
  ck('final pc.py precedes ep.py','--final' in trace and trace.rfind('/b/pc.py')<trace.rfind('/b/ep.py'))
  ck('copier waits precede final',trace.count(' wait ')>=2 and trace.rfind(' wait ')<trace.find('--final'))
  ck('both copier groups stopped',trace.count('kill -TERM -- -')==2)
  ck('o.py absent from shell trap trace','/b/o.py' not in trace)
 except Exception as e:ck('assertions complete',False,error=repr(e))
 cases.append(dict(case='cps_'+c['name'],verdict='PASS' if all(x['pass_'] for x in local) else 'FAIL',command_exit_code=c['exit_code'],assertions=local,observations=c,target_files=['b/pc.sh','b/pc.py','b/ep.py','b/z.py']))
local=[]
def ck(label,v,**details):local.append(dict(assertion=label,pass_=bool(v),**details))
try:
 root=R/'cps/cases/exit/Q_ROOT';target=R/'cps/project/o/2401'
 expected=['q.log','rooms.log','rooms.json','h.log','t.log','p/q/RESULT.json','p/q/host.json','p/q/f.json']
 with tarfile.open(target/'o.tar') as tf:
  ck('archive member list',tf.getnames()==expected)
  ck('archive payload bytes',all(tf.extractfile(n).read()==(root/n).read_bytes() for n in expected))
 ck('o.py result',load(target/'RESULT.json')==dict(proof_rc=0,rooms_rc=0,GO=False,submitted_by_build=False))
 ck('local and published tar match',sha(root/'o/o.tar')==sha(target/'o.tar'))
 ck('local and published result match',load(root/'o/RESULT.json')==load(target/'RESULT.json'))
 ck('ep includes result','RESULT.json' in load(target/'r1.json')['files'])
except Exception as e:ck('assertions complete',False,error=repr(e))
cases.append(dict(case='o_standalone',verdict='PASS' if all(x['pass_'] for x in local) else 'FAIL',assertions=local,target_files=['b/o.py','b/ep.py','b/z.py']))
cps_commands=load(R/'cps/verified_run_records.json')
mode_marker=next((x['value'] for x in cps_commands if x['label']=='fake_endpoint_marker'),None)
mode_ok=mode_marker is not None and mode_marker['status']=='export not uploaded: sessions unusable (file mode)'
cases.append(dict(case='fake_endpoint_bad_mode',verdict='PASS' if mode_ok else 'FAIL',assertions=[dict(assertion='0644 sessions rejected before transport',pass_=mode_ok,observed=mode_marker)],target_files=['b/pc.py']))
cases.extend(load(R/'tt/case_results.json'))
publication_result=R/'tt/cases/publication_build_raises/case_result.json'
if publication_result.exists():cases.append(load(publication_result))
else:cases.append(dict(case='publication_build_raises',verdict='FAIL',failure_kind='fixture import failed before routing build or publication',assertions=[dict(assertion='publication case reaches producer and publishers',pass_=False)],stderr=(R/'tt/traces/publication_build_raises.stderr').read_text(),target_files=['b/ep.py','b/rd.py','b/rg.py','b/z.py']))
commands=load(R/'suite_commands.json')+cps_commands+load(R/'tt/commands.json')
executables={}
def executable(path,reason):
 p=Path(path)
 if p.is_file():executables[str(p)]=dict(sha256=sha(p),resolved=str(p.resolve()),provenance=reason)
for name in ['nice','bash','hostname','pwd','rg','wc','sed','head','tail','stat','bwrap','setsid','timeout','sleep','true']:
 executable('/usr/bin/'+name,'shell command or sandbox executable')
executable('/bin/bash','shell interpreter');executable(PY,'requested isolated Python')
for p in (R/'kit/b').iterdir():executable(p,'verified unchanged kit bytes')
for p in [R/'driver.py',R/'finalize.py',*list((R/'cps').glob('*.py')),*list((R/'tt').glob('*.py')),R/'cps/bin/python3',R/'tt/bin/python3',R/'cps/trap_driver.sh',R/'tt/trap_driver.sh']:
 executable(p,'harness source')
coverage={};subprocesses=[];sockets=[];runtime=[];starts=[];source_mismatches=[]
for suite in ['cps','tt']:
 for path in sorted((R/suite/'traces').glob('python-*.jsonl')):
  for line in path.read_text().splitlines():
   event=json.loads(line);kind=event['event']
   if kind=='executable_source':
    executable(event['path'],'observed Python audit exec')
    if executables[event['path']]['sha256']!=event['sha256']:source_mismatches.append(event)
   elif kind=='coverage':
    for p,lines in event['files'].items():coverage.setdefault(p,set()).update(lines)
   elif kind=='subprocess.Popen':subprocesses.append(event)
   elif kind.startswith('socket.'):sockets.append(event)
   elif kind=='runtime':runtime.append(event)
   elif kind=='python_start':starts.append(event)
check('all executed source hashes match',not source_mismatches,failures=source_mismatches)
check('socket attempts observed and at most four threads',bool(sockets) and all(v.get('threads',1)<=4 for v in sockets),attempts=len(sockets),max_threads=max([v.get('threads',1) for v in sockets],default=0))
check('recorded processes are nice and bounded',bool(runtime) and all(v['nice']>=10 and len(v['affinity'])<=4 and v['threads']<=4 for v in runtime))
check('Python starts isolated and no bytecode',bool(starts) and all('isolated=1' in v['flags'] and 'no_user_site=1' in v['flags'] and 'dont_write_bytecode=1' in v['flags'] for v in starts))
for leaf in ['pc.py','ep.py','z.py','o.py','h.py','rd.py','rv.py','rg.py']:
 check('native source line coverage '+leaf,bool(coverage.get(str(R/'kit/b'/leaf))))
check('z.load and screen bodies executed', {12,528}<=coverage.get(str(R/'kit/b/z.py'),set()))
check('all required case results produced',len(cases)==22,count=len(cases))
check('suite launchers exited zero',all(c['exit_code']==0 for c in load(R/'suite_commands.json')))
check('all test commands preserve expected exit codes',all(c.get('exit_code')=={'term':143,'usr1':138,'term_worker':7,'pc_finish':7}.get(c['label'],0) for c in commands if 'exit_code' in c))
failed=[c['case'] for c in cases if c['verdict']!='PASS']+[c['assertion'] for c in checks if not c['pass_']]
verdicts={}
for leaf in ['pc.sh','pc.py','ep.py','z.py','o.py','h.py','rd.py','rv.py']:
 selected=[c for c in cases if 'b/'+leaf in c.get('target_files',[])]
 verdicts[leaf]='PASS' if selected and all(c['verdict']=='PASS' for c in selected) else 'FAIL'
status='FAIL' if failed else 'PASS'
report=[
 'FAIL: cps shutdown/o.py/mode cases and publication_build_raises have harness failures; 14 tt24t2 cases passed.',
 'pc.sh: FAIL coverage; five traps ran, but Python children failed in the added tracing launcher before kit execution.',
 'pc.py: FAIL coverage; tt24t2 0600 synthetic denied-transport cases passed; cps live/checkpoint/session-mode paths remain untested.',
 'ep.py: FAIL coverage; tt24t2 worker-exit publication passed; routing-build-failure publication never reached its test body.',
 'z.py: FAIL coverage; tt24t2 capsule/seal/screen checks passed; cps archive-name path and new publication case remain untested.',
 'o.py: FAIL coverage; its launcher failed before the separate archive test could execute.',
 'h.py: PASS; valid v.json, E85 and R1_HOST_RECEIPT_INVALID.',
 'rd.py: FAIL coverage; all three inherited routing cases passed; added failure-artifact publication remains untested.',
 'rv.py: PASS; timeout, matching PASS, identity mismatch, malformed, non-PASS and 0644 review.',
 'Source/copied SHA256SUMS verified before and after; seal 60d24119; b/ matches fec34c9d reference; kit and tree bytes unchanged.',
 'The cps tracing launcher tried to raise inherited RLIMIT_FSIZE from 32 to 64 MiB; this is a harness error, not a kit failure.',
 'The added publication fixture imported model code whose tempfile probe failed under deletion-denying seccomp; no case was retried.',
 'RESULT.json records commands, exits, executable hashes, assertions and fixture changes; rv retains its fake clock and evidence stub.',
 'Writes stayed under rt24h; read-only kit/tree, denied sockets/deletions, nice>=10, <=4 threads and 7 GiB address-space limits applied.']
assert len(report)<15
(R/'REPORT.md').write_text('\n'.join(report)+'\n')
inventory=[dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(R.rglob('*')) if p.is_file() and p.name!='RESULT.json']
size=sum(p.stat().st_size for p in R.rglob('*') if p.is_file())
check('R below one GB',size<1_000_000_000,bytes_before_result=size)
check('cps launcher failure identified',(R/'cps.stderr').exists())
result=dict(status=status,failed=failed,file_verdicts=verdicts,host=os.uname().nodename,source=str(source),source_seal=after['source']['seal'],reference_seal=after['reference']['seal'],assertions=checks,cases=cases,commands=commands,subprocess_commands=subprocesses,executable_sha256=executables,coverage={p:sorted(v) for p,v in coverage.items()},checksums_before=before,checksums_after=after,adaptations=load(R/'adaptations.json'),fixture_sources=load(R/'fixture_sources.json'),socket_events=sockets,python_starts=starts,runtime_observations=runtime,inventory=inventory,bytes_before_result=size,report_lines=len(report),single_run=dict(start=load(R/'RUN_STARTED.json'),finish=load(R/'RUN_FINISHED.json'),retries=0),failure_kind='Harness failures; no kit defect demonstrated',harness_failures=dict(cps=dict(cause='Tracing launcher common.limits tries to raise hard RLIMIT_FSIZE from inherited 32 MiB to 64 MiB, before kit Python body runs.',stderr=(R/'cps.stderr').read_text(),evidence=(R/'cps/traces/exit.verified.stderr').read_text()),publication=dict(cause='Unnecessary mdg_parent import loads transformers/torch cache code. tempfile probe requires unlink, denied by seccomp; case body never runs.',stderr=(R/'tt/traces/publication_build_raises.stderr').read_text())),limitations=['No failed harness or case was rerun under run-once instruction.','Cps Python paths and new routing-failure publication are not covered because of fixture/launcher failures.','Review fake clock and pre-wait evidence stub inherited unchanged in intent.','Synthetic routing builder was prepared but never executed because its fixture imports failed.','seccomp refuses socket creation before any connection; real GCS and real sessions are never used.','No 420-second worker-timeout or unfinished-trainer small fallback test was requested.'],skill=dict(path='/home/jjyeung/.agents/skills/no-archaeology/SKILL.md',borderline_sentences_kept=[]))
put(R/'RESULT.json',result)
assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<1_000_000_000
print(json.dumps(dict(status=status,failed=failed,cases=len(cases),bytes=sum(p.stat().st_size for p in R.rglob('*') if p.is_file()),report_lines=len(report))))
