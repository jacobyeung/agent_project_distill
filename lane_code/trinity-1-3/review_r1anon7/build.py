import json,re,difflib,hashlib,os
from pathlib import Path
EV=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events')
W=Path('/scratch/jjyeung/orch_n30/r1_ops/work');L=Path('/scratch/jjyeung/orch_n30/review_r1anon7')
sha=lambda b:hashlib.sha256(b).hexdigest()
prev=json.loads((EV/'review_r1anon6/ANON_SCAN_R1C.json').read_text())
okprev=json.loads((EV/'review_r1anon6/ANON_OK.json').read_text())
A=(W/'drv_c1/scan1.out').read_text().splitlines();Braw=(W/'drv_c1/scan1_c3.out').read_bytes();B=Braw.decode().splitlines()
assert sha(Braw)=='53f131077a25af99cf5ca91b6b76b9526aa9e384392f7613680d7aaedf2165d4'
op=re.compile(prev['regex']['operator'].split(' (')[0])
pr=re.compile(prev['regex']['precedent'].rsplit(' (',1)[0])
sm=difflib.SequenceMatcher(None,A,B,autojunk=False)
amap={};changed=[]
for o,i1,i2,j1,j2 in sm.get_opcodes():
  if o=='equal':
    for k in range(i2-i1): amap[i1+k+1]=j1+k+1
  else: changed+=list(range(j1+1,j2+1))
hits=[]
for h in prev['hits']:
  n=amap[h['line']]; assert B[n-1]==h['text']==A[h['line']-1]
  g=dict(h); g.update(file='drv_c1/scan1_c3.out',line=n,prior_line='drv_c1/scan1.out:%d'%h['line'],
    why=h['why']+'; carried from review_r1anon6 (ANON_SCAN_R1C.json, drv_c1/scan1.out:%d), line byte-identical in scan1_c3.out'%h['line'])
  hits.append(g)
hitlines={h['line'] for h in hits};hittext={h['text'] for h in hits}
dup=0;unacc=[]
for i,l in enumerate(B,1):
  if op.search(l) or pr.search(l):
    if i in hitlines: continue
    if l in hittext: dup+=1
    else: unacc.append(i)
cl=[]
for j in changed:
  cl.append(dict(file='drv_c1/scan1_c3.out',line=j,text=B[j-1],regex_hit=bool(op.search(B[j-1]) or pr.search(B[j-1])),**{'class':'clean new name/argv/command line'}))
assert not any(c['regex_hit'] for c in cl)
counts={}
for h in hits: counts[h['class']]=counts.get(h['class'],0)+1
print(counts,dup,unacc,changed)
def sec(t):
  return B.index(t)+1
sections=dict(new=[2,sec('INHERITED NAMES INSIDE VERIFIED 0700 TREES / INHERITED STAGING LOCATORS')-1],
  inh=[sec('INHERITED NAMES INSIDE VERIFIED 0700 TREES / INHERITED STAGING LOCATORS')+1,sec('SEALED SCRIPT COMMAND LINES FOR ARGV REVIEW (NO SESSION CONTENTS)')-1],
  cmd=[sec('SEALED SCRIPT COMMAND LINES FOR ARGV REVIEW (NO SESSION CONTENTS)')+1,sec('GREP NEW NAMES')-1],
  grep_new=[sec('GREP NEW NAMES')+1,sec('GREP INHERITED NAMES / ARGV (account for each under the ruling)')-1],
  grep_inh=[sec('GREP INHERITED NAMES / ARGV (account for each under the ruling)')+1,len(B)-3])
R1758='events/r1_ops/20261117T1758Z_ORCH_ANSWER_anon_hits_exempt_submit_proof1.md'
new_content=[
 dict(id='E8',class_='exempt-content',member='p_05b8ac69.sh (decoded embedded source 90f96822, in-script pin equal)',
  matches='student_pilot at :130 (inherited loader_audit import, now after v.tree trainer check), :255,:256 (rehearsal replace of that import), :262 (student_pilot.p3_provenance import); vqa at :263 (stream key); .split at :244',
  why='Python source carried in a 0700 BUN member; bash tail and inner Python reach the interpreter on stdin (execute(): runner(args, input=script); inner "python -B - $X <<P"), never argv, env, job name or log text; ORCH 1758Z; r1anon6 E5/E7 precedent'),
 dict(id='E9',class_='exempt-content',member='s.sh canary branch (lines 26-119)',
  matches='vqa at :77 (cfg streams key); .split/.splitlines at :58,:59,:83,:93',
  why='Python source on stdin of "python3 -I -B - $KH $BUN" inside 0700 BUN; assertion messages are fixed English (Staged config differs: <field> with fields streams|s1_routing|remove_files|type_mix, Store differs, Unit slice differs, REMOVE hashes differ, ...); canary record keys canary, admission_job, proof_job, config_identity, contract_sha256, manifest_sha256, wrapper_sha256, admission_receipt_sha256, admission_log_sha256, admission_kit, proof_partition, proof_state, job_name, submission; ORCH 1758Z'),
 dict(id='E10',class_='exempt-content',member='rehearsal logs and receipts in KH/o and /tmp/jjyeung/a_05b8ac69/jobs/<job>.proof/',
  matches='possible traceback text naming student_pilot modules or vqa if the rehearsal fails',
  why='in-job log/file contents inside the 0700 KH/o tree or node-local /tmp job dir; fixed log words are REHEARSAL_STEP <bwrap_setup|environment|pythonpath|namespace|trainer_tree|loader_import|staged_store_startup> PASS and receipt keys status, steps, production_authorized, admission_executed, rehearsal, staged_source, rc, log; ORCH 1758Z (E1 precedent)')]
for e in new_content: e['class']=e.pop('class_')
mem={}
ex=W/'ex_08f3a7b2'
for p in sorted(ex.rglob('*')):
  if p.is_file(): mem[str(p.relative_to(ex))]=sha(p.read_bytes())
ext=[dict(path='/project/community/jjyeung/okh7/i_7f1589c1/'+k,sha256=v) for k,v in sorted(mem.items())]
req=json.loads((W/'drv_c1/CERTIFICATE_REQUIREMENTS.json').read_text())
assert {e['path']:e['sha256'] for e in req['external']}=={e['path']:e['sha256'] for e in ext} and len(ext)==40
rec=dict(reviewer='review_r1anon7 (Devin Opus, trinity-1-3)',verdict='CLEAN',anon_ok_written=True,
 config_identity='6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74',
 operator_archive_sha256='08f3a7b2ef2e1923ba77b464afcedbbe668a77a1915b4c32c0a815044ff7d9fd',
 package='R1 vehicle P continuation C fix round 4: BUN /project/community/jjyeung/okh7/i_7f1589c1, KH /project/community/jjyeung/okh7/x_7f1589c1, run 05b8ac69, job a15_cot_ap05b8ac69, rehearsal job a15_cot_ap05b8ac6a',
 precedent='events/review_r1anon6/ANON_SCAN_R1C.json and ANON_OK.json (archive 6a5c7d00, manifest d008b39a, scan 3a5ac3a0, CLEAN)',
 rule=prev['rule'],regex=dict(operator=prev['regex']['operator'].replace('scan_body.py','scan_body.py; drv_c1/scan1_c3.out'),precedent=prev['regex']['precedent']),
 inputs=dict(scan=str(W/'drv_c1/scan1_c3.out'),scan_sha256=sha(Braw),manifest_sha256_in_scan='635c5335667dba36473ddad8068f7225d1cda81df4baee2e861c1b8e4175b12f',
  archive=str(W/'snap_08f3a7b2/out/p_08f3a7b2.tar'),archive_sha256='08f3a7b2ef2e1923ba77b464afcedbbe668a77a1915b4c32c0a815044ff7d9fd',
  archive_extracted=str(ex),archive_check='40/40 tar members byte-equal to ex_08f3a7b2; 40 member pins equal drv_c1/CERTIFICATE_REQUIREMENTS.json external',
  member_diff_vs_previous='p_05b8ac69.sh 4a304bfd->0c065dde, s.sh 5f15c65f->83d20907, sums.txt ab08a74a->1d227092; 37 members byte-equal to ex_6a5c7d00',
  previous_scan='drv_c1/scan1.out (sha 3a5ac3a0)',proof_embedded_sha256='90f968228b4130f5d65f33e3fce7604a582f8c80fd7b5bd56fd070625c647e47 (decoded; equals in-script pin; previous 861b540b)',
  rulings=['events/r1_ops/20261117T1557Z_ORCH_ANSWER_bind_v7_card_v3.md item 1',R1758]),
 sections=sections,
 counts_by_class={'inherited-accepted':counts.get('inherited-accepted',0),'exempt-content':counts.get('exempt-content',0),'new-visible':0},
 counts_note='%d hits carried with class from review_r1anon6 at byte-identical lines; %d further regex-matching lines duplicate a classified hit text; %d unaccounted; 0 regex hits among the %d changed or added scan lines'%(len(hits),dup,len(unacc),len(changed)),
 scan_diff_vs_r1anon6=dict(changed_or_added_lines=changed,lines=cl),
 hits=hits,new_member_content=new_content,other_exempt=prev['other_exempt'],new_visible_hits=[],
 proof_script_check=dict(
  argv='p_05b8ac69.sh changes only line 8 (exec "$PY" -I -B - "$@", was "$1"), embedded source/pin (lines 10-11) and lines 15-21 (argv parse: AUTHORITY or AUTHORITY --rehearsal STAGED_ROOT); #SBATCH header and identity unchanged',
  rehearsal_argv='CONT4.md:90 sbatch --partition=general --nodelist=orchard-community-0 --nodes=1 --ntasks=1 --cpus-per-task=4 --mem=32G --time=00:30:00 --gres=gpu:0 --job-name=a15_cot_ap05b8ac6a --no-requeue --output=$KH/o/%j.rehearsal.out --error=$KH/o/%j.rehearsal.err $BUN/p_05b8ac69.sh $BUN/a4.json --rehearsal /tmp/jjyeung/p_05b8ac69_172180/tmp/jjyeung/a_05b8ac69/root; sealer CONT4.md:85 /usr/bin/python3 -I -B $BUN/p.py --kit $KH --bundle $BUN --binding $BUN/BINDING.json --partition general --out $BUN/a4.json; job name opaque hex token, no further underscore; all paths opaque; no regex hit',
  bwrap='rehearsal inserts --ro-bind <staged root> /tmp/jjyeung/a_05b8ac69/root before /bin/bash; staged root must resolve under /tmp/jjyeung/; otherwise argv is the inherited command()',
  receipts_and_logs='KH/o/<job>.rehearsal.json (REHEARSAL_RUNNING -> REHEARSAL_OK|REHEARSAL_FAIL), KH/o/<job>.rehearsal.log, KH/o/%j.rehearsal.out|err, /tmp/jjyeung/a_05b8ac69/jobs/<job>.proof/tail.json; log words REHEARSAL_STEP <step> PASS; all names opaque',
  env='new reads: TRAINER (set by inherited KH b/c.sh), TK_JOBDIR (existing proof export), SLURM_JOB_NAME compared with a15_cot_ap05b8ac6a; no new export',
  embedded_diff='decoded 90f96822 vs 861b540b: line 130 heredoc adds v.tree trainer check and sys.path insert of $TRAINER before the inherited student_pilot.loader_audit import; adds rehearsal_program/rehearsal_execute; main(authority, rehearsal_root) branches job name, receipt name and status; production branch unchanged in substance (indented)',
  home_literal='no /home/<user> literal in p_05b8ac69.sh, decoded source, s.sh or sums.txt; only inherited KH b/c.sh:351 bwrap token /home/jjyeung (inherited-accepted, carried)'),
 gate_check=dict(
  s_sh='canary branch (go.canary true) pinned to ADMISSION_JOB=172180, PROOF_JOB==BUN/job.id, refuses <job>.rehearsal.json, ADMISSION_KIT in {KH, KH.f172180}; pinned receipt/log/manifest SHAs; squeue --noheader --jobs <job> --format=%i|%T|%j|%P with TZ=UTC must show a15_cot_ap05b8ac69 on general; writes KH/o/<job>.canary.json; PASS branch unchanged; training sbatch line byte-identical (now s.sh:121): -J a15_cot_ap05b8ac69 -o /dev/null -e $KH/o/%j.err -A mt01 -p advanced -N1 --ntasks=1 --gres=gpu:4 -c 48 --mem=800G -t 24:00:00 --signal=B:USR1@3600 --no-requeue $BUN/jb.sh; env keys PROOF_JOB, ADMISSION_JOB, ADMISSION_KIT opaque; no regex hit in argv, env or messages',
  jb_sh='byte-equal to previous kit (5e03795d); classification carried from r1anon6',
  job_sh='KH manifest changes only ANON_OK.json, SHA256SUMS.txt, k/selection_equality.json (KIT_DIFF4.md); job.sh scan COMMANDS lines unchanged; classification carried from r1anon6'),
 not_observable='Orchard not contacted; deployed KH bytes and modes known only via scan listing and KIT_DIFF4.md; rehearsal argv taken from CONT4.md, not from a sealed member')
rraw=(json.dumps(rec,indent=1,sort_keys=True)+'\n').encode()
cert=dict(config_identity=rec['config_identity'],operator_archive_sha256=rec['operator_archive_sha256'],
 manifest_sha256='635c5335667dba36473ddad8068f7225d1cda81df4baee2e861c1b8e4175b12f',scan_sha256=sha(Braw),
 exemption_record=R1758,exemption_records_cited=rec['inputs']['rulings'],external=ext,hits=0,
 inherited_accepted=rec['counts_by_class']['inherited-accepted'],exempt_content=rec['counts_by_class']['exempt-content'],
 inherited_token_accepted=[],private_tree_contents_accepted=[],reviewer=rec['reviewer'],
 scan_record='events/review_r1anon7/ANON_SCAN_R1C4.json',status='CLEAN')
craw=(json.dumps(cert,indent=1,sort_keys=True)+'\n').encode()
(L/'out/ANON_SCAN_R1C4.json').write_bytes(rraw);(L/'out/ANON_OK.json').write_bytes(craw)
print('ok',sha(rraw)[:8],sha(craw)[:8])
