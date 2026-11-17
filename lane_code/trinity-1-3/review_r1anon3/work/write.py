import json,hashlib
EV='/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_r1anon3'
SCAN='/scratch/jjyeung/orch_n30/r1_ops/work/drv_p2/scan1.out'
c=json.load(open('cls.json'));sha=lambda b:hashlib.sha256(b).hexdigest()
ss=sha(open(SCAN,'rb').read());assert ss=='434f0515abb0c93f939d8a46c7d30952e68799bd4d09a72c66aea5ca83b2a8b0'
assert c['manifest']=='ed7be1bb642b6b5e71c8bd770bed50c0ab2f0248572a96065102a95b72d19bfe'
ID='2c67f1f25114ab1324cee10b796e86afc79d01999ad3881860ab35710e7fee5d';OUT='def1e1f2b1153328b024209e69fcbb71f2dd556b7376eacb836d40bb66d9845f'
R1557='events/r1_ops/20261117T1557Z_ORCH_ANSWER_bind_v7_card_v3.md';R1758='events/r1_ops/20261117T1758Z_ORCH_ANSWER_anon_hits_exempt_submit_proof1.md'
cnt=c['counts']
rec=dict(
 reviewer='review_r1anon3 (Devin Opus, trinity-1-3)',
 package='R1 vehicle P proof-2 Orchard kit: BUN /project/community/jjyeung/okh7/i_6f8ed106, KH /project/community/jjyeung/okh7/x_6f8ed106, run 78d0a06c, job a15_cot_ap78d0a06c',
 config_identity=ID,operator_archive_sha256=OUT,
 rule='ORCH 1557Z item 1 (inherited sealed names stay; every NEW visible name stays clean; private 0700 trees are not visible) and ORCH 1758Z (in-job file and log contents in 0700 trees exempt; the account home path token accepted)',
 regex=dict(operator='(?i)split|revsi|vsibench|vsi|distill|qgen|scannet|arkit|qwen|sft|student|benchmark|eval (scan_body.py)',precedent='ANON_SCAN_R1P.json regex, applied to every scan1 line'),
 inputs=dict(scan1_out=SCAN,scan_sha256=ss,scan_lines=c['lines'],manifest_sha256_in_scan=c['manifest'],
   scan_script='drv_p2/scan1.sh (body = drv_p2/scan_body.py with @STORE@=6f8ed106, @RUN@=78d0a06c)',
   archive_extracted='/scratch/jjyeung/orch_n30/r1_ops/work/ex_6f8ed106',archive_members=len(c['ext']),
   archive_check='all 35 local members byte-equal to snap_2c67f1f2/out/p_6f8ed106.tar (sha def1e1f2...) and to sums.txt',
   proof_embedded_sha256='575ca063ec91c04e409c58fb0ccaf31f7b1ec6aa80881789de3b94df9e7bd93f (decoded from p_78d0a06c.sh line 10; equals its in-script pin)'),
 sections=c['sections'],
 counts_by_class=dict(cnt,**{'new-visible':0}),
 counts_note='951 inherited-accepted = 634 GREP INHERITED lines + 313 GREP NEW BUN/qt/ lines + 4 precedent-regex-only lines (819, 1759, 2656, 2855); 9 exempt-content = 6 GREP NEW tar-member lines + 3 GREP NEW BUN/qt/student_pilot/{loader_audit,type_mix,vehicle_p}.py',
 qt_ruling=dict(
   question='Are the BUN/qt/ file paths (e.g. qt/configs/student_benchmark_eval_v1.json, qt/evalpath/*) inherited names in a private 0700 tree or new visible names?',
   answer='Inherited names in a private 0700 tree (accepted), except the 3 new student_pilot members, which are the same names proof 1 ruled exempt as tar members and stay inside the same 0700 tree.',
   evidence=['scan_body.py:11 asserts every directory under BUN and KH is mode 0700 and :10 that none is a symlink before anything prints; scan1.out reaches its MANIFEST line (3853), so every BUN/qt directory passed (47 subdirectories + qt itself)',
     'scan1.sh: private "$O" and private "$BUN" require okh7 and i_6f8ed106 to be 0700 non-symlink dirs; the scan ran, so they are',
     'drv_p2/q1.sh selection_tree(): target.mkdir(mode=0o700), parents mkdir(mode=0o700), files chmod 0o600, every member sha-checked against c.json files, inventory must equal c.json',
     'scan1.out: BUN/qt holds 847 entries = qt + 47 dirs + 799 files; the 799 relative names equal the t.tar member set exactly (796 listed INHERITED via H k/7.json + 3 listed NEW); no other name',
     'qt reaches no argv: q1.sh passes it only as PYTHONPATH in the child environment (/proc/<pid>/environ is owner-only); q.py argv names BUN/q.py, H/k/pool_selection_eac5f9f0.json, H/k, i_1be16f28/q_6c18a2bf/o/native/receipt.json, BUN/{j,c,u,config}.json, BUN/q (all clean); p_78d0a06c.sh, embedded p.py, jb.sh and s.sh contain no qt reference; the proof bwrap argv lists okh7 and KH top-level entries only, so BUN subpaths never appear'],
   options_rejected='new-visible: rejected because the names are not visible to any other account (0700 chain okh7 -> i_6f8ed106 -> qt) and are byte-identical inherited sealed member names'),
 hits=c['hits'],
 new_visible_hits=[],
 proof_script_check=dict(
   argv=['sbatch: TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable -J a15_cot_ap78d0a06c -A mt01 -p advanced|general -N1 --ntasks=1 -c 48 --mem=800G -t 04:00:00 --no-requeue -o KH/o/%j.out -e KH/o/%j.err BUN/p_78d0a06c.sh BUN/a.json (scan1 NEW section) - clean',
     'p_78d0a06c.sh:2-3 #SBATCH lines clean; :8 exec "$PY" -I -B - "$1" (source on stdin) - clean',
     'embedded p.py command(): bwrap --ro-bind per okh7 and KH top-level entry, /bin/bash -c "set -e; chmod 700 -- $1 $2 $3; exec /bin/bash -s" a KH okh7/r okh7 - same as proof 1, clean',
     'embedded p.py :114 loader audit: "${BW[@]}" "$PILOT_VENV/bin/python" -B - "$X"; module name student_pilot.loader_audit only in the stdin heredoc (0700 work dir), not argv - same as proof 1',
     'embedded p.py :70/:72 now --dir /home and test -d /home: the proof-1 N4 token /home/jjyeung is gone (only diff vs proof-1 embedded source)'],
   environment='embedded p.py environment(): SLURM_* plus PATH, HOME=/tmp/jjyeung, TMPDIR=/tmp, TZ=UTC, LC_ALL=C, CUDA_VISIBLE_DEVICES=, PYTHONDONTWRITEBYTECODE=1; no /home/<user> literal',
   home_literal='no /home/<user> literal in p_78d0a06c.sh or its embedded source; the only /home/jjyeung left is inherited KH b/c.sh:351 (scan1 line 2855), inherited-accepted as in proof 1',
   census_keys='t.tar student_pilot/loader_audit.py (new): opaque_keys() maps the 4 dataset prefixes in printed keys to g0..g3 and prints census_code_map_sha256 only; :162 breakdown, :228 trace rows, :244 required_families go through print_record; the code map stays local (snap CENSUS_CODES.local.json). Census keys are opaque.',
   log_lines='w.steps lines from jb.sh prefix (host, /tmp free, TK_JOB_START, sessions, staging) unchanged vs proof 1 except run/kit tokens - clean; proof.log/proof.json in KH/o (0700, private() check at p.py main) - exempt content'),
 other_exempt=[
   dict(id='E1',surface='log lines: KH/o/<job>.proof.log',text='loader_trace rows still carry values such as "stream": "vqa", qid, question_type, database, frames, target (opaque_keys encodes keys, not values); traceback text on failure may name student_pilot/loader_audit.py',
     **{'class':'exempt-content'},ruling=R1758+' (in-job log contents in 0700 trees exempt; same class as proof-1 N1-N3)'),
   dict(id='E2',surface='file contents of bundle members (u.json, BINDING.json, c.json, j.json, config.json, ...)',text='u.json names /scratch/jjyeung/orch_n30/... paths and student_pilot/* implementation keys; content only, in 0700 BUN',**{'class':'exempt-content'},ruling=R1758),
   dict(id='E3',surface='u.gz',text='gzip FLG=0 (no embedded original file name); content is unit rows JSONL',**{'class':'exempt-content'},ruling=R1758)],
 diff_vs_proof1=dict(
   method='normalize c5f3847d/6f8ed106, 26cc98b7/78d0a06c, t_5e1514ef9d91bee8/t_b83a8a35d420815b; compare scan1 sections',
   inherited_section='1771 = 1771 lines, identical after normalization',
   commands_section='124 = 124 lines, identical after normalization',
   new_section_added=['BUN/qt/ (847 entries, ruled above)','BUN/u.gz','BUN/u.json','BUN/i.json','BUN/m.json','BUN/q/u','BUN/q/u/e.tsv','BUN/q/u/m.json','BUN/q/u/native','BUN/q/u/native/U_Faithful.json','BUN/q/u/native/receipt.json','BUN/r4.txt','KH/k/5c867d34.json','/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/u_d7c3206c079b8397/{i.json,m.json,u.gz}','sbatch argv with -p general (both partitions now listed)'],
   new_section_removed=['KH/k/29ddc426.json'],
   added_names_clean='no operator- or precedent-regex hit in any added name outside BUN/qt; unit source names (u.gz, u.json, i.json, m.json, q/u/*, U_Faithful.json, u_d7c3206c079b8397) clean',
   classes='same classes as proof 1 (inherited-accepted, exempt-content); no new-visible'),
 visible_clean=dict(job_name='a15_cot_ap78d0a06c',exports='e.txt 20 destinations q8/8865619b/78d0a06c_{m100,m200,mstop,mstopB,mstopC}.tar.partNN-of-04',
   production_sbatch='s.sh:42 -J a15_cot_ap78d0a06c -o /dev/null -e KH/o/%j.err ... BUN/jb.sh',paths='okh7/r/78d0a06c, s_22b44165/d.db, /tmp/jjyeung/a_78d0a06c, /tmp/jjyeung/p_78d0a06c_<job>/{entry.sh,tmp,slots,arm,runs}, /scratch/fsw/.../ap/6f8ed106/*'),
 not_observable='Orchard was not contacted; proof.log is not yet observable; okh7 top-level entry names beyond i_6f8ed106/x_6f8ed106/r/s_22b44165 are not in scan1 (bwrap argv lists them; unchanged class from proof 1)',
 verdict='CLEAN',anon_ok_written=True)
rb=(json.dumps(rec,indent=1,sort_keys=True)+'\n').encode()
open(EV+'/ANON_SCAN_R1P2.json','wb').write(rb)
cert=dict(status='CLEAN',hits=0,config_identity=ID,operator_archive_sha256=OUT,manifest_sha256=c['manifest'],scan_sha256=ss,
 scan_record='events/review_r1anon3/ANON_SCAN_R1P2.json',exemption_record=R1758,exemption_records_cited=[R1557+' item 1',R1758],
 exempt_content=cnt['exempt-content'],inherited_accepted=cnt['inherited-accepted'],private_tree_contents_accepted=[],inherited_token_accepted=[],
 external=c['ext'],reviewer='review_r1anon3 (Devin Opus, trinity-1-3)')
open(EV+'/ANON_OK.json','w').write(json.dumps(cert,indent=1,sort_keys=True)+'\n')
print('written',sha(rb))
