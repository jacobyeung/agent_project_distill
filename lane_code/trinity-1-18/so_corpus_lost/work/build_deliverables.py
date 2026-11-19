from pathlib import Path
import hashlib, json, re, subprocess, sys

L = Path('/scratch/jjyeung/orch_n30/so_corpus_lost')
I = Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/corpusin')
D = Path('/data2/jjyeung/agent_project_data/distill_design')
A = Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/src')
PY = '/scratch/jjyeung/envs/p1cpu/bin/python'
OUT = L/'out'
W = L/'work'

def stamp():
    return subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip()

def cite(name, line, root=D):
    return f'[{name}:{line}]({root/name}:{line})'

def ev(name, line, root=D):
    return dict(path=str(root/name), line=line, text=(root/name).read_text().splitlines()[line-1])

def status(task, message):
    with (W/'STATUS.md').open('a') as f:
        f.write(f'{stamp()} Task {task}: {message}\n')

pub = [json.loads(x) for x in (W/'index_snapshot/INDEX.jsonl').read_text().splitlines()]
pub_by_job = {}
for n,r in enumerate(pub,1):
    pub_by_job.setdefault(str(r.get('job_id')), []).append((n,r))

def indexed(job):
    return '; '.join(f'`{r["read_id"]}` (published line {n}, {r["item_count"]} items)' for n,r in pub_by_job[str(job)])

lost = dict(
    read_id='CP1_s200_revsi_direct_reported_lost', status='lost',
    export=dict(run=None, step=200, artifact_id=None, artifact_sha256=None),
    model_label='CP1 m200', set='ReVSI official999', vehicle='direct',
    arms=None, job_id=None, item_count=999, official=None, partial=None,
    purpose='Record the explicitly reported loss of the parent ReVSI per-item answers.',
    reported_by='REVSI_DIRECT_STEP544_20261115.md:20,26',
    reported_artifact_prefix='c1a42588',
    last_known_paths=['/scratch/jjyeung/orch_cd/trace_diag/out/normalized.jsonl'],
    path_basis='Derived from design INDEX.md:138 lane output directory and TRACE_DIAGNOSIS_CP1_DEVS1_REVSI_20261112.md:10 filename; this is a normalized multi-journal derivative, not an invented original return path.',
    loss_basis='The ReVSI record explicitly states the parent per-item answers/file are lost. The normalized derivative was in the orch_cd tree on unreachable trinity-2-18. No surviving ReVSI parent row source is named in the consulted records.',
    notes='Record-supported loss, not a fresh remote existence check. The immutable run ID, job ID and exact arm population are not recorded and remain null. The artifact prefix is not a full SHA256 and is not used as a run ID. 999 is a recorded per-run population, not a new measurement. Recovery of any original or normalized parent journal should retire this proposed lost entry.',
    evidence=[ev('REVSI_DIRECT_STEP544_20261115.md',20),ev('REVSI_DIRECT_STEP544_20261115.md',26),ev('TRACE_DIAGNOSIS_CP1_DEVS1_REVSI_20261112.md',10),ev('INDEX.md',138),ev('RECOVERY_MAP_2_18_OUTAGE_20261115.md',7)])
(W/'meta'/f'{lost["read_id"]}.json').write_text(json.dumps(lost,indent=2)+'\n')
(W/'ingest_read.py').write_bytes((I/'ingest_read.py').read_bytes())
cmd=[PY,'-I','-s','-B',str(W/'ingest_read.py'),'lost','--meta',str(W/'meta'/f'{lost["read_id"]}.json'),'--out',str(W/'index_snapshot')]
p=subprocess.run(cmd,text=True,capture_output=True)
(W/'lost_command.log').write_text('UTC: '+stamp()+'\nCOMMAND: '+' '.join(cmd)+'\nEXIT: '+str(p.returncode)+'\nSTDOUT:\n'+p.stdout+'STDERR:\n'+p.stderr)
assert p.returncode == 0,p.stderr
entry=json.loads((W/'index_snapshot/index'/f'{lost["read_id"]}.json').read_text())
# Canonical bytes are exactly the encoding used by ingest_read.py index.
(OUT/'LOST_LINES.jsonl').write_text(json.dumps(entry,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n')
cmd2=[PY,'-I','-s','-B',str(W/'ingest_read.py'),'index','--out',str(W/'index_snapshot')]
p2=subprocess.run(cmd2,text=True,capture_output=True)
with (W/'lost_command.log').open('a') as f:
    f.write('COMMAND: '+' '.join(cmd2)+'\nEXIT: '+str(p2.returncode)+'\nSTDOUT:\n'+p2.stdout+'STDERR:\n'+p2.stderr)
assert p2.returncode==0,p2.stderr

rows=[]
def row(identity, decision, detail, evidence): rows.append([identity,decision,detail,evidence])
row('reader_r1 job 171253; step 544; tower/null and distance/best-candidate', 'INDEXED', indexed(171253), cite('READER_R1_20261117.md',35))
row('reader_r1 job 172456; step 544; room 134', 'INDEXED', indexed(172456), cite('READER_R1_20261117.md',37))
row('D0 run 359fcc3c, step 200; job 170320; dev-S1 + facing; 1,825 items', 'INDEXED', indexed(170320)+'. Missing m200_return_1837Z.tar is not loss of the read. The design record names trinity-0-13 for that mirror, not trinity-1-18.', cite('D0_M200_READ_20261116.md',3)+'; '+cite('D0_M200_READ_20261116.md',7))
row('native_r4 job 170294; step 544; VSTI-450; camera-served native', 'MAY EXIST / RAW RETAINED', '`okh7/n2r/d627d31523064791d2ce3456/result.tar.gz`, recorded SHA prefix 9971853f and 89,790,245 bytes; GCS `q8/n2r/` same token. Identity is explicit, not merely likely. Raw corpus bundle is named in LEFTOVER:4.', cite('VSTI_NATIVE_CAMERA_READ_STEP544_20261116.md',9)+'; '+cite('VSTI_NATIVE_CAMERA_READ_STEP544_20261116.md',37)+'; '+cite('IDENT.txt',57,I))
for job,line,token,count,desc in [(170631,101,'b01ec87a6f29b00029a87','1,050 camera reads','Camera component complete; the whole return reports 1,050/1,536 and FAILED. Token association is inferred from package, count and camera journals, not explicitly job-bound by IDENT.'),(170694,102,'b01ec87a6f29b00029ac6','36 room reads','Token association is inferred from package, room journal and exact 36 count.'),(170706,103,'b01ec87a6f29b00029ad2','369/450 distance reads','Token binding is explicit in the diagnosis; baseline 150, x0.5 150, x2 69.')]:
    row(f'H1-0 job {job}; step 544; own arm; {count}','MAY EXIST / RAW RETAINED',f'`okh7/ae71c903/{token}/result.tar.gz`. '+desc+' Package inputs: `okh7/e6fc152498/p446`.',cite('H1_GT_HEAD_ROUTING_SFT_20261116.md',line)+'; '+cite('H1_0_NOT_SEEN_DIAGNOSIS_20261117.md',3)+'; '+cite('H1_0_NOT_SEEN_DIAGNOSIS_20261117.md',83))
for job,name,line,detail in [
 (169501,'ROUTED_READ_PARITY_PROBE_169501_20261114.md',7,'Native parity probe: 33 generated token IDs; scored population is unrecorded. The record ties the comparison to step-200 export baccafbf at line 12; it does not supply a full run ID or returned corpus item count.'),
 (169605,'ROUTED_READ_FIRST_ITEMS_169605_20261114.md',3,'Step-200 routed pilot; ten item pairs discussed at lines 40–43, scripted and unflagged arms. Local relative return `work_debug_distance/ret/` on trinity-2-18; its absolute parent is not supplied in this record.'),
 (169670,'ROUTED_READ_GEOMETRY_GUARD_169670_20261115.md',3,'Step-544 geometry-failed pilot; `/scratch/jjyeung/orch_cd/leg_s1_review/work_debug_gravity/ret/`. 636 is the planned population (line 23), not an observed completed-item count.')]:
    row(f'Routed pilot {job}','MAY EXIST / UNRESOLVED',detail+' The known Trinity copy is unavailable. The old Orchard pool `/home/jjyeung/okit/evalx_results` is documented, but the family token and membership of this job are not. Do not publish a lost entry without that check.',cite(name,line)+'; '+cite('LEFTOVER.md',7,I)+'; '+cite('ROUTED_READ_PIN_GRAPH_AUDIT_20261114.md',60)+'; '+cite('RECOVERY_MAP_2_18_OUTAGE_20261115.md',52))
row('CP1 m200 parent; ReVSI official999; direct; 999 recorded items','LOST',f'Proposed `{lost["read_id"]}`. Exact run/job/arms unknown. The later ReVSI record explicitly says its per-item file is lost. The trace audit names `normalized.jsonl` under the lost orch_cd lane; this derivative is the named row source, not an original return archive.',cite('REVSI_DIRECT_STEP544_20261115.md',20)+'; '+cite('REVSI_DIRECT_STEP544_20261115.md',26)+'; '+cite('TRACE_DIAGNOSIS_CP1_DEVS1_REVSI_20261112.md',10)+'; '+cite('INDEX.md',138))
row('H1-0 distance precursor 170674; step 544; own arm; first 6 reads','MAY EXIST / POSSIBLE RAW MATCH','Recorded return prefix cb45b439. `ae71c903/b01ec87a6f29b00029ab2` has 6/486 reads and is a plausible match, not proven. Package p446; record describes three looping reads among first six.',cite('H1_GT_HEAD_ROUTING_SFT_20261116.md',112)+'; '+cite('IDENT.txt',10,I))
row('H1-1 run 17c4ffa4, step 100; camera job 170846; 1,050 mode-expanded reads','MAY EXIST / RAW RETAINED','`okh7/ae71c903/bf94a7976a7e900029b5e/result.tar.gz`; re-pinned evaluator bf94a7976a7e9 and exact count establish the association. Check RETURN_ID before ingestion. Scoring job 170903 recomputes the same read; it is not a separate generation read.',cite('H1_GT_HEAD_ROUTING_SFT_20261116.md',104)+'; '+cite('IDENT.txt',20,I))
row('LEG-S1 step 544 direct e193c2a3c / job 169526','MAY EXIST','Old Orchard `okit/evalx_results/e193c2a3c/result.tar.gz`, recorded 39,743,652 bytes and SHA prefix ea97204a. Absent from the published index; do not confuse with D0 readk using e193 membership.',cite('TRINITY_READ_RUNTIME_20261116.md',3)+'; '+cite('RECOVERY_MAP_2_18_OUTAGE_20261115.md',52))
row('LEG-S1 direct step 400 e3da9a577; step 200 bffa0d6ef; b719d20dd (step unrecorded)','MAY EXIST','Old Orchard `okit/evalx_results/` names these tokens; b719d20dd and bffa0d6ef were explicitly unverified in the recovery record. bffa0d6ef has 1,975 recorded items and export prefix baccafbf. Each needs its original return identity and task population.',cite('RECOVERY_MAP_2_18_OUTAGE_20261115.md',52)+'; '+cite('ROUTED_READ_PARITY_PROBE_169501_20261114.md',12)+'; '+cite('ROUTED_READ_PARITY_PROBE_169501_20261114.md',17))
row('Native pilot 9, job 169792, family ebe307cf4','MAY EXIST','Orchard `okit/evalx_results/ebe307cf4/metadata/STAGING.json` and its return are recorded as surviving; run, step, scored items not stated.',cite('RECOVERY_MAP_2_18_OUTAGE_20261115.md',36))
row('b04 own-depth parity read; step 544; 51/636 keys','MAY EXIST','`/scratch/jjyeung/orch_n30/b04_e2ehook/out/proofs/PARITY_own_depth_p0_51rows.jsonl` on trinity-3-30; lane mirror `/scratch/jjyeung/n30_mirror/b04_e2ehook/` on trinity-1-18. Host withdrawal does not prove loss of the saved journal.',cite('E2E_READER_B04_20261116.md',7)+'; '+cite('E2E_READER_B04_20261116.md',12))
row('CP1 m200 dev-S1 direct comparator','MAY EXIST','trinity-1-18 `/scratch/jjyeung/orch_cd/devs1_direct/out`, r5 merge, B2048; covers 150 distance + 36 room shared keys. This is not evidence that the ReVSI parent file survived.',cite('NATIVE_ROUTED_READ_DEVS1_STEP544_20261115.md',22))
row('Official proof 170035 / pb906babb42; proof 169991 / possible pb59bef09f3','MAY EXIST / RAW RETAINED','`okh7/x27ret/pb906babb42/result.tar.gz` has 10 reported items; exact job token documented. pb59bef09f3 has 14 reported items, but the inspected records do not link it explicitly to 169991; keep job ID null.',cite('REVSI_DIRECT_STEP544_20261115.md',24)+'; '+cite('OFFICIAL_VSI_DIRECT_STEP544_20261115.md',27)+'; '+cite('IDENT.txt',70,I))
row('n2r/f4af36fcc1 native probe, step 544','MAY EXIST / RAW RETAINED','39,357,038 bytes; `native/probe/items.jsonl`; job, set and count unrecorded in IDENT. Keep distinct from the K1 head-only native/probe output.',cite('IDENT.txt',62,I))
row('K1 own phase 170235 / ad2472b1be07d4193','NOT A GENERATION READ','Prefill-only captures; zero item files in IDENT. Output `/scratch/jjyeung/k1/own_170235/native/probe` and trinity-3-30 mirror are recorded. Preserve as head evidence; no corpus generation lines can be recovered by adding task inputs.',cite('K1_KILL_TEST_RUN_20261116.md',56)+'; '+cite('K1_KILL_TEST_RUN_20261116.md',57)+'; '+cite('K1_KILL_TEST_RUN_20261116.md',58)+'; '+cite('K1_KILL_TEST_RUN_20261116.md',69))
row('170209, 170228, 170254; H1-0 170620; reader_r1 171143; CPU check 170854','NO SCORED READ PROVEN','VSTI record explicitly says the first three read no item. H1-0 failed at its first namespace call; reader_r1 failed its operator startup; 170854 was a CPU package check. Do not create lost student-row entries from job existence alone.',cite('VSTI_NATIVE_CAMERA_READ_STEP544_20261116.md',37)+'; '+cite('H1_GT_HEAD_ROUTING_SFT_20261116.md',78)+'; '+cite('READER_R1_20261117.md',35)+'; '+cite('READER_R1_20261117.md',15))
row('170008, 170037, 170056, 170757, 170786, 170808, 171197, 172466, 172475','INDEXED','All are present in the 18-entry published snapshot. Job 170903 only scores existing camera rows. Training jobs and CPU admissions are not additional trace reads.', '; '.join(f'job {j}: lines '+','.join(str(n) for n,_ in pub_by_job[str(j)]) for j in [170008,170037,170056,170757,170786,170808,171197,172466,172475]))

text='# Lost-read decisions\n\n'
text+='The records support one additional reported loss: the CP1 m200 ReVSI parent answers. Three old routed pilots remain unresolved because their Orchard pool was not checked. They are classified as may exist, not emitted as lost. Missing Trinity working files do not imply that a read is lost when the published index or a named Orchard return survives. The reader_r1 index entries contain the tower arm; their own-arm comparator comes from the separately listed H1 returns.\n\n'
text+='The published snapshot contains 18 entries (measured). Its fingerprint is in `work/published_fingerprint.json`. This audit reads records only; availability outside the snapshot is reported evidence, not a fresh existence measurement. Unknown run IDs, arms and item counts remain unknown. Source paths below are recorded unless explicitly labelled derived.\n\n'
text+='| Read | Decision | Identity, location and reason | Evidence |\n|---|---|---|---|\n'
for r in rows: text+='| '+' | '.join(x.replace('|','\\|').replace('\n',' ') for x in r)+' |\n'
text+='\n`LOST_LINES.jsonl` is the exact canonical entry emitted by the supplied `lost`/`index` commands under `work/index_snapshot/`. It is a proposal for review, not a publication. The full copied index has 19 entries after adding this one; the published index was never opened for writing.\n'
(OUT/'LOST_TABLE.md').write_text(text)
(W/'decisions.json').write_text(json.dumps(rows,indent=2)+'\n')
status(1,'Record classification and one reported-lost entry generated with the supplied CLI. Three old pilot returns remain unresolved in the named Orchard pool; no speculative lost entries emitted.')
print('TASK1: one lost entry; 18 published entries preserved; decision table written')
