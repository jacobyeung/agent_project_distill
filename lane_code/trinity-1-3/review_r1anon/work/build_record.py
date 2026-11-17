import re,json,hashlib,collections
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/r1_ops/work');EX=W/'ex_c5f3847d';SCAN=W/'drv/scan1.out'
EV=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_r1anon')
RX=r"(?i)scannet(pp)?|arkit\w*|scene\d{4}|vsi[-_ ]?bench|vsti?bench|dsibench|\bvsi\b|revsi|qwen[\w.-]*|\bsplit\b|distill\w*|\bqgen\b|gemini|/scratch/jjyeung|/home/jjyeung|orch_n\d+|agent_project\w*|\bteacher\b|\bstudent\w*|spatial|benchmark\w*|hypersim|multiscan|scanqa|sqa3d|\bvqa\b"
R=re.compile(RX);P=re.compile(r'split|revsi|vsibench|vsi|distill|qgen|scannet|arkit|qwen|sft|student|benchmark|eval',re.I)
L=SCAN.read_text().splitlines()
sec=lambda n:'NEW' if n<135 else 'INHERITED' if n<1907 else 'COMMANDS' if n<2032 else 'GREP_NEW' if n<2039 else 'GREP_INHERITED' if n<2674 else 'TAIL'
hits=[];cnt=collections.Counter()
for n,l in enumerate(L,1):
  s=sec(n)
  if s not in ('GREP_NEW','GREP_INHERITED') and not (s=='COMMANDS' and R.search(l) and not P.search(l)): continue
  m=sorted({x.group(0) for x in R.finditer(l)}|{x.group(0) for x in P.finditer(l)})
  if not m: continue
  if ' :: ' in l:
    if s=='GREP_NEW': cls,why='exempt-content','new tar member name inside t.tar / KH k/t_5e1514ef9d91bee8.tar (0700 trees); archive member names are not visible names under the rule; extraction stays in 0700 trees'
    else: cls,why='inherited-accepted','inherited tar member name (in H k/7.json files) inside 0700 tree; ORCH 1557Z item 1'
  elif '/distill/okit/' in l: cls,why='inherited-accepted','inherited staging locator (unchanged k/0.json entry of H x_3fdda0fb); same 43 distill part paths accepted ORCH 2309Z; passed to cat $parts (c.sh) on compute node'
  elif l.endswith('benchmark_scene_exclusions.json'): cls,why='inherited-accepted','inherited KH file name (in H SHA256SUMS) inside 0700 KH'
  else: cls,why='inherited-accepted','inherited KH runtime b/c.sh command line (same class as the 9 c.sh/r.sh hits accepted ORCH 2309Z)'
  cnt[cls]+=1
  hits.append(dict(file='drv/scan1.out',line=n,section=s,matches=m,text=l[:300],class_=cls,why=why))
for h in hits:h['class']=h.pop('class_')
prf='/scratch/jjyeung/orch_n30/review_r1anon/work/proof_embedded.py (decoded from BUN/p_26cc98b7.sh line 9, sha256 15550426...4390)'
la='t.tar :: student_pilot/loader_audit.py (NEW member)'
newvis=[
 dict(id='N1',surface='log line: KH/o/<job>.proof.log',producer=prf+':114 appends loader audit to entry.sh; :168/:272 stdout+stderr -> proof.log',source=la+':138 print_breakdown',
  certainty='certain (key set fixed in code; audit() runs with local_vqa_only=False)',matches=['scannetpp','scannetppv2','scannet','arkitscenes'],
  text='{"loader_draw_breakdown": {... "routing_absolute_distance": {"eligible": {"arkitscenes/": N, "scannet/": N, "scannetpp/": N, "scannetppv2/": N, "unknown": N}, "drawn": {same keys}, ...}}}',
  origin='loader_audit.py:90 PREFIXES, :134 eligible/drawn dicts over PREFIXES',class_='new-visible'),
 dict(id='N2',surface='log lines: KH/o/<job>.proof.log',producer=prf+':114/:168',source=la+':204 loader_trace rows',
  certainty='certain for "stream": "vqa" (config.json type_mix.streams = routing, vqa); probable further hits in row fields database/qid/question_type/target/frames (not observable locally)',matches=['vqa'],
  text='{"database": ..., "family": <cell>, "frames": [...], "index": i, "loader_trace": true, "qid": ..., "question_type": ..., "stream": "vqa", "target": ..., "target_sha256": ...}',
  origin='new in this kit (loader audit added to the proof program)',class_='new-visible'),
 dict(id='N3',surface='log line: KH/o/<job>.proof.log',producer=prf+':114/:168',source=la+':220 print(required_families)',
  certainty='certain',matches=['vqa'],
  text='{"required_families": {"checked": {"vqa/appearance": {...}, ...}, "required": {"vqa": [...], "routing": [...]}, ...}}',
  origin='vehicle_p.py:34 required dict key vqa, :55 checked keys stream/name',class_='new-visible'),
 dict(id='N4',surface='argv on the shared proof node (ps): nested bwrap namespace probe',producer=prf+':70,:72 namespace_probe',source='p_26cc98b7.sh embedded source (NEW function vs H1 sealed proof)',
  certainty='certain',matches=['/home/jjyeung'],
  text='<bwrap> --ro-bind ... --dev-bind /dev /dev --proc /proc --tmpfs /home --dir /home/jjyeung --remount-ro /home --unshare-user --uid U --gid G /bin/bash -c \'test -r /proc/self/status && test -w /dev/null && test -d /home/jjyeung\'',
  origin='new argv; same token as inherited c.sh:351 tk_bwrap (--dir /home/jjyeung), which also runs in this job; ORCH may accept it as that inherited token',class_='new-visible'),
]
for h in newvis:h['class']=h.pop('class_')
cnt['new-visible']=len(newvis)
members=sorted(str(p.relative_to(EX)) for p in EX.rglob('*') if p.is_file())
content=collections.Counter()
for m in members:
  if m=='t.tar':continue
  content[m]=len(R.findall((EX/m).read_text(errors='replace')))
rec=dict(reviewer='review_r1anon (Devin Opus, trinity-1-3)',package='R1 vehicle P final Orchard kit: BUN /project/community/jjyeung/okh7/i_c5f3847d, KH /project/community/jjyeung/okh7/x_c5f3847d, run 26cc98b7, job a15_cot_ap26cc98b7',
 rule='ORCH 1731Z, reaffirmed 1557Z item 1: file contents of shipped files exempt; inherited sealed names stay accepted; private 0700 trees are not visible; every NEW visible name must be clean: job names, file and directory names outside tar archives, paths, argv, environment, log lines and sbatch lines carry no project, benchmark, dataset, model or method word',
 regex=RX,regex_note='precedent regex (review_h1anon/review_h1pkt); scan1 operator pattern also applied to scan1 lines',
 inputs=dict(scan1_out=str(SCAN),scan_sha256=hashlib.sha256(SCAN.read_bytes()).hexdigest(),scan_lines=len(L),manifest_sha256_in_scan=L[2673].split()[1],
   archive_extracted=str(EX),archive_members=len(members),proof_embedded_sha256='15550426aac3b6bc8f0077e746844a66da549e488f6dba583798e337026a4390'),
 scanned_surfaces={'scan1 NEW names/argv/exports (lines 2-134)':133,'scan1 INHERITED names (136-1906)':1771,'scan1 command lines (1908-2031)':124,'scan1 GREP NEW (2033-2038)':6,'scan1 GREP INHERITED (2040-2673)':634,
   'bundle members read (contents)':len(members),'proof embedded source lines':300,'jb.sh lines (proof runs 1-55; production 1-263)':263,'s.sh lines':43,'new t.tar members read: loader_audit.py, type_mix.py, vehicle_p.py':546},
 counts_by_class=dict(cnt),counts_note='exempt-content and inherited-accepted count scan1 hit lines (640 grep lines + 1 precedent-regex-only command line c.sh:351); new-visible counts distinct surfaces predicted from code (proof not yet run, so proof.log is not observable)',
 hits=hits,new_visible_hits=newvis,
 exempt_content_matches_by_bundle_file={k:v for k,v in content.items() if v},
 other_exempt=['BINDING.json content (/scratch/jjyeung, orch_n30, vqa): record content, read by p.py only','KH/o/<job>.proof.json: receipt record (checks incl. required_families vqa keys), same class as precedent r.json/receipt.json',
   'physical run inputs/l.json, a.json under /tmp/jjyeung/p_26cc98b7_<job> (0700, directory_modes check)','entry.sh heredoc "from student_pilot.loader_audit import main": stdin/file content in 0700 work dir, not argv'],
 inherited_notes=['jb.sh:194,195,220 python -c argv ".split(": jb.sh byte-identical to H1 jb.sh except KH/RUN/RS/NL paths, run token, milestone list and v.py/b0 paths','KH/o/<job>.vt.json (jb.sh:53, runs in the proof): v.py byte-identical to H1; prints inherited distill part paths (inherited_parts_present), the accepted locators',
   'c.sh tk_env env names STUDENT_* and R1_STUDENT_HEX: inherited runtime, noted in review_h1pkt2','Inherited classification of KH files in scan_body.py is by relative name in H SHA256SUMS, not by bytes'],
 conditional_not_counted=['loader audit failure: traceback lines naming student_pilot/loader_audit.py and ValueError text such as "Family draws exceed four times eligible rows: vqa/<cell>" would also land in proof.log'],
 visible_clean=dict(job_name='a15_cot_ap26cc98b7',proof_sbatch='TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable -J a15_cot_ap26cc98b7 -A mt01 -p advanced ... -o KH/o/%j.out -e KH/o/%j.err BUN/p_26cc98b7.sh BUN/a.json',
   sbatch_lines='p_26cc98b7.sh:2-3, jb.sh:3-4, job.sh:2-9 #SBATCH lines',production_sbatch='s.sh: -J a15_cot_ap26cc98b7 -o /dev/null -e KH/o/%j.err ... BUN/jb.sh',
   proof_argv='python3 -I -B - BUN/a.json; outer bwrap --ro-bind / / --proc --dev --bind work/tmp /tmp --tmpfs okh7, --ro-bind per okh7 entry, --tmpfs okh7/r --bind work/slots okh7/r/26cc98b7 --tmpfs KH --ro-bind per KH entry, --bind work/arm|runs, --bind KH/o, /bin/bash -c "set -e; chmod 700 -- $1 $2 $3; exec /bin/bash -s" a KH okh7/r okh7',
   proof_env='SLURM_* plus PATH, HOME=/tmp/jjyeung, TMPDIR=/tmp, TZ, LC_ALL, CUDA_VISIBLE_DEVICES, PYTHONDONTWRITEBYTECODE',
   loader_audit_argv='"${BW[@]}" $PILOT_VENV/bin/python -B - $X (module name on stdin only)',
   jb_proof_prefix_log_lines='w.steps: "wrapper start on <host>; /tmp free N GiB; TK_JOB_START=...", "export sessions present for run 26cc98b7", "staging entries verified", refusals',
   paths='BUN i_c5f3847d, KH x_c5f3847d, okh7/r/26cc98b7, s_22b44165, /tmp/jjyeung/a_26cc98b7, /tmp/jjyeung/p_26cc98b7_<job>/{entry.sh,tmp,slots,arm,runs}, /scratch/fsw/.../ap/c5f3847d/*',
   exports='e.txt 20 destinations q8/8865619b/26cc98b7_{m100,m200,mstop,mstopB,mstopC}.tar.partNN-of-04',
   new_names='all 133 NEW-section lines except the 6 tar member names: 0 regex hits'),
 new_visible_exposure=True,verdict='HITS',anon_ok_written=False)
(EV/'ANON_SCAN_R1P.json').write_text(json.dumps(rec,indent=1)+'\n')
print(dict(cnt),len(hits))
