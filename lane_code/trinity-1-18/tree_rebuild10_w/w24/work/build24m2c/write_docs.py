from common import *
v=J.load(D/'VALIDATION.json')
for name in ('HIDDEN_PATH_TESTS','SOURCE_PIN_TESTS','SOURCE_PIN_UPDATE'):
 assert J.load(D/(name+'.json'))['status']=='PASS'
 v['checks'][name]=dict(status='PASS',sha256=J.sha(D/(name+'.json')))
J.write(D/'VALIDATION.json',v)
iv=J.load(D/'INVARIANTS.json');ks={k:v['kit_seal'] for k,v in iv['kits'].items()}
up=J.load(L/'out/UPLOADS_24M2.json')
card=f'''Vehicle N uses MINIMAL. q, n and qd have GO=false; only the unuploaded n_go template has GO=true. Production admission is blocked.
The final tree is {iv['tree_sha256']} (943 files). The source archive, inventories, code capsules and dependent pins match that tree.
Kit q: {ks['q']}; kit n: {ks['n']}.
Kit n_go: {ks['n_go']}; discovery kit qd: {ks['qd']}.
UPLOADS_24M2.json contains {up['total_files']} entries ({up['total_bytes']:,} bytes) relative to 24m1, including qd/ and jd.sh. Preserve recorded file modes. The stream root is {up['stream_root']}.
UPLOADS_24M2_GO.json contains the separate three-file GO delta. Neither that delta nor any kit was uploaded or launched.
P's authenticated step-400 export 5083243c initializes N. N starts a fresh optimizer, counter and schedule; the step-544 lineage, routing_opener_init=keep and DEFERRED boundary remain pinned.
The planner resolves closure pins through SHA256-indexed staged members, checks their bytes and stages u/<sha256>. It never falls back to a receipt's literal host path.
P routing database 4e8e6c04 has no authenticated staged member in the supplied inventories. Mode r is expected to refuse R1_STAGED_PIN_MISSING before preparation. Its size is not recorded in the supplied receipt.
Catalog pin eac5f9f0 also has no verified source; the unavailable production small archive may contain it. MISSING_STAGED_PINS.md records full hashes, fields and evidence without inventing sizes or sources.
Item 2b is STOPPED: the missing camera/routing population prevents authenticated native scene rebuild. SCENE_REBUILD_INPUTS.md lists all 54 inputs. No rebuild hook is installed and the null rebuild/coverage fields remain unchanged.
Item 2c is STOPPED: r1_launch22.validate_removals rejects a thirteenth list with R1_NAMING_REMOVAL_ORDER. verify_union accepts it; the gate still blocks installation. The twelve existing lists remain unchanged.
The native removal fixture removes all 320 d21e374f keys and none through the existing twelve lists. Supplied production expectations are 25,020 pointing rows, 320 newly removed, zero previously removed, 6,584 scene exclusions and zero K1-held-out admissions after the new list; these are not a local production scan.
After native preparation succeeds, the census reads native Rows and room/exclusion authorities for every stream. It reports admitted totals and admitted counts in BENCH v2, dev-S1, R0, withheld-80, K1 held-out and official scenes.
The pointing census reads provenance.canonical_scene through Rooms.room, as audit_point.py does. A positive pointing/K1 fixture prevents a vacuous zero count.
Any protected admitted row refuses R1_SCENE_PROTECTED_ADMITTED_ROWS before WAITING_REVIEW. live/s0.json and s1.json hold native rebuild evidence; s2.json binds their hashes and counts; s3.json contains protected row keys per stream. Their combined cap is under 1 MB.
Mode r publishes routing_selection.json, receipt.json and materialization.json to <n_root>/o/<jobid>/; the two regenerated artifacts have a combined 5 MB cap and their SHA256 values are logged.
All modes publish l.py-equivalent filtered q/rooms/h/rv/t log tails, routing log tails, .steps and RESULT/refusal records from EXIT/TERM traps outside bwrap. Each diagnostic publication stays under 5 MB; opaque filenames preserve the naming policy.
The qd job requests preempt, one GPU, 48 CPUs, 800G, four hours and no requeue. Its opaque name is a15_cot_ap24d9b8e2; batch logs are under x_22c714e1/j/.
qd runs the resolver, mode r, then mode q in a fresh physical root using the same logical namespace and its own routing selection. It runs d.py, h.py and rv.py, publishes WAITING_REVIEW and stops without waiting or training.
qd's config, stores, removal lists and admission are identical to q's. Its BUILD and RESULT records say discovery=true and claims=nothing. Publication runs every 600 seconds and at exit, including failure.
The native hook creates the fresh q directory and copies the pinned plan. h.py preserves the new host.json fields and enforces the host hash, assertions and loader checks; q/qd require proof_mode=q and n requires train.
Normal q still needs an independently reviewed routing-selection pin. N still requires the prepared identity review before rank 0. The discovery self-selection grants neither production approval nor a launch GO.
N requests advanced, four GPUs/four ranks, 48 CPUs, 800G and 24 hours. The independent review wait remains 7,200 seconds with 30-second polling, strict receipt ownership/modes and identity checks.
The existing live copier, export milestones, checkpoint policy, session names and bounded signal cleanup remain in force. Two head slots are NOT_PRESENT; seven other slots are DEFERRED and block official reads.
Final decoded scans and kit/naming/resolver/guard/live/routing/review/publication tests pass. Native host tests pass 44 cases; the scene census passes 25 cases. Production receipts reproduce 24m1's literal-path failure in both modes and produce the named missing-pin refusal in all final kits.
The discovery shell fixture reaches WAITING_REVIEW with real h.py/rv.py/publication checks. Native routing regeneration/digest and native handover/rank checks run separately; capacity, staging and preparation fixture boundaries are explicit in VALIDATION.json. No production preparation or admission is claimed.
'''
replace(L/'out/N_CARD_KIT_ROWS.md',card)
report=f'''Item 0 fixed: SHA256-only staged resolution; absent P database 4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84 has no staged source; catalog eac5f9f01587803b2402f80cc310b75ec1f960270a6bc059416b1e1407b1e7c9 remains unverified. Sizes are unknown, not invented.
Expected first discovery refusal: R1_STAGED_PIN_MISSING:4e8e6c04...:config.streams.routing.database in mode r, BEFORE preparation.
Items 2b and 2c STOPPED: 2b lacks the authenticated camera/routing population; 2c needs a tree change because validate_removals rejects the thirteenth list. No verifier or gate was changed.
The final tree seal is {iv['tree_sha256']}; all 943 files and UNCHANGED24L3 match. The retained fuzz-0 patch evidence passes.
q, n, n_go and qd contain the final source archive, inventory, code capsule and dependent seals. Template source pins and their u/ upload entries agree with the runtime capsule.
The 54 scene-rebuild inputs are listed in out/SCENE_REBUILD_INPUTS.md. out/MISSING_STAGED_PINS.md lists full hashes, config fields, unknown sizes and source evidence.
The native Removals fixture removes the 320 candidate pointing keys; the existing twelve lists remove zero. verify_union accepts thirteen, but validate_removals refuses R1_NAMING_REMOVAL_ORDER in every kit.
The six-status census covers every native admitted stream, publishes counts and protected row keys under opaque live/ names, and refuses before review. Its 25 fixtures include a positive pointing/K1-held-out case.
EXIT/TERM publication works outside bwrap in all kits; filtered diagnostic copies stay under 5 MB. The 600-second loop, concurrent publication and failed exits pass fixture tests.
Mode r publishes the regenerated receipt and materialization beside routing_selection.json, enforces their 5 MB combined cap and logs SHA256 values.
out/kit_qd has GO=false, discovery=true and claims=nothing. out/jd.sh requests preempt, GPU:1, 48 CPUs, 800G, 04:00:00 and no requeue; it uses the kit resolver.
qd runs r then fresh-root q with its own selection, followed by d.py/h.py/rv.py, and stops at WAITING_REVIEW. Its config, stores, removals and admission match q exactly.
The decoded discovery shell fixture reaches WAITING_REVIEW; native routing regeneration/self-selection and native handover checks pass separately. Fixture preparation/capacity boundaries are recorded; no production preparation is claimed.
Native host tests pass 44 cases. Final decoded scans and kit/naming/resolver/guard/live/routing/review-wait/security tests pass; source-pin resolver checks pass for all four final kits.
The hidden-path look-ahead executes plan_payload q and r on real receipt bytes: 24m1 fails on its literal host path, and all final kits refuse the missing hash without opening a host path. Missing production payloads are not fabricated.
Resolver identities, config semantics, admission, legality, removals, opener rows, step-544 lineage and DEFERRED remain unchanged. h.py accepts the added host fields unchanged.
Kit seals: q={ks['q']}; n={ks['n']}; n_go={ks['n_go']}; qd={ks['qd']}.
out/UPLOADS_24M2.json/.list contain {up['total_files']} entries ({up['total_bytes']:,} bytes), stream root {up['stream_root']}; qd is only under qd/. The separate GO delta is not uploaded.
The package, SHA256, member seal and storage accounting are in out/DELIVERY_24M2.json. Final new allocation is below 200 MB; a temporary overrun occurred because the initial check omitted directories. The size fixture is retained losslessly compressed in attic/. All twelve prior package hashes are unchanged.
No Orchard, network, SSH, GPU, scheduler, Git, tmux or other agent was used. This is a packaged, production-blocked delivery, with no launch or admission claim.
'''
assert len(report.splitlines())<30
replace(L/'out/BUILD24M2_REPORT.md',report)
print('report lines',len(report.splitlines()),'card lines',len(card.splitlines()))
