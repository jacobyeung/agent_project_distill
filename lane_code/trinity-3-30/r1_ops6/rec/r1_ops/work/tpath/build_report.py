import hashlib
import json
from pathlib import Path

W = Path(__file__).resolve().parent
H = W / 'x/x_3fdda0fb'
A = W / 'x/x_69d2930d'
B = Path('/scratch/jjyeung/orch_n30/r1_ops/work/ex_9dd2fbb7')

intro = '''Audit of job 171377: no additional A-specific deterministic startup defect was established. The audit found an inherited export-shutdown defect (D1), an inherited allocation-deadline risk (R1), and an unverified export-session binding risk (R2). These findings do not establish that the running job has encountered any of them. The supplied fixes to live b/ mode and k/4.json are treated as installed.

D1: b/r.sh:72,84–85 can leave the background uploader alive when it kills only the persister shell, then start another export pass. Both passes can use the same tar.part, stop-generation claim, receipts file, and upload sessions (b/c.sh:413–435). A CPU-only reproduction of that shell pattern confirmed overlap. Serialize the complete export operation, including its completion check, claim, tar creation, upload, and receipt publication, with a per-run lock; stop and join the persister gracefully before the final pass. The code is shared with H1; successful H1 training does not rule out this timing-dependent defect.

R1: the trainer uses recipe.wall_seconds=86400 and stop_before_seconds=3600, although the allocation is 46800 seconds. Its fallback budget therefore targets approximately 23 hours, not the allocation's 12-hour stop point (trainer/A/student_pilot/carrier_c1_run.py:2838–2841,2398–2408). The configured B:USR1@3600 signal has a complete relay path, but a lost signal or a slow final step/checkpoint/export/upload/slot copy can exhaust the allocation. Use the actual allocation deadline for the runtime stop budget and reserve the measured time for all final persistence. Retain the reviewed LR horizon and do not change sealed recipe bytes casually: b/g.py:61 currently requires 86400. For this running job, an operator can supervise the existing stop-request mechanism against its real deadline; this audit made no live change.

R2: sess.json was deliberately excluded from both fetched kits. e.txt and the wrapper agree on all 20 keys, but neither this audit nor jb.sh:42–50 proves that each value is a usable session URI for the intended object. Executing the actual wrapper check locally showed that it accepts both an invalid array of the 20 names and a dictionary whose 20 values are null. b/gcsput.py:48 checks returned size and MD5, not returned object name/bucket, and :84–85 skips receipts by name/size/offset without checking the current payload digest. Require a JSON object mapping all 20 expected names to nonempty HTTPS session-URI strings, verify their object bindings with the operator's session-mint record, and require matching object name/bucket and payload hashes before accepting or reusing upload receipts. Do not copy H1's sessions or receipts into A. Missing receipts themselves are safe and need no fix.

All paths below are relative to A's fetched kit unless prefixed with BUN (the supplied ex_9dd2fbb7 bundle), H1, or trainer/A. JSON files named in the brief are compact one-line files, so their field references use :1. EXPECTED includes identity/path changes, unchanged checks, and deliberate packet-A behavior; it does not mean that A trains identically to H1. The complete active configuration matches BUN/config.json except its separately bound admission review.

The audit used local CPU reads only, with writes confined to this work directory. It used no SSH, Orchard connection, Git, GPU, deletion, or live-job control. LANE_RULES.md was read; the task's explicit write boundary overrides its external event/mirror instructions. The no-archaeology writing rule was applied. No borderline process-history statement was retained.

| File | Field/check | H1 | A | Class | Fix |
| --- | --- | --- | --- | --- | --- |
'''

rows = [
('b/r.sh:72,84–85; b/c.sh:413–435','D1: final/background export ownership','Same shell lifecycle','Same lifecycle; toy reproduction overlaps','DEFECT','Lock the entire per-run export transaction; gracefully join the persister before final export.'),
('b/g.py:61–62; trainer/A/student_pilot/carrier_c1_run.py:2398–2408','R1: runtime deadline','86400 recipe, 3600 reserve; 13-hour job.sh','Same; BUN/jb.sh and s.sh also 13 hours','RISK','Use actual allocation deadline for the runtime stop decision; budget checkpoint, export, upload, and slot publication.'),
('BUN/jb.sh:42–50; b/gcsput.py:19–51,84–85','R2: session destination and receipt integrity','sess excluded; 4 m100 receipts supplied','sess excluded; keys agree; values unverified','RISK','Validate dict[str,str] HTTPS-session shape and URI-to-object bindings; check returned name/bucket and current payload hash before accepting or skipping uploads.'),
('b/r.sh:25–39','Startup seal and admission sequencing','a.py before p child, then g.py t','Same; training authority already installed','EXPECTED','No change. Parent does not rerun a.py between completed p and g.py t.'),
('b/; b/c.sh:94–97,108,292,299','Permissions','Recursive removal of write bits in staged source/model directories','Live b/ is 0500 per brief; staged files lose write bits and directories become 0700','EXPECTED','Keep the supplied live b/ fix. Directory mode change preserves owner traversal; content seals check bytes, not directory modes.'),
('k/4.json:1; b/g.py:82–87; b/i.py:44–76','Training authority','p/t/u, grants 0/4/4, advanced','4.train.json is byte-identical to fetched k/4.json; same operational grants','EXPECTED','Keep training authority through staging and worker authorization. Follow auth1/READERS.md for restoration timing.'),
('SHA256SUMS.txt; b/a.py:14–23','Temporary authority/manifest mismatch','All available entries match','Only available mismatch is k/4.json, as expected for the supplied hot installation','EXPECTED','Do not rerun a.py or restart the job with this transient seal. Restore the pinned authority only after the documented worker-authorization point; do not restore it early.'),
('k/4.json:1','wall_seconds / documentary authorization fields','wall_seconds=46800; H1 evidence/conditions','wall_seconds=14400; proof-oriented conditions remain','EXPECTED','No inspected t reader enforces authority.wall_seconds or condition prose. Runtime expiry, revision, modes, arm and GPU checks pass static validation.'),
('k/launch.json:1; b/g.py:43–81,91–117','Launch/source/review/staging gate','READY, production_authorized=true, world=4','Same; new hashes internally consistent','EXPECTED','No change. g.check static gates passed with only runtime receipt and persistent-state calls stubbed.'),
('k/launch.json:1; k/1.json:1','Active configuration and identity','arm 0 → 1dd078da; identity eb45ebfd…','arm 0 → 666c05ea; identity fac07052…','EXPECTED','No change. Launch config SHA, active mapping, source seal, review and training authority agree.'),
('k/0.json:1; k/7.json:1; k/s1_record.json:1','Trainer archive/tree/runtime record','95886619…; 796 files; 200-file training import closure','b83a8a35…; 799 files; 203-file closure','EXPECTED','Both complete archive inventories and transitive import closures match their seals; no missing source dependency found.'),
('k/archive.json:1; b/g.py:91–97','Durable archive attestation','BUN i_1be16f28/t_9588661986650d29.tar','BUN i_69d2930d/t.tar; 9963520 bytes','EXPECTED','A local bundle archive matches its digest and inventory. g.py validates the attestation, not live remote availability.'),
('k/review.json:1; k/staging.json:1','Review scope, stage attestation','H1 review/evidence','A review/evidence; PASS and bound identity/contract','EXPECTED','No change. Nested production_go_granted=false is documentary here; launch authorization and the separate submission GO are distinct.'),
('k/selection_equality.json:1','Selection evidence schema/status','selection-equality-v1 / EQUAL','r1-selection-projection-v1 / PASS; room projection','EXPECTED','This file is sealed but is not consumed by the inspected training path. Training consumes the pinned selection and native materialization, not this documentary status.'),
('k/0.json:1; b/c.sh:133–173,270–337','Staging inputs','Shared base inputs','All inherited entries unchanged; 12 extra destinations','EXPECTED','Eleven added bundle payloads match their pins locally. The added d.db is external at okh7/s_22b44165/d.db; its bytes were not supplied. Existing in-job staging validates it.'),
('b/c.sh:18–22,31–37,339–363','Node-local and namespace paths','a_17c4ffa4; run 17c4ffa4','a_673bc60f; run 673bc60f','EXPECTED','All host run, logical output, admission directory and wrapper RUN paths agree. Logical kit key 8865619b is intentionally retained.'),
('b/c.sh:398–407','Kit copy and small-file persistence','Copies b/k/cert/manifest, arm; mirrors NX/o and run JSON','Same','EXPECTED','t stages the current authority into NX. KH/o is not restored into NX/o; parent i.py creates the new allocation receipt there.'),
('b/d.py:36–135; b/i.py:73–76','Derived admission files','Reads current run inputs/data_receipt.json and pinned derived records','Same checks; A streams/config must match A contract','EXPECTED','p must publish real PREPARED data, config, preparation, routing materialization, frame and parent records. They are outputs of this admission, not files to copy from H1/proof.'),
('b/i.py:60–68,120–158; b/w.py:11–24,108–112','Allocation, parent receipt, four worker checks','One node, four ranks; exact derived-config receipt','Same','EXPECTED','No change. i.py creates NX/o/171377.3.json; each worker reauthorizes and compares it. A parent receipt alone does not prove all workers passed.'),
('b/w.py:24,62,80–103; b/x.py:14–27,52–63','Runtime tree and input bindings','Full sealed trainer tree; final-mode stream/preparation pins','Same','EXPECTED','No extra H1 operator file is needed. Missing input-scan certification logs a warning; actual checked pins and trainer preparation still authenticate payloads.'),
('k/666c05ea.json:1; trainer/A/student_pilot/type_mix.py:75–110,189–256','Family quotas and capped sampler','No type_mix','New VQA/routing quotas; max_repeats=4; units source','EXPECTED','Matches packet A. Configuration validation passes. p creates prepared/type_mix.json; t requires the exact pin/spec/recipe/streams and populations. Actual admission populations were excluded from this audit.'),
('trainer/A/student_pilot/carrier_c1_run.py:655–660,785–790,1029–1041','Prepared type-mix dependency','Absent','Generated and rebound by prepare/prepared/Rows','EXPECTED','Preserve the whole admission inputs tree, including prepared/type_mix.json. It is included by the slot tar of inputs; no manual H1-created file is required.'),
('k/666c05ea.json:1; trainer/A/student_pilot/h1.py:17–36','Own-camera/scheduled sampling','faithful=true; probability=.5; force_from_step=1','faithful=false; probability=0; force_from_step=null','EXPECTED','Intentional packet-A behavior; also disables H1 AnswerStop. Keep stop_after_step=200 and the 1000-step LR horizon.'),
('k/666c05ea.json:1; BUN/r.json,s.json,d.json,n.json','Room routes, source selection, VQA, extra removals','Room types route; H1 selected population and VQA','Room types direct; projected selection; replacement VQA; seventh removal list','EXPECTED','Matches packet A and staging pins. n.json contains JSONL despite its suffix, as required by row_removals.py:31.'),
('trainer/A/student_pilot/h1_r0.py:45–59; trainer/A/auth/R0_ROOMS.txt:1','Relative R0 room-list dependency','Present in sealed trainer archive','Present with the same registered SHA','EXPECTED','No operator-created file required; resolved relative to trainer root, not bundle cwd.'),
('trainer/A/student_pilot/carrier_c1_run.py:2808–2947','Before first optimizer step','Validate; process groups; preparation; source; parent allocation; model/init; FLA; FSDP; AdamW; Rows; lock/binding','Same, plus the type-mix receipt binding','EXPECTED','No GPU run was performed. Real parent-weight load, FLA execution, memory fit and row tensors remain runtime checks.'),
('trainer/A/student_pilot/carrier_c1_run.py:1510–1630,2357–2367; trainer/A/student_pilot/s1_first_step.py:10–47','First native optimizer step/admission','72 microsteps/rank; 288 global rows','Same stream counts; quota-chosen A rows','EXPECTED','Per rank: pose=16, VQA=32, routing=16, pointing=8. All-rank finite/coverage/no-substitution admission occurs after optimizer.step; receipt is inputs/first_step_171377.json.'),
('k/666c05ea.json:1; b/w.py:177–181; trainer/A/student_pilot/carrier_c1_run.py:2297–2311,2406–2439','Milestones, stop_after_step, milestone_gate','m100/m200; stop=200; LR steps=1000; gate_stop=false; milestone_gate=null','Same','EXPECTED','No m400 gate is required. A stops at 200 unless signal/time/stall stops it earlier. m200 uses the normal export path before H1_STOP.'),
('trainer/A/student_pilot/carrier_c1_run.py:2394–2421; trainer/A/student_pilot/checkpoint_space.py:11–18,117–120','Checkpoint and export disk budget','First-step checkpoint; 7200-second periodic save; plan=14+2 full states and 3 exports, 200 GB reserve','Same','EXPECTED','No static plan mismatch. Actual free space at first save was not supplied; jb.sh checks 3.8 TB only before staging.'),
('trainer/A/student_pilot/carrier_c1_run.py:2023–2083; b/c.sh:413–417','Export completion marker','artifact.json written after weights/heads','Same','EXPECTED','Uploader ignores incomplete exports. Export rereads staged cfg.code and cfg.preparation; no KH/o proof receipt is required.'),
('BUN/e.txt:1–20; BUN/jb.sh:46–49; b/c.sh:417–434','Export names','q8/8865619b/17c4ffa4_m100…','q8/8865619b/673bc60f_{m100,m200,mstop,mstopB,mstopC}.tar.part00..03-of-04','EXPECTED','All 20 A names agree exactly. e.txt is an operator mint list, not a t-time input. Do not substitute kit_key 69d2930d for upload prefix 8865619b.'),
('sess.json.receipts.jsonl; b/gcsput.py:57–64,103–105','Prior upload receipts','Four m100 part receipts','Absent from supplied A tree','EXPECTED','No fix: absence returns an empty receipt map and first successful upload appends the file. Receipts are results, not admission prerequisites.'),
('b/c.sh:416,423–430','KH/o export markers and stop claims','Per-run .done and .claim outputs','New run-specific names','EXPECTED','Absent markers are normal. Do not seed them from H1. Protect claim/check/publication with D1 locking.'),
('b/g.py:31–39; b/r8.py:64–148','Persistent root and RUN marker ownership','Persistent r/39504485; logical run 17c4ffa4','Persistent r/673bc60f; logical run 673bc60f','EXPECTED','r8 chooses t/u from checkpoints even when called by mode p. Empty history creates RUN.json; repeat same-job t passes; foreign first_job or slot history refuses cold t. Synthetic ownership checks passed.'),
('BUN/jb.sh:24–35,88–96','Run/slot creation and binding mirror','H1 wrapper not supplied; job.sh identical','Creates private RUN/RS, starts binding mirror, launches job.sh','EXPECTED','RUN.json comes from r8, binding.json from trainer bind_output, mirror from jb.sh. Current marker contents/modes were not supplied; do not reset an existing marker to bypass ownership.'),
('BUN/jb.sh:95; b/r.sh:13–24; b/h.py:7–17; b/i.py:111–117,156','USR1 relay','Shared r/h/i signal implementation; job.sh same signal directive','Wrapper → r.sh → i.py → rank processes; persistent stop request also written','EXPECTED','No broken relay found statically. R1 covers the finite shutdown budget and signal dependence.'),
('b/i.py:151–158; b/sg.py:44–92','Stall guard','3600 startup, 1200 idle, 600 checkpoint grace','Same','EXPECTED','No A-specific change. Slow startup/step work without observed file activity can trigger the guard; native timing was not measured here.'),
('BUN/jb.sh:98–115,166–263','End-slot archive and verification','H1 wrapper bytes unavailable for direct comparison','Latest complete checkpoint + inputs + binding; alternating A/B; hashes and all rank payloads checked before verified=true','EXPECTED','Requires positive checkpoint step, inputs/binding and slot space plus 20 GB. No static path/schema mismatch with trainer output was found.'),
('BUN/jb.sh:115–164','Insufficient-project-space fallback','H1 wrapper unavailable','GCS gcloud stream with deadline=TK_JOB_START+46800−300; size/MD5 checked; success exits 6','EXPECTED','This fallback needs the separate Orchard gcloud config, not sess.json. If it fails, continuation is lost and SLOT_SKIPPED records it; retain/check free space before shutdown. Live capacity/credentials were not supplied.'),
('BUN/jb.sh:57–85; b/r8.py:102–129','Subsequent resume leg','Same r8 code','Restores verified slot, checks binding; later job needs slot and binding mirror','EXPECTED','No manual RUN marker/proof seeding. The slot includes the new type-mix receipt under inputs; source/kit/staged inputs remain external prerequisites.'),
('job.sh:1–19; BUN/s.sh:19–109','Entrypoints and proof/GO files','job.sh byte-identical','s.sh consumes GO/proof only before sbatch; jb.sh is the submitted wrapper','EXPECTED','No t-time read of BUN/go.json, BUN/job.id, or KH/o/<proof>.proof.json after the current admission child. H1 s.sh/jb.sh were not supplied; no byte-equality claim is made for them.'),
]

def cell(v):
    return str(v).replace('|', '\\|').replace('\n', '<br>')

text = intro + ''.join('| '+' | '.join(cell(v) for v in row)+' |\n' for row in rows)
text += '''
The read chain is jb.sh → job.sh → r.sh t → admission r.sh p → g.py t → c.sh staging/namespace → i.py authorization/receipt → four w.py workers → trainer preparation/model/FSDP/AdamW/Rows → optimize_step → native first-step admission → first checkpoint → m100/m200 or stop export → c.sh uploader → jb.sh slot publication. No supplied t-path reader loads selection_equality.json as an admission gate, and no t-time reader requires H1's export receipts.

The fetched copies contain 93 distinct relative file names: 76 are byte-identical, 15 differ, one active config is A-only, and H1's export-receipts file is H1-only. The complete comparison is in file_comparison.json; code.diff records every wrapper/runtime code change. field_differences.json preserves full old/new JSON values. trainer.diff records both changed existing trainer files; the three added files are type_mix.py, vehicle_p.py, and loader_audit.py. archive_validation.json verifies all 796/799 archive members, including auth/R0_ROOMS.txt. The transitive training source closures also match k/7.json (200/203 files).

audit_checks.json records the successful CPU checks. The real g.check ran with runtime admission and persistent-state calls stubbed; it is not a live admission result. Real i.authorize passed p/t/u with synthetic admission configuration, the launcher constructed four ranks, and w.dispatch passed the correct settings to a fake trainer without executing training. The actual wrapper session check accepted both malformed session shapes described in R2. Real r8 marker ownership, type-mix configuration validation, all 20 export names, milestone/stop fields, and optional missing receipts were checked locally. export_overlap_check.py and export_overlap.jsonl demonstrate D1 with owned toy processes and no network. The system Python lacked required modern APIs; the successful checks used /scratch/jjyeung/envs/p1cpu/bin/python. No real optimizer step, upload, slot copy, live session inspection, or real data-receipt validation was performed.

The fetched omissions are not evidence that production files are missing. Both kit fetches exclude sess.json, o/, runs/, archives and files over 2 MB. Complete source archives were available in the supplied local bundle and auth1 fixture and were verified against their pinned hashes. Live admission outputs, model/data payloads, persistent marker contents, free-space measurements and session URI values remain unobserved. H1's external bundle wrapper was not provided. Consequently this audit cannot certify live readiness or assert that there must be a third A-specific blocker.

The following table accounts for every changed JSON field. Large values are summarized by type/count and SHA256 of canonical JSON; field_differences.json contains their full values. The grouped behavior rows above explain the checks and fixes; fields below are expected identity, reviewed-treatment, or documentary differences, not additional findings.

| File | Field/check | H1 | A | Class | Fix |
| --- | --- | --- | --- | --- | --- |
'''

def summarize(value):
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':'))
    if len(encoded) <= 100:
        return encoded
    if isinstance(value, (dict, list)):
        return '{}({}), sha256={}'.format(type(value).__name__, len(value), hashlib.sha256(encoded.encode()).hexdigest()[:16])
    return encoded[:82]+'…'

fields = json.loads((W / 'field_differences.json').read_text())
for file, changes in fields.items():
    if file == 'AUTH_LIVE':
        continue  # Byte-identical to A k/4.json; its fields are already listed.
    for field, before, after in changes:
        if file == 'k/0.json' and field == '/extra':
            h = {v['dest']:v for v in before}; a = {v['dest']:v for v in after}
            for dest in sorted(h.keys() | a.keys()):
                if h.get(dest) != a.get(dest):
                    row = ('k/0.json:1', '/extra/'+dest, summarize(h.get(dest,'<ABSENT>')), summarize(a.get(dest,'<ABSENT>')), 'EXPECTED', 'New packet-A staging dependency; see staging checks above.')
                    text += '| '+' | '.join(cell(v) for v in row)+' |\n'
            continue
        label = 'k/1dd078da.json → k/666c05ea.json:1' if file.startswith('ACTIVE_CONFIG') else file+':1'
        why = 'No change: pins/identities agree.'
        if file.startswith('ACTIVE_CONFIG'):
            why = 'No change: matches packet A; behavior described above.'
        elif file == 'k/selection_equality.json':
            why = 'No change: sealed documentary evidence; not a t gate.'
        elif file in ('ANON_OK.json','k/review.json','k/staging.json','k/4.json'):
            why = 'No change: operational checks distinguished from documentary fields above.'
        elif file in ('k/7.json','k/s1_record.json') and any(s in field for s in ('carrier_c1','type_mix','loader_audit','vehicle_p')):
            why = 'No change: sealed packet-A sampler/loader implementation; archive verified.'
        row = (label, field, summarize(before), summarize(after), 'EXPECTED', why)
        text += '| '+' | '.join(cell(v) for v in row)+' |\n'

text += '\nThe manifest differences bind the changed files listed below. Its k/4.json entry intentionally retains the pre-install authority digest; the running parent has already passed the startup seal check. All other available manifest entries match their fetched payloads.\n\n| File | Field/check | H1 | A | Class | Fix |\n| --- | --- | --- | --- | --- | --- |\n'
def manifest(root):
    return {n:s for s,n in (line.split('  ',1) for line in (root/'SHA256SUMS.txt').read_text().splitlines())}
hm, am = manifest(H), manifest(A)
for name in sorted(hm.keys() | am.keys()):
    if hm.get(name) != am.get(name):
        row = ('SHA256SUMS.txt', name, hm.get(name,'absent'), am.get(name,'absent'), 'EXPECTED', 'Known authority timing exception above.' if name=='k/4.json' else 'No change; payload pin verified where supplied.')
        text += '| '+' | '.join(cell(v) for v in row)+' |\n'
(W / 'TPATH_AUDIT.md').write_text(text)
print('Wrote TPATH_AUDIT.md:', len(text), 'characters;', len(rows), 'primary rows')
