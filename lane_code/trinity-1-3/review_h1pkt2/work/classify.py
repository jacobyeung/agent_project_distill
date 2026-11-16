import json
from collections import Counter,defaultdict
W='/scratch/jjyeung/orch_n30/review_h1pkt2/work'
hits=json.load(open(W+'/raw_hits.json'))
VIS={('derived_kit','b/c.sh',11):'compute-node argv: R feeds IN and part paths (tar -x -f $IN/e00|d00, sha_is, p0.sh python argv)',
     ('derived_kit','b/c.sh',102):'compute-node argv: mv models--Qwen--Qwen3.5-9B (model word)',
     ('derived_kit','b/c.sh',369):'job env: STUDENT_* variable names (method word student)',
     ('derived_kit','b/c.sh',370):'job env: STUDENT_MODEL_ROOT',
     ('derived_kit','b/c.sh',371):'job env: STUDENT_FRAME_ROOT_MAP',
     ('derived_kit','b/c.sh',375):'job env: STUDENT_PRESERVE_CHECKPOINTS',
     ('derived_kit','b/c.sh',429):'compute-node argv: gcsput.py split (literal project word)',
     ('derived_kit','b/r.sh',61):'job env: STUDENT_IO_THREADS'}
CLEAN={('derived_kit','b/c.sh',17),('derived_kit','b/c.sh',346)}
out=[];cnt=Counter();perfile=defaultdict(Counter)
for h in hits:
    k=(h['surface'],h['file'],h['line'])
    if k in VIS: c='visible';h['why']=VIS[k];h['origin']='inherited from sealed source kit 07ca49df (D0); unchanged by H1'
    elif h['surface']=='upload' and h['file']=='over.json' and 'distill' in h['match'].lower():
        c='visible';h['why']='deployment part path; derived into k/0.json and passed to cat $parts (c.sh:151) on compute nodes';h['origin']='inherited: all 100 H1 distill part paths are a subset of D0 k/0.json (111); none new'
    elif k in CLEAN: c='visible-clean';h['why']='argv/path but matched only /home/jjyeung; no project word'
    else: c='exempt-content'
    h['class']=c;cnt[c]+=1;perfile[c][h['surface']+':'+h['file']]+=1
    if c!='exempt-content': out.append(h)
res=dict(reviewer='review_h1pkt2 (Devin, trinity-1-3)',
 package=dict(upload_tar='p_d1279a8677c91e57.tar',sha256='d1279a8677c91e577d67933139bd52e320d9054b999d99b2d9a2b447d794ceb2',transport_orch_h1_sh='87fb17b7c50f675122ccce6f2bc8aad10f6ec2bf7312ece25cdfc19c94ee1acb',gate_patch='f240e251f52780468c43bd8e4274ab0c416e1ed46a18b029a9bc0f0ef892312c',trainer_tar='25f1c3a7394564d9287ba382fa58c476c4fb17d20063f5b643937d388339a4ec',derived_kit_manifest='SHA256SUMS.txt of fresh empty-review derivation == cont_ops build/fx (byte-identical)'),
 rule='ORCH 1731Z: contents of shipped files exempt; job names, paths, argv, env, logs, sbatch line must carry no project/benchmark/dataset/method word',
 scanned=dict(upload_members=25,trainer_tar_files=796,transport=['orch_h1.sh','fin_h1.sh','build/g_patch.sh'],derived_kit='build/fx job.sh, job8.sh, b/*, b/sa/* (runtime scripts as derived)'),
 pattern=r'(?i)scannet(pp)?|arkit\w*|scene\d{4}|vsi[-_ ]?bench|vsti?bench|dsibench|\bvsi\b|revsi|qwen[\w.-]*|\bsplit\b|distill\w*|\bqgen\b|gemini|/scratch/jjyeung|/home/jjyeung|orch_n\d+|agent_project\w*|\bteacher\b|\bstudent\w*|spatial|benchmark\w*|hypersim|multiscan|scanqa|sqa3d|\bvqa\b (superset of the builder prescan pattern)',
 prescan_reconciliation=dict(prescan_hits=383,R0_ROOMS_txt=372,h1_r0_py=11,classification='exempt-content (shipped file contents inside the trainer tar, extracted only under 0700 BUN/t)'),
 counts=dict(cnt),
 visible_surfaces_checked=dict(job_name='a15_cot_ap5ee9da63 (clean)',sbatch_line='s.sh: -J a15_cot_ap5ee9da63 -o /dev/null -e $KH/o/%j.err -A mt01 ... $BUN/jb.sh (clean)',workdir='/project/community/jjyeung/okh7/i_1be16f28 (clean)',paths='okh7/i_1be16f28, x_4b3114cf, r/766136c1, /tmp/jjyeung/a_17c4ffa4 (clean); upload member names all opaque',login_argv='orch_h1.sh, o.sh, r.py, g.sh (incl. bwrap argv), z.sh, s.sh, fin_h1.sh, g_patch.sh: clean; g.sh no longer reads the distill path (first-review F1 fixed)',gcs='q8/8865619b/17c4ffa4_* (clean)',logs='KH/o/%j.err, o/*.w.steps, o/gcs.log (names clean)'),
 visible_hits=out,
 visible_via_variable=[dict(file='b/c.sh',lines=[13,115,117,151,174],text='IN=$R/in; sha_is/tar -x -f "$IN/e00|d00"; cat $parts',why='expand to /project/community/jjyeung/distill/okit/... in compute-node argv'),dict(file='b/p0.sh',lines=[12],text='/usr/bin/python3 -I - ... "$IN" ...',why='distill path in python argv')],
 exempt_by_file={k:dict(v) for k,v in perfile.items() if k=='exempt-content'},
 new_visible_exposure_from_h1=False)
json.dump(res,open('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_h1pkt/ANON_SCAN.json','w'),indent=1)
json.dump(res,open(W+'/../ANON_SCAN.json','w'),indent=1)
print(cnt,len(out))
