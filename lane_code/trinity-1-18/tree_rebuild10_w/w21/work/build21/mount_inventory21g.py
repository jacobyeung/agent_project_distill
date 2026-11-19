from pathlib import Path
import datetime,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21g'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
print(datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
args=J.load(D/'proofs/view/after.json');mounts=[];i=1
two={'--ro-bind','--bind','--dev-bind','--symlink'};one={'--tmpfs','--dir','--proc','--remount-ro'}
while i<len(args):
    op=args[i]
    if op in two:mounts.append(dict(order=len(mounts)+1,operation=op,source=args[i+1],destination=args[i+2]));i+=3
    elif op in one:mounts.append(dict(order=len(mounts)+1,operation=op,destination=args[i+1]));i+=2
    elif op in ('--uid','--gid'):i+=2
    elif op=='--unshare-user':i+=1
    else:raise ValueError(op)
AS='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung';AL=AS.replace('/scratch/','/lustre/');X=AS+'/ap/8865619b'
N='${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID}';P='/project/community/jjyeung/c7d31ddd'
rows=[]
def row(name,path,source,category,evidence):rows.append(dict(name=name,destination=path,source=source,availability=category,evidence=evidence))
row('host top-level entries','/* /.[!.]* /..?* except /home,/dev,/proc','same host entry or readlink target','exists on host by -e/-L guard; bwrap starts with writable empty root','P b/c.sh:343-347; concrete Trinity entries below')
row('/tmp (overlay)','/tmp','tmpfs','exists from top-level ro bind; writable private parent after overlay','kit.py generated tk_bwrap; MOUNT_REDUCTION.json')
row('Q_ROOT',N,N,'host created by bootstrap; creatable in /tmp tmpfs or already exists at SLURM_TMPDIR','b/z.py bootstrap; tk_stage before tk_bwrap; restored before child binds')
row('/dev','/dev','/dev','special dev-bind; parent is namespace root','P tk_bwrap')
row('/proc','/proc','procfs','special proc mount; parent is namespace root','P tk_bwrap')
row('/home','/home','tmpfs','creatable at namespace root; remounted read-only last','P tk_bwrap')
row('/home/jjyeung','/home/jjyeung','--dir','creatable inside preceding /home tmpfs','P tk_bwrap')
row('AS',AS,N+'/s/aws/u','read-only host /scratch ancestor; already exists on production host (inferred)','Orchard job 173051 reached Q_NS after this bind; absent elsewhere would require an operator-provided host path')
row('AL',AL,N+'/s/aws/u','read-only host /lustre ancestor; already exists on production host (inferred)','Orchard job 173051 reached Q_NS after this bind; absent elsewhere would require an operator-provided host path')
row('X',X,N+'/x','inside earlier read-only AS bind; target exists in U/ap/8865619b','tk_stage creates U/ap/K before tk_bwrap; this bind makes X writable')
row('X/runs',X+'/runs',N+'/rp','inside earlier writable X; also created in NX/runs','tk_nx creates NX/runs')
row('X/u',X+'/u',N+'/s/aws/u/ap/8865619b/u','inside earlier writable X; also created in NX/u','tk_stage creates NX/u and source U/ap/K/u')
row('X/data2root',X+'/data2root',N+'/s/c7d31ddd/data2root','inside earlier writable X; also created in NX/data2root','tk_nx and tk_stage')
row('X/models',X+'/models',N+'/s/c7d31ddd/runs/aws128p_20261025/models','inside earlier writable X; also created in NX/models','tk_nx and tk_stage_model')
row('P',P,N+'/s/c7d31ddd','read-only host /project ancestor; already exists on production host (inferred)','Orchard job 173051 reached Q_NS after this bind; no pool directory is created by the fix')
row('EPOCHS','/home/jjyeung/6d00e578',N+'/s/epochs','creatable inside earlier /home tmpfs','P tk_bwrap; /home remount-ro follows this bind')
row('TK_JOBDIR',N+'/j',N+'/j','host created by tk_stage; inside restored writable Q_ROOT','tk_stage and tk_env create jobdir/tmp before tk_bwrap')
row('Q_NS','/tmp/q_22c714e1',N,'absent host destination under read-only /tmp before fix; creatable in private tmpfs after fix','MOUNT_REDUCTION.json and VIEW.json reproduce failure and success')
J.write(D/'MOUNTS.json',dict(mode='q',job_example='173051: N=/tmp/q_22c714e1_173051 only if SLURM_TMPDIR is unset; its actual production value is unavailable here.',
    production=rows,trinity_argument_order=mounts,source='ext/pwrap/b/c.sh:339-366; decoded kits/q/k/j.json; supplied Orchard job 173051 failure',
    qualifications='No Orchard host inspection was performed. AS/AL/P host existence follows from the reported ordered bwrap failure, not a new stat on Orchard. The stand-in test creates only prefixed AS/AL/P host targets under L.'))
stages=[
 ('bwrap mounts','Exact generated function, before failure and after true/marker success; AS/AL/P use documented L prefix.','VIEW.json; TMP_VIEW.json','Production mounts and all GPU driver paths still need the real job.'),
 ('b/g.py GPU guard','Real in-view entry refuses E42 on CPU.','VIEW.json','No GPU availability, driver or 80-GiB capacity claim.'),
 ('b/a.py extraction and kit verification','Real in-view q entry authenticates/extracts the shipped source archive and verifies kit.','VIEW.json; NATIVE_VIEW.json','Production venv import compatibility is untested.'),
 ('staged pins, config/card and room audit','Native functions pass on existing authenticated synthetic-fixture inputs, then refuse R1_PROOF_FRAME_HOST_REQUIRED on Trinity.','NATIVE_VIEW.json','Production stores/room certificates and frame-host boundary remain unproved.'),
 ('persisted export receipt and component evidence','Focused/resolver readers exercise pinned identity and default-deny paths on CPU.','SUITES.json; TESTS.json','DEFERRED production evidence must remain a refusal.'),
 ('opener witness and handover target','Focused tests exercise retained step-544 and keep/reset contracts.','SUITES.json; TESTS.json','Production witness has not run inside this view.'),
 ('s1_routing.build; compose_native; s1_admission.prepare','Existing CPU fixture tests cover producers/readers; this in-view run stops at the frame-host boundary.','SUITES.json; NATIVE_VIEW.json','Real RGB/labels, joins and staged-store composition remain unproved.'),
 ('bind_prepared; production_audit','Focused admission checks cover fixture invariants.','SUITES.json; TESTS.json','No production population or capacity assertion here.'),
 ('final bind_handover and persisted admission','Focused tests retain authenticated manifest/identity checks and export-only proof restriction.','SUITES.json; TESTS.json','Production final prepared-store binding remains unproved.'),
 ('load base model from staged snapshot; init export','Kit/resolver tests check snapshot layout and authenticated native export sibling paths.','SUITES.json; TESTS.json','No 9B weights, production tokenizer execution, CUDA load, memory fit or kernel check.'),
 ('every rank first batch and finite loss','Focused tests cover fixture behavior; no production first batch ran here.','SUITES.json; TESTS.json','All configured ranks/streams, RGB forward, loss and GPU memory need production proof.'),
 ('b/d.py room count','Exact in-view entry reports both synthetic rows using real pinned room authority and withheld reader.','ROOM_VIEW.json','Not a production census; this report cannot admit the proof.'),
 ('b/o.py result archive','Existing kit/naming controls validate output names and GO=false.','SUITES.json; TESTS.json','No production pool write or upload is attempted.')]
J.write(D/'LOOKAHEAD.json',dict(GO=False,scope='All listed production stages remain unrun after the reported Orchard namespace failure; CPU checks are limited as stated.',
    stages=[dict(stage=s,cpu_proves=c,evidence=e,unproved=u) for s,c,e,u in stages]))
