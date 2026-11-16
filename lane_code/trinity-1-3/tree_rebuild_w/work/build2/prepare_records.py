"""Write reviewable policy slots, mix and provenance without inventing lost evidence."""
import hashlib
import json
from pathlib import Path
import re
import sys
L=Path(__file__).resolve().parents[2]; T=L/'work/tree_r1'; O=L/'out'
sys.path.insert(0,str(T))
from student_pilot import r2_policy as P, r2_mix as M
from student_pilot.r2_withheld import Withheld, SHA256, LOST
from student_pilot.p3_provenance import sha256
from launch_r2.build import WORDS

def output(name,value):
    (O/name).write_text(json.dumps(value,indent=2)+'\n')

registry=P.slots();output('COMPONENT_SLOTS.json',registry)
source='work/rec/recovered/scene_evidence/results/20261115T074012_a97ad692_L2391_result.txt'
lines=['# Component policy','',
       'Missing evidence blocks admission. Slot names explicitly recovered from the summary retain those names. '
       'GUESS: names for the tower, segmenter, room rule, alias table and depth cut are reconstruction defaults; their original record filenames are unverified. '
       'Base-model pretraining is disclosed separately as externally pretrained and frozen for the scene audit; its provenance belongs in the init record. '
       'The lost record count is reported by `'+source+'`.','',
       '| Component | Class | Phase | Policy status | Record slot | SHA256 |',
       '|---|---|---|---|---|---|']
regen=['# Records to regenerate','',
       'Each record must use `r2-component-evidence-v1`, name its component, class and phase, bind every input by SHA256, '
       'and separate computed overlap from the adopted ruling. The registry accepts no unknown verdict. '
       'The schemas and refusal logic are in `work/tree_r1/student_pilot/r2_policy.py`.','',
       '| Record | Must prove | Required inputs |','|---|---|---|']
for name,slot in registry.items():
    lines.append(f"| {name} | {slot['component_class']} | {slot['phase']} | {slot['status']} | EVIDENCE_{name}.json | MISSING |")
    if name in P.LINEAGE:
        proof='Full parent lineage; explicit checked banks; no in-scope overlap except venue 381879; inherited overlap outside scope.'
        inputs='Export metadata, parent membership receipts, training scene manifests, sealed exclusion records; init also binds external base pretraining.'
    elif name in P.CHOICES:
        proof='Fit or selection scenes, chosen values and chronology; applicable pre-registration choices and dated freeze.'
        inputs='Fitted coefficients or rule bytes, input scene lists, eligibility intersections, pre-registration and freeze evidence.'
    elif name in P.EXTERNAL:
        proof='External pretraining provenance and frozen status; disclosure, without a clean-scene claim.'
        inputs='Weights/config identities, upstream release identity, optimizer trainable inventory.'
    else:
        proof='Complete admitted source population after every sealed exclusion and withholding; no unknown scene overlap.'
        inputs='Family manifests, frame map, alias resolution, upstream receipts, final membership and withheld-room SHA256.'
    regen.append(f'| EVIDENCE_{name}.json | {proof} | {inputs} |')
lines += ['', 'Claim scope, the venue rule and the open lineage question follow the user build brief and `work/records/design/POLICY_AUDIT_20261115.md`. '
          'The qualification-room default follows the user build brief; future probe reads are seen-in-training. '
          'The original evidence bytes were not available and were not reconstructed from assertions.']
(O/'COMPONENT_POLICY.md').write_text('\n'.join(lines)+'\n')
(O/'RECORDS_TO_REGENERATE.md').write_text('\n'.join(regen)+'\n')

mix=M.table();fallback=M.table(True);output('MIX_A0.json',mix);output('MIX_FALLBACK.json',fallback)
population=[52720,67970,22082,10492,10000,2335,15302,4308,465,9404,14020,12260,9143,11728,3820,22280,194987,20239]
plan='work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md#4'
table=['# Per-step mix','',
       'The quotas match the sealed parent. D0 moves route planning to VQA, then proportionally renormalizes each stream. '
       'The exact rational weights and registered-run integer totals come from `work/tree_r1/student_pilot/r2_mix.py`. '
       'Population values below are plan metadata, not newly filtered counts. Repeats are therefore provisional arithmetic, '
       'not real admission. Real admission requires pinned post-filter counts before materialization.','',
       '| Stream | Type | Form | Plan / step | New / step | Plan population | Provisional repeats | Source |',
       '|---|---|---|---:|---:|---:|---:|---|']
totals=M.allocation(mix)
for cell,count in zip(mix['cells'],population,strict=True):
    table.append(f"| {cell['stream']} | {cell['type']} | {cell['form']} | {cell['plan_rows_per_step']:.3f} | {cell['rows_per_step']:.6f} | {count} | {totals[cell['type']]/count:.4f} | `{plan}`; `out/MIX_A0.json` |")
table+=['','| Stream | Parent / step | New / step | Source |','|---|---:|---:|---|']
for key,value in mix['quotas'].items():
    table.append(f'| {key} | {value} | {value} | `work/kit07ca49df_meta/m/k/b02e4385.json`; `out/MIX_A0.json` |')
table+=['','The registered step total, rank allocation and duration are bound in `out/MIX_A0.json`. '
        'The pose/pointing fallback is bound in `out/MIX_FALLBACK.json` and requires a pinned frame-host absence receipt. '
        'The native sampler consumes the bound table, complete filtered-population receipts and final-reader type indices. '
        'It preserves paired facing rows within a step and exact registered-run totals. The executable proof is `out/B2_SAMPLER_PROOF.json`.']
(O/'MIX_A0.md').write_text('\n'.join(table)+'\n')
w=Withheld()
output('WITHHELD_BINDING.json',dict(path='work/shared/WITHHELD_ROOMS_80.json',sha256=SHA256,
    sorted_room_list_sha256=w.rooms_sha256,lost_digest=LOST,match=w.rooms_sha256==LOST,
    qualification_rooms_bind=False))
hashes=json.loads((T/'launch_s1/b/wh.json').read_text())
words=set(WORDS)
for path in (T/'launch_s1').rglob('*'):
    if path.is_file() and path.suffix in ('.py','.sh','.json'):
        words.update(re.findall(r'[a-zA-Z][a-zA-Z0-9_+-]*',path.read_text().lower()))
known={hashlib.sha256(w.encode()).hexdigest():w for w in words}
decoded={h:known[h] for h in [*hashes['word'],*(h for hs in hashes['substr'].values() for h in hs)] if h in known}
output('FORBIDDEN_STRINGS.json',dict(explicit_substrings=list(WORDS),inherited_hash_rules=hashes,
       inherited_rule_sha256=sha256(T/'launch_s1/b/wh.json'), recovered_spellings=decoded,
       note='All inherited hashes are enforced even if their plaintext spelling is not recovered.'))
status='''# Build 2 status

The shared grammar is installed byte for byte. The tree wrapper retains native event-span checks and the build-1 explicit-label dialect. Initial regression results are in work/build2/initial_tests.log; adapter fixes and new proofs are running.

Component slots, claim-scope bank reads, dated-freeze checks and shared-room withholding are implemented. Missing records block admission. The kit builder uses the parent inventory and byte verifier, carries opaque metadata, and refuses launch. The parent kit's anonymity waiver does not carry over.

The per-type mix, metadata repeat gate and native sampler are implemented. Counts from the plan remain provisional; no real post-filter count receipt is available. Both pose source pins come from the parent staging list.

Native GF-1 no longer creates a camera connector. CPU tests are checking independent-parent parity and stage trainables. The A2 kit proof uses an explicitly synthetic dense manifest because the real dense manifest is absent.
'''
(L/'work/build2/STATUS.md').write_text(status)
