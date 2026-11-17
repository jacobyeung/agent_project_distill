import json,hashlib,sys
sys.path.insert(0,'/scratch/jjyeung/orch_n30/r1_ops/work/drv_p4')
EV='/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_r1anon4'
SCAN='/scratch/jjyeung/orch_n30/r1_ops/work/drv_p4/scan1.out'
c=json.load(open('cls.json'));sha=lambda b:hashlib.sha256(b).hexdigest()
ss=sha(open(SCAN,'rb').read());assert ss=='1f8b8d8cadc1aed41bea6c1961b2b86cc96707908b59d6ab8d6dac04ac913866'
assert c['manifest']=='4617dc08c53190459ff3c4cfd2c8c7e489ccd1122a72af5898a09983bff3deda'
ID='fac0705214fdecb53561c633d7d94642cd469b50b662c5de81f09d11891d115f';OUT='a99ab475f602c63332d4faaa4bf20f9d75e604cb973a80a041338b03a7d5f589'
R1557='events/r1_ops/20261117T1557Z_ORCH_ANSWER_bind_v7_card_v3.md';R1758='events/r1_ops/20261117T1758Z_ORCH_ANSWER_anon_hits_exempt_submit_proof1.md'
for h in c['hits']:
  h['file']='drv_p4/scan1.out'
  h['why']=h['why'].replace('NEW line','scan1 NEW line')+'; identical after token normalization to proof-2 hit classified %s by review_r1anon3 (ANON_SCAN_R1P2.json)'%h['class']
cnt=c['counts']
rec=dict(
 reviewer='review_r1anon4 (Devin Opus, trinity-1-3)',
 package='R1 vehicle P packet A (fix round 10) Orchard kit: BUN /project/community/jjyeung/okh7/i_69d2930d, KH /project/community/jjyeung/okh7/x_69d2930d, run 673bc60f, job a15_cot_ap673bc60f',
 config_identity=ID,operator_archive_sha256=OUT,
 rule='ORCH 1557Z item 1 (inherited sealed names stay; every NEW visible name stays clean; private 0700 trees are not visible) and ORCH 1758Z (in-job file and log contents in 0700 trees exempt; the account home path token accepted)',
 precedent='events/review_r1anon3/ANON_SCAN_R1P2.json and ANON_OK.json (proof 2, CLEAN)',
 regex=dict(operator='(?i)split|revsi|vsibench|vsi|distill|qgen|scannet|arkit|qwen|sft|student|benchmark|eval (scan_body.py)',precedent='ANON_SCAN_R1P.json regex, applied to every scan1 line'),
 inputs=dict(scan1_out=SCAN,scan_sha256=ss,scan_lines=3859,manifest_sha256_in_scan=c['manifest'],
   scan_script='drv_p4/scan1.sh = drv_p2/scan1.sh after token normalization (69d2930d/6f8ed106 -> STORE, 673bc60f/78d0a06c -> RUN) except the PACKET print line',
   archive_extracted='/scratch/jjyeung/orch_n30/r1_ops/work/ex_69d2930d',archive_members=len(c['ext']),
   archive_check='fresh extraction of snap_fac07052/out/p_69d2930d.tar (sha a99ab475...) is diff -r identical to ex_69d2930d; 36/36 sums.txt entries OK; 37 member pins equal drv_p4/CERTIFICATE_REQUIREMENTS.json external',
   proof_embedded_sha256='7883e3fe80d934785de06805828222fc2e867e03fba1c19dd2660c756294e0b8 (decoded from p_673bc60f.sh line 10; equals its in-script pin and drv_p4/proof_decoded.py)'),
 sections=c['sections'],
 counts_by_class=dict(cnt,**{'new-visible':0}),
 counts_note='960 grep/precedent hits, each identical after token normalization (text, section, class) to proof 2: 951 inherited-accepted (634 GREP INHERITED, 313 GREP NEW BUN/qt, 4 precedent-only at lines 820, 1764, 2661, 2860), 9 exempt-content (6 GREP NEW tar-member lines 3216-3221, 3 GREP NEW BUN/qt/student_pilot lines 3078, 3172, 3173)',
 diff_vs_proof2=dict(
   method='sed 69d2930d|6f8ed106 -> STORE, 673bc60f|78d0a06c -> RUN over both scan1.out files, then diff',
   added_names=['scan1:40 BUN/n.json','scan1:913 BUN/r5.txt','scan1:914 BUN/r6.txt','scan1:920 BUN/records/n.json','scan1:966 /scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/n.json (staging locator, config.json remove_files[6])'],
   replaced_names=['scan1:946 KH/k/18fccf83.json replaces KH/k/5c867d34.json'],
   other_changes='PACKET and MANIFEST lines only; INHERITED, COMMANDS, GREP NEW and GREP INHERITED sections identical after normalization',
   added_names_clean='no operator- or precedent-regex hit in any added or replaced name; all are opaque (n, r5, r6, 18fccf83) under already-accepted parents',
   archive_member_changes='new n.json, records/n.json, p_673bc60f.sh (replaces p_78d0a06c.sh); content changed in BINDING.json, config.json, d.json, records/d.json, d.py, e.txt, ids.json, jb.sh, p.py, s.sh, sums.txt, v.json, records/v.json; t.tar (e5be8157) unchanged. jb.sh, s.sh, e.txt identical after normalization; d.py and p.py add only validate_switches (S2 on, S1 off, own-sampling 0).'),
 n_json_ruling=dict(
   question='Is the content of n.json / records/n.json (601 JSONL rows {pool, question_type, reason, row_key, scene}) exempt in-job content in a 0700 tree under 1758Z, or a new visible name?',
   answer='Exempt in-job content (class exempt-content). Only the names n.json, records/n.json and the staging locator .../ap/69d2930d/n.json are visible, and they are clean.',
   content_facts=['601 rows; pools b12_cntapp_gt_v1 468, vsti_rel_v4 127, r1_room_traced 6; 10 question types (obj_appearance_order, object_counting, first_seen_frame, camera_obj_rel_dist_v1-3, obj_obj_relative_pos_lr/ud/nf, room_size_estimation); reason outside_native_training_division for all; scenes d1/v<12hex> or d3/v<12hex> for all',
     'regex over the content: 6 row_keys of pool r1_room_traced carry source tokens (5x scannet with scene0398/0498/0567/0624, 1x vsi590k); pool names and question types carry no operator-regex hit'],
   evidence=['n.json is a file in BUN (0700 chain okh7 -> i_69d2930d; scan_body.py:11 asserts 0700 for every directory and the scan reached MANIFEST) and records/n.json is byte-equal (sha 02315a74)',
     'it reaches the job only as config.json remove_files[6] path, read by the unchanged t.tar trainer code like remove_0..5.jsonl; no script names it in argv, environment or a log line (grep of d.py, p.py, jb.sh, s.sh, embedded proof source)',
     'precedent: proof-2 staged records in the same staging directory ap/<store>/ (c.json, j.json, s.json) carry student/benchmark/revsi/vsi in content and were certified exempt content in proof 2'],
   options_rejected='new-visible: rejected because no row value appears in any name, path, argv, environment, job name or log name; the rulings exempt in-job file contents',
   not_observable='Orchard permissions of /scratch/fsw/.../ap/69d2930d are not in scan1; same class as the proof-2 staged records'),
 hits=c['hits'],
 new_visible_hits=[],
 proof_script_check=dict(
   argv=['sbatch: TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable -J a15_cot_ap673bc60f -A mt01 -p advanced|general -N1 --ntasks=1 -c 48 --mem=800G -t 04:00:00 --no-requeue -o KH/o/%j.out -e KH/o/%j.err BUN/p_673bc60f.sh BUN/a.json (scan1 NEW section) - clean',
     'p_673bc60f.sh:2-3 #SBATCH lines clean; :6 PATH/CUDA_VISIBLE_DEVICES/PYTHONDONTWRITEBYTECODE; :8 exec "$PY" -I -B - "$1" (source on stdin); differs from p_78d0a06c.sh only in the embedded blob, its pin and the identity pin',
     'embedded proof source (7883e3fe) differs from proof 2 (575ca063) only by validate_switches() and its call; bwrap argv and loader-audit invocation unchanged, clean'],
   environment='unchanged from proof 2: SLURM_* plus PATH, HOME=/tmp/jjyeung, TMPDIR=/tmp, TZ=UTC, LC_ALL=C, CUDA_VISIBLE_DEVICES=, PYTHONDONTWRITEBYTECODE=1',
   home_literal='no /home/<user> literal in p_673bc60f.sh or its embedded source (only /home as bwrap tmpfs/dir); the only /home/jjyeung is inherited KH b/c.sh:351 (scan1 line 2860), inherited-accepted',
   census_keys='t.tar unchanged (e5be8157), so student_pilot/loader_audit.py opaque_keys() still maps dataset prefixes to g0..g3 and prints census_code_map_sha256 only: census keys opaque',
   log_lines='new log text only: ValueError "Launch requires S2=true, S1=false, and both max_own_probability=0" on refusal, into KH/o/<job>.err (0700), no regex hit; w.steps lines from jb.sh unchanged after normalization'),
 other_exempt=[
   dict(id='E1',surface='log lines: KH/o/<job>.proof.log',text='loader_trace values such as "stream": "vqa" (keys encoded, values not); same as proof 2',**{'class':'exempt-content'},ruling=R1758),
   dict(id='E2',surface='file contents of bundle members (u.json, BINDING.json, c.json, j.json, s.json, config.json, ...)',text='content only, in 0700 BUN; same as proof 2',**{'class':'exempt-content'},ruling=R1758),
   dict(id='E3',surface='u.gz',text='unchanged from proof 2 (sha 14439f0c); no embedded file name',**{'class':'exempt-content'},ruling=R1758),
   dict(id='E4',surface='file contents of n.json and records/n.json (and staged .../ap/69d2930d/n.json)',text='601 REMOVE rows; 6 row_keys carry scannet/scene#### and vsi590k tokens; pool names vsti_rel_v4, b12_cntapp_gt_v1, r1_room_traced',**{'class':'exempt-content'},ruling=R1758+' (in-job file contents exempt); see n_json_ruling')],
 not_observable='Orchard was not contacted; proof.log does not exist yet; r5.txt, r6.txt and KH k/18fccf83.json are Orchard-only and checked by name only',
 verdict='CLEAN',anon_ok_written=True)
rb=(json.dumps(rec,indent=1,sort_keys=True)+'\n').encode()
cert=dict(status='CLEAN',hits=0,config_identity=ID,operator_archive_sha256=OUT,manifest_sha256=c['manifest'],scan_sha256=ss,
 scan_record='events/review_r1anon4/ANON_SCAN_R1PA.json',exemption_record=R1758,exemption_records_cited=[R1557+' item 1',R1758],
 exempt_content=cnt['exempt-content'],inherited_accepted=cnt['inherited-accepted'],private_tree_contents_accepted=[],inherited_token_accepted=[],
 external=c['ext'],reviewer='review_r1anon4 (Devin Opus, trinity-1-3)')
cb=(json.dumps(cert,indent=1,sort_keys=True)+'\n').encode()
from cert_policy import validate_certificate
from packet_config import PINS, MEMBERS
ROOT='/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/'
r=validate_certificate(json.loads(cb),rb,open(SCAN,'rb').read(),open(ROOT+R1758,'rb').read(),PINS,MEMBERS)
print('validate PASS',r['scan_record_sha256'])
if 'write' in sys.argv:
  open(EV+'/ANON_SCAN_R1PA.json','wb').write(rb);open(EV+'/ANON_OK.json','wb').write(cb)
  print('written scan',sha(rb),'ok',sha(cb))
