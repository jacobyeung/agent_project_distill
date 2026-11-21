from pathlib import Path
import json,hashlib,re
J=Path.cwd();D=J/'work/build24m4z12';O=J/'out';E=O/'e3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
scope=json.loads((D/'SCOPE.json').read_text());delta=json.loads((D/'DELTA.json').read_text());baseline=json.loads((D/'BASELINE_FILES.json').read_text())
files=['b/o.py','b/pc.py','b/pc.sh','k/y.json','SHA256SUMS.txt','BUILD.json']
def entry(p,name,old=None):
 assert p.stat().st_size<5_000_000
 return dict(name=name,relative_path=str(p.relative_to(J)),local_path=str(p),bytes=p.stat().st_size,sha256=sha(p),mode=format(p.stat().st_mode&511,'04o'),baseline_sha256=old,action='replace' if old else 'add')
normal=[entry(O/'kit_n'/n,'n/'+n,baseline['work/build24/kits/n'][n]['sha256']) for n in files]+[entry(O/'jn3.sh','jn3.sh')]
go=[entry(O/'kit_n_go'/n,'n_go/'+n,baseline['out/kit_n_go'][n]['sha256']) for n in files]
e3=[entry(E/n,'e3/'+n) for n in ('e3.sh','e3.py','observe.py','run.sh','k.tgz','pins.json','trinity.sh','trinity.py','readback.py','SESSION_NAMES.template.list','STATUS_NAMES.template.list')]
for suffix,rows,armed in (('',normal,False),('_GO',go,True),('_E3',e3,False)):
 stem='UPLOADS_24M4Z12'+suffix
 write(O/(stem+'.json'),dict(build='24m4z12',files=rows,GO=armed,uploaded=False,launched=False,training_gate='NO-GO',total_bytes=sum(r['bytes'] for r in rows),tree_sha256=delta['tree_sha256'],baseline='24m4y2 reviewed overlay',kit_delta_vs_z10=['b/pc.py','SHA256SUMS.txt','BUILD.json']))
 (O/(stem+'.list')).write_text(''.join(r['name']+'\n' for r in rows))
# Refresh the bundle/pin hashes in the existing usage table without changing any executable.
p=E/'E3_USAGE.md';s=p.read_text()
for r in e3:
 pattern=r'^\| '+re.escape(r['name'])+r' \|.*$'
 s=re.sub(pattern,'| '+r['name']+' | '+str(r['bytes'])+' | '+r['sha256']+' |',s,flags=re.M)
p.write_text(s)
report="Both review findings pass offline on the sealed kits. The build used the real shell EXIT finalizer and the strict resumable sink for the old/new controls.\n\n| Finding | Fail-before: 24m4z10 | Pass-after: 24m4z12 | Logs |\n|---|---|---|---|\n| 1. Ordinary checkpoint drain | No pending ordinary checkpoint obtains a receipt after either an explicit or nominal stop. | Steps 10 and 2 upload in that order after step 30's stop checkpoint, the stop export, other exports, logs, archive and the durable u-log prefix settle. A failed stop also releases the queue. Interrupted ordinary parts resume from their acknowledged Range; the reserve blocks further ordinary work. A fresh live pass drains the same settled queue. | work/build24m4z12/new_verified/RESULT.json and each case's shell.log, sink/events.jsonl; PRIORITY_CONTROLS.json |\n| 2. Live log screening | The probe token survives unchanged in live/j2.log, live/j2.err and the other four log tails. | Every live log tail passes through the kit's sealed screen with k/g.json and b/wh.json; the transformed token replaces the probe before publication. | work/build24m4z12/new_verified/RESULT.json; after_success/x/o/41/live/ |\n\nOrdinary checkpoints remain held until the final priority pass has attempted each publication. A snapshot binds settlement to the stop request, nominal-stop state and checkpoint/export/report markers. Both the copier and each writer request reject stale settlement; a new export interrupts an in-flight ordinary part before the next request. The ordinary budget ends at the earlier of archive_due and data_deadline. The 150-second reserve and allocation deadline remain unchanged.\n\nThe u publication retains its sealed four-part design: its durable prefix settles before ordinary checkpoints, and its reserved final tail records the subsequent retries after the final pass. The new ordering does not freeze that final tail early or alter completed parts. A final checkpoint failure is never relabeled as an ordinary checkpoint. Empty or completed ordinary queues do not add a checkpoint phase.\n\nAll required suites pass: current (8), archive (4), legacy (5), ENOSPC/refusal/recovery, signals, wrapper forwarding/race/exception, core (7), advanced (9), real EXIT, final-loop, strict-sink malformed-range negatives, both tgcs controls, E3 offline (17 checks), Trinity fake-session, set_stop and stop-policy. Evidence: work/build24m4z12/ALL_SEALED.json, SUITES_SEALED.json, e3_sealed/RESULT.json, trinity_sealed/RESULT.json and findings_sealed/RESULT.json. FAILURES.json preserves the setup/assertion failures and their output; no unresolved gate remains.\n\nThe full comparison hashes all 192,840 members of baseline archive 15cdc1273ff7a1c794c79c895505d08a5a1e325b21029d3606eac999f5efa181. Only b/o.py, b/pc.py, b/pc.sh, k/y.json and seals differ in each N kit. Against 24m4z10, only b/pc.py and seals differ. Q, QD, rcj and both trees are unchanged; the tree seal is 9d2bbb8ad209d91e21e56121785f62b0dddf3c8d9f14db8d23daf6dcd1d3591b. See DELTA.json and SCOPE.json.\n\nE3's k.tgz and pins match the final GO=false kit. e3.py, observe.py, run.sh, e3.sh, trinity.py, trinity.sh and readback.py are byte-identical to 24m4z10. The supplied tgcs_900004 evidence has 16 receipts whose hashes match their local part bytes, including u; ckstop reused ck00. The unchanged transport/session files preserve the stated carry for job 173966; this build made no remote request and claims no new real-service rate or resume result.\n\nThe stop setting remains 3,600 seconds. The planning rule remains 2 x (W + B/R) + 150 <= stop_before_seconds - 15, using measured write time W, bytes B and real rate R; the 1.5x variant requires qualifying real resume evidence. No training or numerical stop-window approval is inferred from offline fixtures.\n\n| Kit | Old seal | New seal |\n|---|---|---|\n"
report+=''.join('| '+r['kit']+' | '+r['old']+' | '+r['new']+' |\n' for r in scope['seals'])
report+='\ny.json, gc.py, o.py, pc.sh, the session-cache format and session handling are unchanged. SHA256 values follow; session rows hash the exact unchanged function source.\n\n| Unchanged file/source | SHA256 |\n|---|---|\n'
report+=''.join('| '+k+' | '+v+' |\n' for k,v in scope['unchanged_files'].items())
report+=''.join('| pc.py:'+k+' | '+v+' |\n' for k,v in scope['unchanged_session_source_sha256'].items())
report+='\nThe old/new descriptions above are required controls, retained as evidence rather than revision history.\n'
(O/'ENOSPC_24M4Z12.md').write_text(report)
short=[
'Both review findings pass offline through the real EXIT path and strict sink.',
'Ordinary checkpoints drain newest first after priority settlement, resume interrupted parts and stop at the reserve.',
'Every live log tail uses the sealed screen; the raw probe token never reaches X on the new kit.',
'All required suites pass, including E3 offline, Trinity fake-session and set_stop; FAILURES.json retains resolved output.',
'Only pc.py and seals differ from z10; the full y2 archive diff stays within the four allowed files and seals.',
'E3 bundle and pins match the final kit; e3.py, observe.py, run.sh and e3.sh are unchanged.',
'The supplied 16 real-service receipt hashes match local bytes; this build made no remote request or training submission.',
'ENOSPC_24M4Z12.md and UPLOADS_24M4Z12{,_GO,_E3}.json/.list provide evidence, seals, hashes and exact upload files.'
]
(O/'BUILD24M4Z12_REPORT.md').write_text('\n'.join(short)+'\n')
print('Reports and upload manifests written')
