import json,re,hashlib,difflib,collections
W='/scratch/jjyeung/orch_n30/r1_ops/work'
EV='/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events'
sha=lambda b:hashlib.sha256(b).hexdigest()
op=re.compile(r'split|revsi|vsibench|vsi|distill|qgen|scannet|arkit|qwen|sft|student|benchmark|eval',re.I)
pr=re.compile(r"(?i)scannet(pp)?|arkit\w*|scene\d{4}|vsi[-_ ]?bench|vsti?bench|dsibench|\bvsi\b|revsi|qwen[\w.-]*|\bsplit\b|distill\w*|\bqgen\b|gemini|/scratch/jjyeung|/home/jjyeung|orch_n\d+|agent_project\w*|\bteacher\b|\bstudent\w*|spatial|benchmark\w*|hypersim|multiscan|scanqa|sqa3d|\bvqa\b")
scanraw=open(W+'/drv_c1/scan1.out','rb').read(); C=scanraw.decode().splitlines()
A=open(W+'/drv_p5/scan1.out').read().splitlines()
norm=lambda s:s.replace('69d2930d','7f1589c1').replace('673bc60f','05b8ac69')
sm=difflib.SequenceMatcher(None,[norm(x) for x in A],C,autojunk=False)
amap={};changed=[]
for t,i1,i2,j1,j2 in sm.get_opcodes():
  if t=='equal':
    for k in range(i2-i1): amap[j1+k+1]=i1+k+1
  else: changed+=list(range(j1+1,j2+1))
r5=json.load(open(EV+'/review_r1anon5/ANON_SCAN_R1PA5.json'))
byline={h['line']:h for h in r5['hits']}
# section bounds in C
def idx(prefix): return next(i+1 for i,l in enumerate(C) if l.startswith(prefix))
sec=dict(new=[2,idx('INHERITED NAMES')-1],inh=[idx('INHERITED NAMES')+1,idx('SEALED SCRIPT')-1],cmd=[idx('SEALED SCRIPT')+1,idx('GREP NEW')-1],grep_new=[idx('GREP NEW')+1,idx('GREP INHERITED')-1],grep_inh=[idx('GREP INHERITED')+1,idx('PACKET ')-1])
hits=[];dups=0;unacc=[]
for n,l in enumerate(C,1):
  if not (op.search(l) or pr.search(l)): continue
  a=amap.get(n)
  if a in byline:
    h=byline[a]
    hits.append(dict(cls=None,**{}) if False else dict(**{'class':h['class'],'file':'drv_c1/scan1.out','line':n,'matches':h['matches'],'prior_line':'drv_p5/scan1.out:'+str(a),'section':h['section'],'text':l,
      'why':h['why'].split('; byte-identical line carried')[0]+'; carried from review_r1anon5 (ANON_SCAN_R1PA5.json, drv_p5/scan1.out:%d) identical after token normalization (69d2930d->7f1589c1, 673bc60f->05b8ac69)'%a}))
  elif a is not None: dups+=1
  else: unacc.append(n)
assert not unacc, unacc
cnt=collections.Counter(h['class'] for h in hits)
chg=[dict(file='drv_c1/scan1.out',line=n,text=C[n-1],regex_hit=bool(op.search(C[n-1]) or pr.search(C[n-1])),**{'class':'clean new name/argv/command line'}) for n in changed]
assert not any(c['regex_hit'] for c in chg)
rec=dict(
 reviewer='review_r1anon6 (Devin Opus, trinity-1-3)',
 package='R1 vehicle P continuation C (resume of A at step 200) Orchard kit: BUN /project/community/jjyeung/okh7/i_7f1589c1, KH /project/community/jjyeung/okh7/x_7f1589c1, run 05b8ac69, job a15_cot_ap05b8ac69',
 config_identity='6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74',
 operator_archive_sha256='6a5c7d009a19cb5bac690b864f2be68bb5cebc29649923c93da36328d0f96888',
 rule='ORCH 1557Z item 1 (inherited sealed names stay; every NEW visible name stays clean; private 0700 trees are not visible) and ORCH 1758Z (in-job file and log contents in 0700 trees exempt; the account home path token accepted)',
 precedent='events/review_r1anon5/ANON_SCAN_R1PA5.json and ANON_OK.json (packet A fix 12, archive 9dd2fbb7, CLEAN)',
 regex=dict(operator='(?i)split|revsi|vsibench|vsi|distill|qgen|scannet|arkit|qwen|sft|student|benchmark|eval (drv_c1/scan_body.py)',precedent=pr.pattern+' (ANON_SCAN_R1P.json), applied to every scan1 line'),
 inputs=dict(scan='/scratch/jjyeung/orch_n30/r1_ops/work/drv_c1/scan1.out',scan_sha256=sha(scanraw),manifest_sha256_in_scan='d008b39abda96b911540cfe0da53875da1c520a7329cb73a285c8b41010f2212',
   previous_scan='drv_p5/scan1.out (sha 440b5c25)',archive='/scratch/jjyeung/orch_n30/r1_ops/work/snap_6a5c7d00/out/p_6a5c7d00.tar',archive_sha256='6a5c7d009a19cb5bac690b864f2be68bb5cebc29649923c93da36328d0f96888',
   archive_extracted='/scratch/jjyeung/orch_n30/r1_ops/work/ex_6a5c7d00',archive_check='40/40 tar members byte-equal to ex_6a5c7d00; 40 member pins equal drv_c1/CERTIFICATE_REQUIREMENTS.json external',
   member_diff_vs_A='added a0.json (byte-equal to A config.json), c0.py, r4.py, p_05b8ac69.sh; removed p_673bc60f.sh; changed BINDING.json, config.json, d.py, e.txt, ids.json, jb.sh, p.py, s.sh, sums.txt; 27 members byte-equal to A',
   proof_embedded_sha256='861b540bef15666fd8dc97fb6999e495743613b1c5e0573117681aec45e064b9 (decoded from p_05b8ac69.sh line 10; equals in-script pin)'),
 sections=sec,
 counts_by_class={'inherited-accepted':cnt['inherited-accepted'],'exempt-content':cnt['exempt-content'],'new-visible':0},
 counts_note='%d hits, each carried with its class from review_r1anon5 at an unchanged (token-normalized) scan line; %d further regex-matching lines are unchanged duplicates of a classified GREP-section hit; 0 unaccounted regex lines; 0 regex hits among the %d changed or added scan lines'%(len(hits),dups,len(changed)),
 scan_diff_vs_r1anon5=dict(changed_or_added_lines=changed,note='all classified clean: new opaque names a0.json, c0.py, r4.py, rc1.txt, rc2.txt, b/c0.py, b/r4.py, k/a0.json, k/c0af7444.json; A record_key staging dests ap/69d2930d/*; export parts m400/m600; proof argv -p bootstrap/general -t 04:00:00; s.sh:44 sbatch -t 24:00:00; p_05b8ac69.sh:2 -p general; jb.sh:3, job.sh:7 24:00:00; job.sh:20 python3 -I $ROOT/b/c0.py $ROOT $RUN; c.sh:400 rsync -rt --chmod=D700; r.sh/i.py line shifts; PACKET/MANIFEST',lines=chg),
 new_member_content=[
  dict(id='E5',member='c0.py (BUN/c0.py, KH/b/c0.py)',matches='vqa at :74,:83,:228 (stream key literals); .split() at :117,:127,:141',**{'class':'exempt-content'},why='Python source contents inside 0700 BUN and KH (b/ 0500 within 0700 KH); argv is python3 -I $ROOT/b/c0.py $ROOT $RUN (opaque paths); errors are opaque c0:NN codes; fixture result keys status, fixture, run, step, config; never argv, env, job name or log text; ORCH 1758Z'),
  dict(id='E6',member='r4.py (BUN/r4.py, KH/b/r4.py)',matches='.split at :62,:63',**{'class':'exempt-content'},why='Python source contents in 0700 trees; messages are fixed English resource errors; ORCH 1758Z'),
  dict(id='E7',member='config.json, a0.json, BINDING.json (BUN and KH k/a0.json)',matches='inherited A config tokens (ARKIT_*, benchmark_scene_exclusions, vqa, student_* etc.)',**{'class':'exempt-content'},why='a0.json byte-equal to A config.json; config.json and BINDING.json differ from A only in 13 leaves each (continuation block, stop 600, milestones 400/600, run/store/record keys, output paths runs|f/05b8ac69, job_name a15_cot_ap05b8ac69, proof_partition general, time_limit 24:00:00), none matching either regex; contents in 0700 BUN: E2 class, ORCH 1758Z')],
 proof_script_check=dict(argv='p_05b8ac69.sh differs from A p_673bc60f.sh (token-normalized) only at line 2 (-p general), line 10-11 (embedded source and pin) and line 13 (identity); exec "$PY" -I -B - "$1" with source on stdin',
   embedded_diff='decoded 861b540b vs A b7ce4ec9: proof partition also accepts bootstrap and checks allowed_partitions; directory_modes() factored out; resume_fixture() loads KH/b/c0.py and runs c0.fixture on work/c0 with k/a0.json and k/7.json; checks.resume_pointer added to required set; no new argv, env or log word; no regex hit in added lines; unchanged line 130 keeps inherited student_pilot.loader_audit in stdin source (inherited-accepted as in r1anon5)',
   home_literal='no /home/<user> literal in p_05b8ac69.sh, decoded source, s.sh, jb.sh, c0.py or r4.py; only inherited KH b/c.sh:351 bwrap token /home/jjyeung (inherited-accepted, scan1 line carried)'),
 gate_check=dict(s_sh='44 lines; canary branch removed; argv sha256sum -c sums.txt, env -u PYTHONOPTIMIZE python3 -I -B - "$KH" "$BUN" (source on stdin), training sbatch s.sh:44 -J a15_cot_ap05b8ac69 -o /dev/null -e $KH/o/%j.err -A mt01 -p advanced -N1 --ntasks=1 --gres=gpu:4 -c 48 --mem=800G -t 24:00:00 --signal=B:USR1@3600 --no-requeue $BUN/jb.sh; env read PROOF_JOB; messages fixed assertion text; no regex hit',
   jb_sh='differs from A only at :3 (#SBATCH -t 24:00:00), :46 export names m400/m600, :120 deadline 86400; .split at :194,:195,:220 are unchanged A Python source (inherited); log/record lines carry job ids, steps, hashes, opaque slot names and q8/8865619b/05b8ac69_* object names',
   job_sh='deployed KH job.sh known via scan COMMANDS lines and d.py transforms: --time=24:00:00; export TK_ALLOCATION_MODE=u|p by SLURM_JOB_PARTITION; export TK_KIT_HOME="$ROOT"; /usr/bin/python3 -I "$ROOT/b/c0.py" "$ROOT" "$RUN"; r.sh adds export TK_ALLOCATION_MODE="$1"; r8.py reads TK_KIT_HOME; g.py/i.py call r4.allocation; all env keys opaque TK_* names; clean',
   d_py_p_py='operator-side derivation and proof sealer: new argv choice --partition bootstrap; no new forbidden word'),
 not_observable='Orchard was not contacted; deployed KH bytes (job.sh, b/*.py after d.py transforms, k/c0af7444.json, rc1/rc2.txt) are checked by scan listing, d.py transforms and name only; 0700/0500 modes are asserted by scan_body.py, not observed by me',
 other_exempt=r5['other_exempt'],
 new_visible_hits=[],
 hits=hits,
 verdict='CLEAN', anon_ok_written=True)
open('ANON_SCAN_R1C.json','w').write(json.dumps(rec,indent=1,sort_keys=True)+'\n')
print(cnt,dups,len(changed))
