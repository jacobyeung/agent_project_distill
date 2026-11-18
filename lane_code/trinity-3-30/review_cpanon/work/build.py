import json,re,collections,hashlib
from pathlib import Path
EV=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events')
P7=EV/'review_r1anon7/ANON_SCAN_R1C4.json'
d=json.load(open(P7))
S=Path('/scratch/jjyeung/orch_n30/r1_ops6/work/xfer/scan1.out'); sraw=S.read_bytes(); SSHA=hashlib.sha256(sraw).hexdigest()
assert SSHA=='befc63858131cdf167bb1ce313d4fcc9eecc6a2c6a6a6d07542cec4f423a1b37'
lines=sraw.decode().split('\n'); lines=lines[:-1] if lines[-1]=='' else lines
MAN='2b8242f095c5a8c7d37a76c5d5226efc03ec870573f99e1b391dd44b9dd083e2'
assert [l for l in lines if l.startswith('MANIFEST ')]==['MANIFEST '+MAN]
op=re.compile(r'split|revsi|vsibench|vsi|distill|qgen|scannet|arkit|qwen|sft|student|benchmark|eval',re.I)
PRE=r"(?i)scannet(pp)?|arkit\w*|scene\d{4}|vsi[-_ ]?bench|vsti?bench|dsibench|\bvsi\b|revsi|qwen[\w.-]*|\bsplit\b|distill\w*|\bqgen\b|gemini|/scratch/jjyeung|/home/jjyeung|orch_n\d+|agent_project\w*|\bteacher\b|\bstudent\w*|spatial|benchmark\w*|hypersim|multiscan|scanqa|sqa3d|\bvqa\b"
pre=re.compile(PRE)
heads={'NEW / BUNDLE NAMES AND SUBMISSION ARGV':'NEW','INHERITED NAMES INSIDE VERIFIED 0700 TREES / INHERITED STAGING LOCATORS':'INHERITED','SEALED SCRIPT COMMAND LINES FOR ARGV REVIEW (NO SESSION CONTENTS)':'COMMANDS','GREP NEW NAMES':'GREP_NEW','GREP INHERITED NAMES / ARGV (account for each under the ruling)':'GREP_INHERITED'}
norm=lambda t:t.replace('7f1589c1','ee227714').replace('05b8ac69','6ed2c7aa')
bysec={};bytext={}
for h in d['hits']:
  bysec.setdefault((h['section'],norm(h['text'])),h); bytext.setdefault(norm(h['text']),h)
sec=None;hits=[];secs={}
for i,l in enumerate(lines,1):
  if l in heads: sec=heads[l];secs[sec]=[i+1,None];continue
  if l.startswith(('PACKET ','MANIFEST ','PENDING ')):sec='TAIL';continue
  if sec in secs: secs[sec][1]=i
  m=sorted(set(x.group(0) for x in op.finditer(l))|set(x.group(0) for x in pre.finditer(l)))
  if not m: continue
  p=bysec.get((sec,l)); how='same section and text'
  if p is None: p=bytext.get(l); how='same text, other section (r1anon7 duplicate)'
  assert p is not None, (i,l)
  tok='' if p['text']==l else ' after token normalization (7f1589c1->ee227714, 05b8ac69->6ed2c7aa)'
  hits.append(dict(file='r1_ops6/work/xfer/scan1.out',line=i,section=sec,text=l,matches=m,class_=p['class'],
    prior=f"events/review_r1anon7/ANON_SCAN_R1C4.json {p['file']}:{p['line']} ({p['section']}; {how})",
    why=f"carried from review_r1anon7 class {p['class']}: text identical{tok}; r1anon7 reason: {p['why'][:260]}"))
for h in hits: h['class']=h.pop('class_')
cnt=collections.Counter(h['class'] for h in hits)
uniq=len({h['text'] for h in hits})
missing=[h for h in d['hits'] if (h['section'],norm(h['text'])) not in {(x['section'],x['text']) for x in hits}]
assert not missing
new_content=[
 dict(id='N1',member='z.json = records/z.json (caba6a56; 17,879 JSONL rows)',class_='exempt-content',
  matches='no operator or precedent regex hit; keys pool,question_type,reason,row_key,scene; pool 6 opaque values p<hex8>; question_type object_counting; reason count_diag_first_seen_list_form (all rows); row_key b12ct_/b12cs_/d0total_/q<hex> opaque; scene d<n>/v<hex12>',
  why='file contents of a 0700 BUN member and its staged copy at .../ap/69d2930d/z.json: in-job file contents exempt (ORCH 1758Z; r1anon7 E2/E4 precedent). The reason string names a row defect (counting question, first-seen list form), not a project, benchmark, dataset, model or method; it never reaches a name, path, argv, env, job name or log name. Review_cprime LOW 4 resolved: accepted as content.'),
 dict(id='N2',member='s.sh canary_delta branch (lines 27-159, 245-247)',class_='exempt-content',
  matches='"Cprime" in docstring :28; vqa :69,:139 (config stream key); .split :98,:225 (Python method); /scratch/fsw/... paths :40,:108,:117 identical in form to C4 config locators; /project/community/jjyeung/okh7/x_7f1589c1 :43 (opaque)',
  why='Python source on stdin of "python3 -I -B - $KH $BUN" inside 0700 BUN (as r1anon7 E9). Error text is "canary_delta: <fixed English>"; record keys canary_delta, authority, admission_job, base_config_identity, config_identity, contract_sha256, manifest_sha256, wrapper_sha256, admission_receipt_sha256, admission_log_sha256, admission_kit, job_name, submission written to KH/o/canary_delta.json (opaque name). Env read: ADMISSION_JOB, ADMISSION_KIT (opaque). "Cprime" is a packet label, not a forbidden-class word, and appears in no visible surface. Training sbatch line :256 equals C4 :121 except -J a15_cot_ap6ed2c7aa.'),
 dict(id='N3',member='c4.json (2152828974; byte-equal to C4 config.json)',class_='exempt-content',
  matches='content carries C4 config words (benchmark_scene_exclusions, arkit_*, vqa) already in C4 config.json',
  why='identical bytes to a C4 member already exempt as bundle-member content (r1anon7 E2); new name c4.json is opaque; ORCH 1758Z'),
 dict(id='N4',member='config.json, BINDING.json, ids.json, e.txt, jb.sh, p_6ed2c7aa.sh, sums.txt',class_='inherited-accepted',
  matches='no regex hit beyond C4 counterparts; diffs are only identity/run/store/job tokens, cents, rows=rebind, counting_removal, z.json pin',
  why='derived token strings only (6ed2c7aa, ee227714, 774503e2, contract 2f27db1b); e.txt export names q8/8865619b/6ed2c7aa_m*.tar.partNN-of-04 opaque; jb.sh env keys KH RUN RS LOG NL unchanged'),
]
for n in new_content: n['class']=n.pop('class_')
gate=dict(
 s_sh='canary_delta branch classified N2; PASS and canary bodies byte-identical to C4 (diff: lines 13-14 BUN/KH, 27-159 new branch, 245-247 marker, 256 -J); sbatch argv at scan1.out:2810 opaque (-J a15_cot_ap6ed2c7aa, $KH/o/%j.err, $BUN/jb.sh); no /home/<user> literal',
 jb_sh='24f7b8b1; differs from C4 5e03795d only at lines 18-19, 25, 32, 53 (x_ee227714, a_6ed2c7aa, r/6ed2c7aa, i_ee227714); env keys and log names ($KH/o/${SLURM_JOB_ID}.w.steps, .vt.json, .gslot.log) opaque; no regex hit; no /home/<user> literal',
 job_sh='KH job.sh command lines (scan1.out:2848-2861) contain only #SBATCH resources, $ROOT/b/{a,g,c0,r8}.py, $ROOT/k/launch.json, b/r.sh; opaque; no regex hit',
 submit_wrapper='drv_cp/go_submit_canary_delta_32337655.sh (930450480307516b, in DRIVER_SHA256SUMS): argv bash -s -- <GO sha>; python3 -I -B - $BUN $KH $GO_SHA; squeue -u $USER -h -o %i|%j|%P|%T|%R; sacct -X -n -P -S 2026-11-17 --name a15_cot_ap6ed2c7aa; sacct -j 171377 (a15_cot_ap673bc60f); env -u PROOF_JOB bash s.sh; env set TZ, PYTHONDONTWRITEBYTECODE, ADMISSION_JOB=172180, ADMISSION_KIT=/project/community/jjyeung/okh7/x_7f1589c1.f172180; writes BUN/go.json, training.{lock,started,sbatch.out,job.id,json}; stdout words PASS/REFUSED/UNCERTAIN/SUBMITTED; mode CANARY_DELTA. All opaque. The word "Cprime" appears in the stdin-delivered comment line 2 and in the refusal text "REFUSED: Cprime identity" (printed only on refusal, to the operator session); not a forbidden-class word, never in argv, env, job name or Orchard log name. No /home/<user> literal.',
 home_literal='only inherited KH b/c.sh:351 (scan1.out:2901, inherited-accepted)')
rec=dict(verdict='CLEAN',anon_ok_written=True,reviewer='review_cpanon (Devin Opus, trinity-3-30)',
 config_identity='774503e26f274a10c96ad06210d339c49ebc9a704ac254df81f389b0da4d98a1',
 operator_archive_sha256='3233765535fc95eb34b876b2e96895b5f684bd8b4e6c5c93f9e23123d320317b',
 package='R1 continuation Cprime: BUN /project/community/jjyeung/okh7/i_ee227714, KH /project/community/jjyeung/okh7/x_ee227714, run 6ed2c7aa, job a15_cot_ap6ed2c7aa',
 precedent='events/review_r1anon7/ANON_SCAN_R1C4.json and ANON_OK.json (archive 08f3a7b2, manifest 635c5335, scan 53f13107, CLEAN)',
 rule='ORCH 1557Z item 1 (inherited sealed names stay; every NEW visible name stays clean; private 0700 trees are not visible) and ORCH 1758Z (in-job file and log contents in 0700 trees exempt; the account home path token accepted)',
 regex=dict(operator=op.pattern+' (re.I; drv_cp/scan_body.py)',precedent=PRE+' (as r1anon7)'),
 inputs=dict(scan='/scratch/jjyeung/orch_n30/r1_ops6/work/xfer/scan1.out',scan_sha256=SSHA,manifest_sha256_in_scan=MAN,
  scan_script='r1_ops6/rec/r1_ops/work/drv_cp/scan1.sh, scan_body.py',
  archive='/scratch/jjyeung/orch_n30/r1_ops6/cp/out/p_32337655.tar',archive_sha256='3233765535fc95eb34b876b2e96895b5f684bd8b4e6c5c93f9e23123d320317b',
  archive_extracted='/scratch/jjyeung/orch_n30/r1_ops6/work/ex_32337655',
  archive_check='43/43 tar members byte-equal to ex_32337655; 43 member pins equal drv_cp/CERTIFICATE_REQUIREMENTS.json external',
  member_diff_vs_C4='BINDING.json, config.json, e.txt, ids.json, jb.sh, s.sh, sums.txt changed; p_05b8ac69.sh -> p_6ed2c7aa.sh; added c4.json, z.json, records/z.json; 32 members byte-equal to ex_08f3a7b2',
  previous_record='events/review_r1anon7/ANON_SCAN_R1C4.json (C4 scan file not available; classified texts used)',
  rulings=['events/r1_ops/20261117T1557Z_ORCH_ANSWER_bind_v7_card_v3.md item 1','events/r1_ops/20261117T1758Z_ORCH_ANSWER_anon_hits_exempt_submit_proof1.md']),
 sections={k:v for k,v in secs.items()},
 counts_by_class=dict(cnt,**{'new-visible':cnt.get('new-visible',0)}),
 counts_note=f'{len(hits)} scan lines match the operator or precedent regex ({uniq} distinct texts); every one equals a review_r1anon7 classified text after token normalization 7f1589c1->ee227714, 05b8ac69->6ed2c7aa; all {len(d["hits"])} r1anon7 hits are present; 0 unaccounted; 0 new-visible',
 hits=hits,new_member_content=new_content,gate_check=gate,new_visible_hits=[],
 not_observable='Orchard not contacted; deployed KH bytes known only via scan listing; KH SHA256SUMS bound by manifest 2b8242f0 in scan')
raw=(json.dumps(rec,indent=1,sort_keys=True)+'\n').encode()
Path('ANON_SCAN_CPRIME.json').write_bytes(raw)
ext=json.load(open('external.json'))
cert=dict(status='CLEAN',hits=0,reviewer='review_cpanon (Devin Opus, trinity-3-30)',
 config_identity=rec['config_identity'],operator_archive_sha256=rec['operator_archive_sha256'],manifest_sha256=MAN,scan_sha256=SSHA,
 scan_record='events/review_cpanon/ANON_SCAN_CPRIME.json',
 exemption_record='events/r1_ops/20261117T1758Z_ORCH_ANSWER_anon_hits_exempt_submit_proof1.md',
 exemption_records_cited=rec['inputs']['rulings'],external=ext,
 inherited_accepted=cnt['inherited-accepted'],exempt_content=cnt['exempt-content'],
 private_tree_contents_accepted=[],inherited_token_accepted=[])
Path('ANON_OK.json').write_text(json.dumps(cert,indent=1,sort_keys=True)+'\n')
print(cnt,uniq,len(hits),secs,hashlib.sha256(raw).hexdigest())
