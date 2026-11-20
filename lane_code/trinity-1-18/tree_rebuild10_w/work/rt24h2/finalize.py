import sys,os,json,hashlib,tarfile,time,resource
from pathlib import Path
R=Path(__file__).resolve().parent
resource.setrlimit(resource.RLIMIT_AS,(7*1024**3,)*2)
resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,)*2)
sys.path.insert(0,str(R/'tt'))
from common import manifest,sha,load,put,limits,PY
limits()
assert (R/'RUN_FINISHED.json').exists(),'Incomplete single run'
checks=[];cases=[]
def check(label,v,**details):checks.append(dict(assertion=label,pass_=bool(v),**details))
source=R.parent.parent/'w24h/out/kit_n_go'
before=load(R/'checksums_before.json')
def fullmanifest(p):
 v=manifest(p);v['build_sha256']=sha(p/'BUILD.json');return v
after=dict(source=fullmanifest(source),copy=fullmanifest(R/'kit'))
put(R/'checksums_after.json',after)
for name in ['source','copy']:
 check(name+' manifest valid and unchanged',after[name]['ok'] and before[name]==after[name])
check('all copied bytes match source including BUILD',all(sha(p)==sha(source/p.relative_to(R/'kit')) for p in (R/'kit').rglob('*') if p.is_file()))
inherited=load(R/'inherited_cases.json')
prior=load(R.parent/'rt24h/RESULT.json')
check('inherited result citation unchanged',sha(Path(inherited['source']))==inherited['sha256'])
check('same kit seal as inherited results',prior['source_seal']==after['source']['seal'])
prior_cases={v['case']:v for v in prior['cases']}
check('inherited cases match authenticated rt24h RESULT',len(inherited['cases'])==14 and all(v==prior_cases.get(v['case']) and v['verdict']=='PASS' for v in inherited['cases']))
check('all b bytes match rt24h tested bytes',all(sha(p)==sha(R.parent/'rt24h/kit/b'/p.name) for p in (R/'kit/b').iterdir() if p.is_file()))
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
  ck('n_ck completion receipt matches ckstop',load(R/'cps/project/n_ck'/job/'complete.json')==q['checkpoint_marker'])
  ck('checkpoint source marker authenticated',sha(root/'p/q/r/checkpoint_100/complete.json')==q['checkpoint_marker']['marker_sha256'])
  with tarfile.open(R/'cps/project/n_ck'/job/'checkpoint_100.tar') as archive:
   ck('checkpoint tar payload bytes',all(archive.extractfile(n).read()==(root/'p/q/r/checkpoint_100'/n).read_bytes() for n in archive.getnames()))
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

for name,job,busy in [('small','2406',False),('term_busy','2407',True)]:
 root=R/'cps/cases'/name/'Q_ROOT';target=R/'cps/project/o'/job;live=target/'live'
 local=[]
 def ck(label,v,**details):local.append(dict(assertion=label,pass_=bool(v),**details))
 try:
  cmd=next(c for c in cps_commands if c['label']==('term_busy' if busy else 'pc_small'))
  ck('expected exit code',cmd['exit_code']==(124 if busy else 0))
  ck('small diagnostics published',all((live/p).is_file() for p in ['markers.json','copy.json','metrics_0.jsonl','attempt_0.json','run_0.json',job+'.steps','q.log','h.log','t.log','rooms.log']))
  ck('small mode does not publish stop checkpoint',not (live/'ckstop.json').exists() and not (R/'cps/project/n_ck'/job/'complete.json').exists())
  if busy:
   trace=(root/'shell.xtrace').read_text()
   ck('native 420-second worker wait timed out',cmd['seconds']>=420 and 'R1_COPY_WORK_WAIT_TIMEOUT' in cmd['stdout'])
   ck('timeout triggers small branch','--small' in trace and '--final' not in trace)
   ck('both copier groups stopped and waited',trace.count('kill -TERM -- -')==2 and trace.count(' wait ')>=2 and trace.rfind(' wait ')<trace.find('--small'))
   ck('small precedes evidence',trace.rfind('/b/pc.py')<trace.rfind('/b/ep.py'))
   ck('timeout status published',load(target/'r1.json')['returncode']==124)
  else:
   ck('small mode does not create export archive',not list((root/'live_spool').glob('*.tar')))
 except Exception as e:ck('case completed',False,error=repr(e))
 cases.append(dict(case='cps_'+name,verdict='PASS' if all(x['pass_'] for x in local) else 'FAIL',assertions=local,target_files=['b/pc.sh','b/pc.py','b/ep.py'] if busy else ['b/pc.py']))
for case in inherited['cases']:
 case['evidence_origin']='inherited rt24h; no rerun'
 case['evidence_source']=inherited['source']
 cases.append(case)
publication=R/'tt/cases/publication_build_raises/case_result.json'
if publication.exists():cases.append(load(publication))
else:cases.append(dict(case='publication_build_raises',verdict='FAIL',assertions=[dict(assertion='fixture reaches publishers',pass_=False)],stderr=(R/'tt/traces/publication_build_raises.stderr').read_text(),target_files=['b/ep.py','b/rd.py','b/rg.py','b/z.py']))
commands=load(R/'suite_commands.json')+cps_commands+load(R/'tt/commands.json')
executables={}
def executable(path,reason):
 p=Path(path)
 if p.is_file():executables[str(p)]=dict(sha256=sha(p),resolved=str(p.resolve()),provenance=reason)
for name in ['nice','bash','hostname','rg','sed','bwrap','setsid','timeout','sleep','true']:
 executable('/usr/bin/'+name,'shell command or sandbox executable')
executable('/bin/bash','shell interpreter');executable(PY,'requested isolated Python')
for p in (R/'kit/b').iterdir():executable(p,'verified unchanged kit bytes')
for p in [R/'driver.py',R/'finalize.py',*list((R/'cps').glob('*.py')),*list((R/'tt').glob('*.py')),R/'cps/bin/python3',R/'tt/bin/python3',R/'cps/trap_driver.sh']:
 executable(p,'harness source')
coverage={};subprocesses=[];runtime=[];starts=[];source_mismatches=[]
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
   elif kind=='runtime':runtime.append(event)
   elif kind=='python_start':starts.append(event)
check('all executed source hashes match',not source_mismatches,failures=source_mismatches)
check('recorded processes are nice and bounded',bool(runtime) and all(v['nice']>=10 and len(v['affinity'])<=4 and v['threads']<=4 for v in runtime))
check('Python starts isolated and no bytecode',bool(starts) and all('isolated=1' in v['flags'] and 'no_user_site=1' in v['flags'] and 'dont_write_bytecode=1' in v['flags'] for v in starts))
for leaf in ['pc.py','ep.py','z.py','o.py','rd.py','rg.py']:
 check('native source line coverage '+leaf,bool(coverage.get(str(R/'kit/b'/leaf))))
check('z.load screen and archive name guard executed',{12,528,542,543,544}<=coverage.get(str(R/'kit/b/z.py'),set()))
check('pc final and small branches executed',{392,408}<=coverage.get(str(R/'kit/b/pc.py'),set()))
check('all required case results produced',len(cases)==24,count=len(cases))
check('all test commands preserve expected exit codes',all(c['exit_code']=={'term':143,'usr1':138,'term_worker':7,'term_busy':124}.get(c['label'],0) for c in commands if 'exit_code' in c))
preflight=next(c for c in commands if c['label']=='tempfile_preflight')
pre=json.loads(preflight['stdout'])
check('tempfile probe works inside R at 64 MiB',preflight['exit_code']==0 and Path(pre['tmpdir']).is_relative_to(R) and pre['fsize']==[64*1024**2]*2)
# Every writable filesystem mount maps to R; the process metadata mounts stay read-only.
writable=[]
for line in pre['mountinfo'].splitlines():
 fields=line.split();mountpoint=fields[4]
 if 'rw' in fields[5].split(','):writable.append(dict(root=fields[3],mountpoint=mountpoint))
device_mounts={'/dev/null','/dev/zero','/dev/full','/dev/random','/dev/urandom','/dev/tty','/dev/pts'}
regular=[v for v in writable if v['mountpoint'] not in device_mounts]
check('sandbox writable file trees backed only by R',bool(regular) and all((Path('/scratch')/v['root'].lstrip('/')).is_relative_to(R) for v in regular),mounts=writable,device_note='Standard device bind mounts and devpts do not permit regular file creation/deletion; /dev parent is read-only.')
size=sum(p.stat().st_size for p in R.rglob('*') if p.is_file())
check('R below one GB',size<1_000_000_000,bytes_before_result=size)
failed=[c['case'] for c in cases if c['verdict']!='PASS']+[c['assertion'] for c in checks if not c['pass_']]
verdicts={}
for leaf in ['pc.sh','pc.py','ep.py','z.py','o.py','h.py','rd.py','rv.py']:
 selected=[c for c in cases if 'b/'+leaf in c.get('target_files',[])]
 verdicts[leaf]='PASS' if selected and all(c['verdict']=='PASS' for c in selected) else 'FAIL'
status='FAIL' if failed else 'PASS'
report=[
 status+(': '+', '.join(failed) if failed else ': all 10 new cases and 14 inherited tt24t2 cases pass on seal 60d24119.'),
 'pc.sh: '+verdicts['pc.sh']+'; EXIT/TERM/USR1, worker drain, both copier groups stopped/reaped, final/small branches and exit codes.',
 'pc.py: '+verdicts['pc.py']+'; live files, ckstop.json, checkpoint tar, n_ck complete.json, no-session marker, 0644 rejection and --small.',
 'ep.py: '+verdicts['ep.py']+'; materialization.json, receipt.json and refresh.json retain exact bytes after routing raises; failure code retained.',
 'z.py: '+verdicts['z.py']+'; load, archive name guard and screening execute; capsule/seal checks retained from rt24h.',
 'o.py: '+verdicts['o.py']+'; separate o.tar member/payload checks and RESULT.json publication.',
 'h.py: '+verdicts['h.py']+'; inherited rt24h/RESULT.json: h_valid, h_no_policy, h_bad_host; identical kit bytes.',
 'rd.py: '+verdicts['rd.py']+'; both routing-failure publication modes; three routing cases retained from rt24h/RESULT.json.',
 'rv.py: '+verdicts['rv.py']+'; inherited rt24h/RESULT.json: absent, PASS, identity, malformed, non-PASS and mode checks; identical kit bytes.',
 'Harness fix: the outer launcher sets RLIMIT_FSIZE=64 MiB once; children assert the inherited limit.',
 'Harness fix: TMPDIR is inside rt24h2; R-backed mounts permit deletion, other file trees remain read-only, and seccomp denies sockets.',
 'Source/copied SHA256SUMS verified before and after; kit bytes unchanged. RESULT.json records commands, exits, hashes and assertions.',
 'Run once; no case retries; synthetic fixtures only; nice>=10, <=4 threads, 7 GiB address-space limit; R stays below 1 GB.',
 'Publication uses a synthetic builder/model pin through native rg.regenerate and ep/rd publishers; tt24t2 evidence is inherited, not rerun.'
]
assert len(report)<15
(R/'REPORT.md').write_text('\n'.join(report)+'\n')
result=dict(status=status,failed=failed,file_verdicts=verdicts,host=os.uname().nodename,source=str(source),source_seal=after['source']['seal'],reference_seal=prior['reference_seal'],reference_evidence='rt24h authenticated b/ against fec34c9d; rt24h2 b/ matches rt24h byte for byte',assertions=checks,cases=cases,commands=commands,subprocess_commands=subprocesses,executable_sha256=executables,coverage={p:sorted(v) for p,v in coverage.items()},checksums_before=before,checksums_after=after,runtime_observations=runtime,python_starts=starts,bytes_before_result=size,report_lines=len(report),single_run=dict(start=load(R/'RUN_STARTED.json'),finish=load(R/'RUN_FINISHED.json'),retries=0),inherited_evidence=dict(path=inherited['source'],sha256=inherited['sha256'],cases=14,matching_source_seal=True),adaptations=[dict(scope='file-size limit',change='Set RLIMIT_FSIZE once to 64 MiB in outer driver; child limit helpers assert inheritance.'),dict(scope='tempfile',change='Remove deletion syscalls from seccomp deny list; allow creation/deletion on R-backed writable mounts, keep all other file trees read-only; TMPDIR points inside R.'),dict(scope='small-mode coverage',change='Add direct --small and a real 420-second worker timeout with synthetic sleep 440; unchanged pc.sh selects fallback.'),dict(scope='tree',change='Use the rt24h extracted source tree read-only; retain synthetic publication fixtures unchanged.')],limitations=['Routing producer and model pin are synthetic fixtures; rg.regenerate and ep/rd publishers are native unchanged kit bytes.','14 passing tt24t2 cases are inherited and authenticated against the identical source seal.','No real sessions, GCS, GPU, network or production routing build used.'],skill=dict(path='/home/jjyeung/.agents/skills/no-archaeology/SKILL.md',borderline_sentences_kept=['Harness changes and inherited rt24h evidence are explicitly required by this task.']))
put(R/'RESULT.json',result)
assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<1_000_000_000
print(json.dumps(dict(status=status,failed=failed,cases=len(cases),bytes=sum(p.stat().st_size for p in R.rglob('*') if p.is_file()),report_lines=len(report))))
