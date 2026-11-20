from common import *
import re
iv=J.load(D/'INVARIANTS.json');s=iv['kits'];up=J.load(L/'out/UPLOADS_24M3.json')
point='d21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1'
card=f"""Vehicle N uses MINIMAL. q, n and qd have GO=false. Only the unuploaded n_go template has GO=true; production admission is not established.
The tree is {iv['tree_sha256']} (944 files). All source archives, inventories, code capsules and dependent seals match.
Kit q: {s['q']}; kit n: {s['n']}.
Kit n_go: {s['n_go']}; discovery kit qd: {s['qd']}.
UPLOADS_24M3.json contains {up['total_files']} files ({up['total_bytes']} bytes) after 24m2d. Its stream root is {up['stream_root']}; top directories are q/, n/, qd/ and u/. Preserve base uploads and recorded modes.
UPLOADS_24M3_GO.json contains only the separate three-file delta from current n to n_go. It is not authorized for upload. jd.sh and unchanged dbb2.py are separate files outside the kit seal; their destinations and hashes are in outside_kit_files.
P's authenticated step-400 export initializes N with a fresh optimizer, counter and schedule. The step-544 lineage, routing_opener_init=keep, two NOT_PRESENT slots and seven DEFERRED slots remain pinned.
The pointing list is {point}: 320 keys in two K1 held-out rooms. It is entry 12 after the first 11 pinned lists and before NAMING_REMOVE, with role=protected_rooms and stream=pointing. Localisation preserves both fields.
Supplied production expectations are 25,020 source rows, 320 listed removals, 6,584 scene exclusions and 18,116 admissions before the target-shape filter, with zero K1 held-out admissions. These are expectations, not a local production scan.
The planner authenticates staged inputs by SHA256 and never falls back to receipt host paths. Mode r reconstructs P's database and requires the complete 4e8e6c04 hash. Mode q uses the selection's authenticated routing base; host.json records both substitution hashes.
Catalog eac5f9f0 remains dependent on the runtime e00 archive. If absent, R1_STAGED_PIN_MISSING names its full hash and field before preparation. MISSING_STAGED_PINS.md records the evidence.
The scene step calls native r2_scene_bindings.rebuild and unchanged verify, binds r2_scene_rebuild and scene_coverage, times the call, and publishes its receipt and coverage as live/s0.json and s1.json. The original pool manifest/tokenizer remain pinned; only the selected routing population follows native substitution.
Every fresh job regenerates native pool selection, room audit, scene evidence, stream/target-filter receipts, preparation and final identity for the configured removal lists. Production-dependent outputs are not fabricated locally.
The final census passes all source rows before removals and all actual admitted native Rows to check_protected_rooms for pose, VQA, routing and pointing. Pose mixtures follow every source and their final order; indexed streams follow admitted indices.
The independent census counts BENCH v2, dev-S1, R0, withheld-80, K1 held-out and official scenes. Pointing checks both canonical resolutions; unresolved VQA uses native Binding.room. Tree 24l4r still supplies the post-condition; the planned 24l4s swap remains external.
live/c4.json is byte-identical to the census receipt pinned by h.py. It records each native return/refusal, counts, config identity, source pins, prepared store pins and hashes of sorted protected row keys. live/c0.json through c3.json hold those keys in pose/VQA/routing/pointing order.
live/h0.json is the exact host receipt pinned by live/v.json. n_review2 can verify that hash, h0.protected_census against c4.json, every stream identity/store pin, and each row-key hash. The source descriptor also authenticates against the native staging manifest.
q, n and n_go refuse on the first census or post-condition refusal. h.py rejects missing, stale-identity or mismatched-store evidence; rv.py rechecks the receipt and host publication before WAITING_REVIEW.
qd alone records census/post-condition failures as WOULD_REFUSE. Its preliminary complete-source diagnostic publishes d0.json through d4.json and returns to native preparation. Its final census and review path can reach WAITING_REVIEW with WOULD_REFUSE; native admission gates remain unchanged.
The qd shell fixture proves this continuation with a protected pointing row, actual native post-condition, actual h.py/rv.py, and byte-identical host/census publication. It exits without review waiting or training and claims nothing.
Run nice -n 10 python3 -B out/bind_protected.py <stream> <list.jsonl> to bind an additional list, stage it, preserve native regeneration steps, reseal all four kits and write an upload diff. Native list validation and the final post-condition still apply.
Pose cleanup is blocked when listed protected rows remain in a pose mixture: 24l4r has no native producer that filters those keys. The tool binds pose lists but does not manufacture a clean pose receipt. REMOVAL_RECEIPTS_BLOCKER.md records the required native producer.
The discovery wrapper runs the unchanged dbb2.py once routing_selection.json appears, retries every 60 seconds for at most 180 attempts, and stops on success. Its SQLite hashes, header search and retry bounds pass fixture tests.
The qd request remains preempt, one GPU, 48 CPUs, 800G, four hours and no requeue, with the opaque job name and filtered evidence traps preserved. No scheduler command ran here.
N remains advanced, four GPUs/ranks, 48 CPUs, 800G and 24 hours. Independent review remains 7,200 seconds with 30-second polling, strict ownership/modes and identity checks. Normal q still requires an independently reviewed selection.
All four decoded scans and the kit, naming, resolver, guard, live, routing and review-wait suites pass. Real receipt bytes reproduce the old literal-path failure and reach the named catalog refusal in both modes in all four kits.
No kit was uploaded or launched. Native production stores, actual admission counts and production readiness remain unverified; DELIVERY_24M3.json records fixture boundaries and the pose-delta limitation.
"""
assert len(card.splitlines())<40
replace(L/'out/N_CARD_KIT_ROWS.md',card)
p=L/'out/SCENE_REBUILD_INPUTS.md';text=p.read_text()
text=text[text.index('\n\nNative rebuild'):].lstrip()
text="""The native scene-rebuild step is installed in all four kits. It authenticates the listed inputs, calls student_pilot.r2_scene_bindings.rebuild with the unchanged verifier, and binds the two returned evidence pins before preparation. The camera/routing population comes from the routing base named by the request's selection and native routing substitution; host.json records its original and substituted hashes. All other 53 original inputs remain authenticated, including the original pool manifest and tokenizer before relocation. The new pointing-role list is an additional input.

"""+text
text=text.replace('| source population camera | 4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84 | Mode-r native reconstruction; full SHA256 must match before reuse in q |','| source population camera | Selected routing receipt database pin; P reconstruction expects 4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84 | Native request routing substitution; authenticate the complete selected database hash before rebuild |')
needle='| removal 11 |'
at=text.index(needle)
text=text[:at]+f'| protected pointing list | {point} | k/p.json upload; role and stream survive localisation to u/<sha256> |\n'+text[at:].replace(needle,'| NAMING_REMOVE (last) |',1)
at=text.index('\nThe complete input census')
text=text[:at]+"""

The inventory contains the 54 original entries plus the pointing-role list. The source receipt must bind the exact selected population pin and count; the native rebuild refuses a mismatch. Missing inputs still refuse by SHA256 before preparation.

The kit publishes the native rebuild receipt and coverage to live/s0.json and s1.json. The final census publishes live/c4.json and c0.json through c3.json before WAITING_REVIEW; h.py pins the exact census bytes in live/h0.json. Only qd records census/post-condition refusals as WOULD_REFUSE and continues. The scene verifier is unchanged.
"""
replace(p,text)
old=L/'out/SCENE_REBUILD_BLOCKER.md'
if old.exists():
 target=L/'attic/build24m3/out/SCENE_REBUILD_BLOCKER.md';target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists():target=target.with_name(target.name+'.'+str(__import__('time').time_ns()))
 old.rename(target)
timings=re.findall(r'scene rebuild seconds=([0-9.]+)',(D/'planner_scene_verified.log').read_text())
J.write(D/'SCENE_TIMING.json',dict(seconds=[float(t) for t in timings],scope='Native complete planner fixture; synthetic frame-host boundary; not a production time estimate.'))
lines=[
f"Tree {iv['tree_sha256']}; q {s['q']}; n {s['n']}; n_go {s['n_go']}; qd {s['qd']}.",
"Scene-rebuild step BUILT: native rebuild and unchanged verify bind both evidence pins; the selected routing database authenticates through native substitution.",
"Pointing-dependent receipts regenerate IN JOB through native functions; fixture regeneration passes. Pose-delta cleanup is BLOCKED as recorded in REMOVAL_RECEIPTS_BLOCKER.md.",
"Expected first discovery refusal: R1_STAGED_PIN_MISSING:eac5f9f01587803b2402f80cc310b75ec1f960270a6bc059416b1e1407b1e7c9 if the catalog is absent; after authenticated reconstruction, qd records census/post-condition failures as WOULD_REFUSE.",
"GO remains false in q, n and qd. Only the unuploaded n_go template has GO=true. Nothing was uploaded, scheduled or trained.",
f"The {point} pointing list binds all four decoded configurations after 11 pinned lists and before NAMING_REMOVE; role, stream and actual removal_order survive localisation.",
"Expected pointing counts: 25,020 source; 320 removed; 6,584 scene-excluded; 18,116 before the target-shape filter; zero K1 held-out admitted. Production counts were not scanned here.",
"Every final census calls the tree post-condition on complete source rows and actual native admitted selections for all four streams.",
"Each result binds the training config identity, source/store pins and sorted protected-key hashes. h.py and rv.py refuse missing, stale or mismatched evidence.",
"live/c4.json and c0..c3.json publish the census and keys; live/h0.json publishes the exact host receipt. Both receipt publications match their pinned bytes.",
"The independent census checks both pointing resolutions and uses native Binding.room for unresolved VQA. The tree stays 24l4r; 24l4s remains an external swap.",
"The delta tool binds, stages and reseals additional role lists and writes upload diffs. Pose fixtures pass binding/isolation/post-condition checks; native pose materialization is not supplied by this tree.",
"The discovery wrapper preserves its launch form and runs unchanged dbb2.py every 60 seconds after selection publication, up to 180 attempts. Native SQLite/header and retry fixtures pass.",
"Four decoded scans and kit/naming/resolver/guard/live/routing/review-wait/publication suites PASS; native host tests pass 81 cases; final census/h checks pass 24 cases.",
"Real receipt bytes reproduce the old literal-path failure and reach the named catalog refusal in r and q for q, n, n_go and qd.",
f"The native scene planner fixture passes with the original pool-manifest pin and logs {timings[-1]} seconds. Separate native rebuild replay produces identical receipt bytes.",
"The qd protected-pointing shell fixture reaches WAITING_REVIEW with WOULD_REFUSE through actual h.py/rv.py and publishes both bound receipts.",
f"UPLOADS_24M3.json/.list contain {up['total_files']} files ({up['total_bytes']} bytes) after 24m2d under q/n/qd/u. The separate GO diff has three files; wrapper/helper destinations are listed outside the kit seal.",
"Every earlier package is unchanged. The tree inventory matches the supplied seal and unchanged-file ledger; admission, legality, resolver identity, step-544 lineage and DEFERRED boundaries remain intact.",
"The delivery archive embeds DELIVERY_24M3.json and a member-hash manifest. External delivery metadata records its final archive hash and byte count.",
"New allocated disk usage stays below 200,000,000 bytes. Completed fixture evidence is retained losslessly; no file-deletion command ran.",
"Production admission remains unproven. Fixtures use synthetic stores and declared host/capacity boundaries; VALIDATION.json records their scope."
]
assert len(lines)<30
replace(L/'out/BUILD24M3_REPORT.md','\n'.join(lines)+'\n')
print('Report',len(lines),'lines; card',len(card.splitlines()),'lines')
