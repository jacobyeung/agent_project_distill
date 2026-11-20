import json,hashlib,tarfile,ast,resource,os
from pathlib import Path
T=Path(__file__).resolve().parent
resource.setrlimit(resource.RLIMIT_AS,(7*1024**3,7*1024**3))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
cases=read(T/'verified_case_results.json')
checks={}
for c in cases:
    q=c['checks'];root=Path(c['root']);live=T/'project/o'/c['job']/'live'
    checks[c['name']]={
      'exit_code':c['exit_code']==c['expected_exit_code'],
      'live_files':all(q['expected_live_files'].values()),
      'copies_match':q['live_copies_match'],
      'not_uploaded_marker':q['export_marker']['status']=='export not uploaded: sessions unusable (directory missing)',
      'no_false_upload_done':not q['upload_done'],
      'checkpoint_marker_and_done':q['checkpoint_done'] and q['checkpoint_marker']['status']=='project',
      'checkpoint_digest':sha(T/'project/n_ck'/c['job']/'checkpoint_100.tar')==q['checkpoint_marker']['sha256'],
      'checkpoint_members':q['checkpoint_tar_members']==['complete.json','state.txt'],
      'export_members':q['export_archive_members'][0]['members']==['artifact.json','config.json','payload.txt'],
      'evidence_no_errors':q['r1']['errors']==[],
      'evidence_status':q['r1']['returncode']==c['expected_exit_code'],
      'trap_has_no_o_py_output':not q['archive_at_trap_exit'] and not q['result_at_trap_exit'],
      'steps_root_and_home_copied':sum(v['name']==c['job']+'.steps' for v in read(live/'copy.json')['files'])==2,
      'markers_list_both':{v['name'] for v in read(live/'markers.json')}=={'m100/artifact.json','checkpoint_100/complete.json'}
    }
root=Path(cases[0]['root']);target=T/'project/o/2401'
o_result=read(target/'RESULT.json')
with tarfile.open(target/'o.tar') as tf:
    members=tf.getnames()
    expected=['q.log','rooms.log','rooms.json','h.log','t.log','p/q/RESULT.json','p/q/host.json','p/q/f.json']
    o_bytes=all(tf.extractfile(n).read()==(root/n).read_bytes() for n in expected)
o_checks={'result':o_result,'result_expected':o_result==dict(proof_rc=0,rooms_rc=0,GO=False,submitted_by_build=False),'archive_members':members,'archive_members_expected':members==expected,'archive_payloads_match':o_bytes,'local_and_published_tar_match':sha(root/'o/o.tar')==sha(target/'o.tar'),'local_and_published_result_match':read(root/'o/RESULT.json')==read(target/'RESULT.json'),'ep_includes_result':'RESULT.json' in read(target/'r1.json')['files']}
after=read(T/'checksums_after.json')
assert all(all(v.values()) for v in checks.values())
assert all(o_checks[k] for k in ('result_expected','archive_members_expected','archive_payloads_match','local_and_published_tar_match','local_and_published_result_match','ep_includes_result'))
assert all(v['ok'] for v in after.values() if isinstance(v,dict))
assert after['all_copy_bytes_equal'] and after['reference_b_bytes_equal']
assert not any(p.name=='sess.json' for p in T.rglob('*'))
assert not any(p.name=='__pycache__' for p in (T/'kit').rglob('*'))
report=[
'FAIL step 3: the refused-endpoint transport case is untested; all copier shutdown assertions pass.',
'The source and copied kit retain seal c992c930; b/ matches reference seal 240f8c17; every checked digest matches.',
'EXIT, TERM and USR1 return 0, 143 and 138; TERM and USR1 with a fake worker preserve its return codes 7 and 0.',
'Each case produces matching live logs, both .steps inputs, metrics, run/attempt JSON and marker listings.',
'Each case writes gcs_m100.json with “export not uploaded: sessions unusable (directory missing)”; no .done falsely claims upload.',
'Each case writes ckstop.json and a verified checkpoint_100.tar plus n_ck/<job>/complete.json.',
'pc.sh stops both copier groups, runs pc.py --final, then ep.py; z.py loads and screens evidence.',
'The trap never calls o.py. Decoded k/j.json calls it at line 438; its separate test produces verified o.tar and RESULT.json.',
'There is no dry-run/no-session CLI switch. Missing sessions trigger pc.py’s built-in error branch; --sessions only selects a file.',
'The synthetic 127.0.0.1:1 file has mode 0644: --sessions rejects its mode cleanly before transport; a valid file would be copied to sess.json.',
'Read-only host mounts and a read-only kit confine persistent writes to T; seccomp denies sockets and connect; no sess.json exists.',
'All tests inherit nice 10, four-CPU affinity, one-thread library settings and a 7 GiB address-space limit; T is below 500 MB.',
'RESULT.json contains the command ledger, exit codes, assertions, call-path description, setup failures, limitations and complete file inventory.'
]
assert len(report)<15
(T/'REPORT.md').write_text('\n'.join(report)+'\n')
commands=read(T/'command_ledger.json')
subcommands=[]
for filename in ('run_records.json','actual_run_records.json','executed_run_records.json','final_run_records.json','verified_run_records.json'):
    subcommands.append({'record_file':filename,'records':read(T/filename)})
details={
 'status':'FAIL',
 'failing_step':3,
 'failure_kind':'requested coverage incomplete, not a demonstrated copier defect',
 'reason':'No valid-session refused-local transport test: the kit has no dry/no-session CLI switch; its valid-session branch necessarily creates and copies live_spool/private/sess.json, prohibited by the task. Missing-directory and bad-file-mode handling passed.',
 'copier_shutdown_assertions':'PASS',
 'host':'trinity-1-18',
 'source':'/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24e/out/kit_n_go',
 'source_seal':'c992c930ac90adeba32496c7508c9e6c89ab5353bc46cfed7182b73c286b1d3e',
 'reference_seal':'240f8c17ffd5a2e800bdc4684ff404d528b87aaf012e7f49f1ff25f3ac6ddd27',
 'checksums_before':read(T/'checksums_before.json'),
 'checksums_after':after,
 'cases':cases,'assertions':checks,'o_py':o_checks,
 'call_path':{
  'job.sh':'Installs pc.sh traps and starts two setsid copier processes. A worker pipeline runs b/x.py and b/l.py; the batch shell waits for TK_WORK_PID. The real job.sh is read only, never submitted or executed because it requests GPUs, 48 threads and training.',
  'pc.sh':'EXIT uses $?; TERM passes 143 signal; USR1 passes 138 signal. tk_live_finish ignores TERM/USR1 and removes EXIT. If TK_WORK_PID is set during a signal, sr.py waits up to 420s and signals matching descendants; a clean wait replaces the signal status with worker status. It TERM-signals copier process groups, waits up to 5s each through sr.py, may KILL, then waits/reaps. With waited=0 it runs timeout --signal=TERM --kill-after=5 150 python3 -B -I -s pc.py KIT ROOT JOB --final; otherwise --small. It then runs ep.py KIT ROOT JOB status and exits status. Publication errors are suppressed with || true.',
  'pc.py':'Reads k/p.json (n_root), k/n.json (stored cfg, otherwise unused), k/y.json (object keys). Creates target/o/JOB/live, target/o/gcs_claims and Q_ROOT/live_spool. Small pass copies bounded logs, metrics, attempts, run JSON and .steps. It archives immutable m*/artifact.json exports. Missing sessions produce export-not-uploaded markers; usable sessions are copied into private/sess.json before invoking gc.py split with four parts and four workers. Final pass archives the latest completed checkpoint locally when space exceeds size plus 50 GiB, otherwise tries ckstop upload.',
  'ep.py':'Uses z.load on k/p.json, k/g.json, b/wh.json and BUILD.json. z.screen screens log tails and JSON fields. It locks target/o/JOB/.l, atomically publishes diagnostics and r1.json, then publishes routing receipts if present. It does not invoke o.py or any child process.',
  'ep.sh':'Separate evidence-only trap helper; starts ep.py --loop via setsid, signals/waits workload and evidence PIDs on shutdown, publishes ep.py, then exits status. It is not sourced by job.sh; pc.sh is.',
  'sr.py':'Reads /proc descendant lists, state, command lines, environment and caught-signal masks; forwards USR1 only to matching rv.py or rank-bearing u.py workers, then waits for exit. Fake workers only sleep and exit; targeted descendant forwarding is not exercised.',
  'z.py':'load validates encoded JSON payload digests. screen and name_guard screen evidence and archive member names. Other resolver/bootstrap code is not run. bootstrap would stage named inputs and decoded k/j.json, then launch /bin/bash through launch_shell.',
  'o.py':'Invoked by decoded k/j.json line 438, separately from tk_live_finish. Archives eight existing diagnostic paths as a gzip tar under Q_ROOT/o, copies o.tar to n_root/o/JOB, writes RESULT.json with proof_rc, rooms_rc, GO=false, submitted_by_build=false, and copies it to the target.',
  'externals':[
   {'scope':'job.sh startup (not executed)','commands':['date +%s','readlink -f','dirname','mkdir -p','python3 b/v.py','python3 b/x.py','python3 b/l.py'],'builtins':['export','set','umask','source','cd','wait']},
   {'scope':'pc.sh tested path','commands':['setsid python3 -B -I -s b/pc.py ... --loop','setsid python3 -B -I -s b/pc.py ... --loop-small','python3 -B -I -s b/sr.py PID 420 signal (worker case)','python3 -B -I -s b/sr.py PID 5','timeout --signal=TERM --kill-after=5 150 python3 -B -I -s b/pc.py ... --final (or --small)','python3 -B -I -s b/ep.py ...'],'builtins':['trap','local','kill','wait','true','exit']},
   {'scope':'pc.py usable sessions only (not executed)','commands':['sys.executable -B b/gc.py split live_spool/private/sess.json OBJECT ARCHIVE 4 4'],'effects':['Copies sessions capabilities','gc.py creates up to four process workers or four fallback threads','HTTPS PUT via http.client','session receipt JSONL sidecar']},
   {'scope':'ep.py, sr.py, o.py and z.load/screen/name_guard','commands':[],'note':'Python standard library filesystem, hash, lock, tar and process-signal operations; no external program.'},
   {'scope':'z.launch_shell (not executed)','commands':['/bin/bash decoded-k-j.sh']},
   {'scope':'test harness','commands':['bwrap','/bin/bash trap_driver.sh','sleep 0.2','sleep 0.3','requested isolated Python interpreter'],'note':'All inherit nice 10; Python shim only selects the requested interpreter and adds -I -s -B; kit bytes remain unchanged.'}
  ]
 },
 'decoded_inputs':{n: {'path':'decoded/'+n,'sha256':sha(T/'decoded'/n)} for n in ['k_p.json','k_n.json','k_y.json','k_g.json','b_wh.json','BUILD.json','k_j.sh']},
 'session_tests':{'cli_flags':['--loop','--loop-small','--final','--small','--sessions'],'dry_or_no_session_switch':None,'implicit_missing_session_branch':'pc.py session_bytes -> ValueError(directory missing) -> send records export not uploaded and returns','synthetic_endpoint':'https://127.0.0.1:1/refused','synthetic_file':'project/n_s/fake-endpoint.json','file_mode':'0644 (intentionally unusable)','synthetic_marker':read(target/'live/gcs_m100.json'),'transport_exercised':False,'real_sessions_read_or_copied':False},
 'confinement':{'persistent_writes':'T only','aliases':{'/project/community/jjyeung/okh7/x_22c714e1':str(T/'project'),'/tmp':str(T/'tmp')},'host_mounts':'/usr /bin /lib /lib64 /etc /scratch read-only, T writable, T/kit read-only','namespace_root':'Read-only; /proc and private /dev read-only. Namespace-only mount points are ephemeral, not host writes. /dev/null writes are shell redirections, not persistent files.','network':'seccomp denies socket(41) and connect(42); no network connection attempted by verified branches','deletion':'seccomp also denies unlink(87), rmdir(84), unlinkat(263); no deletion command issued','audit_limit':'strace denied PTRACE_TRACEME, so confinement is enforced by mounts rather than an observed syscall write log.'},
 'resources':{'nice':10,'cpu_affinity_limit':4,'library_threads':1,'address_space_limit_bytes':7*1024**3,'per_file_limit_bytes':32*1024**2,'training':False,'admission':False,'fixture_population':False,'model':False,'gpu':False,'agents':False,'git':False,'ssh':False},
 'setup_and_run_once_accounting':{'setup_failures':['Shell quoting syntax error before copying','bwrap network namespace blocked by denied NETLINK_ROUTE socket','strace ptrace denied before executing the kit','Installed bwrap does not support --clearenv; no kit execution','Read-only root lacked /project mount point; no kit execution','First mount layout used nodev /dev: shell traps ran, but every Python process failed during interpreter initialization; no copier Python body ran'],'functional_run':'Each of five distinct shutdown scenarios ran once after interpreter preflight passed. Direct o.py, ep.py and --sessions mode-rejection checks each ran once with a working interpreter. No rerun of cluster-killed work occurred.','strict_run_once_limit':'Shell trap setup attempts did occur before the successful functional run; retained logs disclose them.'},
 'limitations':['No refused-local transport execution and no real upload; valid-session path conflicts with never-copy-sess.json constraint.','No 420-second worker-timeout or --small fallback exercise.','No targeted rv.py/u.py descendant signal forwarding; no training process exists.','o.py is a worker epilogue, not a trap child. Its output checks are separate.','The source/reference kit is unmodified; only the synthetic path aliases differ at runtime.'],
 'commands':commands,'subprocess_commands':subcommands,
 'command_record_note':'Tool-issued shell commands and returned exit codes are retained. Shell builtins and kit-issued commands are additionally captured in each shell.xtrace. Trace-tool setup failures never launched the kit. Ledger serialization commands are represented by their operation and stored data, avoiding recursive self-embedding.',
 'finalization_commands':[
  {'command':'nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B '+str(T/'finalize.py'),'exit_code':1,'note':'Report validation compared RESULT.json bytes after ep.py normalized JSON formatting. Corrected the test to compare parsed values; kit unchanged.'},
  {'command':'nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -','exit_code':0,'note':'Changed only finalize.py assertion from byte equality to parsed JSON equality and recorded the failed assertion.'},
  {'command':'nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -','stdin':'Serialize command ledger in 16000-character chunks into command_ledger.json (one write then appends).','exit_code':0},
  {'command':'nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -','stdin':'Write the source stored in finalize.py.','exit_code':0},
  {'command':'nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B '+str(T/'finalize.py'),'exit_code':0}
 ],
 'serialization_tool_error':'One oversized exec command was rejected by the exec service with Argument list too long before creating a process; the ledger was written in bounded chunks.',
 'report_lines':len(report),'skill':'/home/jjyeung/.agents/skills/no-archaeology/SKILL.md',
 'inventory':[]
}
# The report describes findings; chronological setup diagnostics belong in this JSON ledger.
for p in sorted(T.rglob('*')):
    if p.is_file():
        details['inventory'].append({'path':str(p.relative_to(T)),'bytes':p.stat().st_size,'sha256':sha(p)})
details['inventory'].append({'path':'RESULT.json','bytes':None,'sha256':None,'note':'Self-record; digest intentionally omitted to avoid self-reference.'})
details['total_bytes_excluding_RESULT']=sum(x['bytes'] or 0 for x in details['inventory'])
out=T/'RESULT.json'
for _ in range(5):
    raw=json.dumps(details,indent=2)+'\n'
    size=len(raw.encode())
    details['inventory'][-1]['bytes']=size
    details['total_bytes']=details['total_bytes_excluding_RESULT']+size
out.write_text(json.dumps(details,indent=2)+'\n')
assert sum(p.stat().st_size for p in T.rglob('*') if p.is_file())<500_000_000
assert len((T/'REPORT.md').read_text().splitlines())<15
assert read(out)['status']=='FAIL'
print(json.dumps({'status':'FAIL','failing_step':3,'copier_shutdown_assertions':'PASS','report_lines':len(report),'files':len(details['inventory']),'bytes':sum(p.stat().st_size for p in T.rglob('*') if p.is_file()),'report':str(T/'REPORT.md'),'result':str(out)}))
