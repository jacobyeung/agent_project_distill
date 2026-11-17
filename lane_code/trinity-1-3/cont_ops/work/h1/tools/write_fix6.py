"""Write current packet findings and operator instructions from checked local artifacts."""
import difflib,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parents[1]
load=lambda n:json.loads((H/n).read_text())
sha=lambda n:hashlib.sha256((H/n).read_bytes()).hexdigest()
ids=load('ids.json');up=load('UPLOAD.json');audit=load('evidence/fix6_admission/results.json');changes=load('evidence/fix6_patch_manifest.json')
assert audit['routing_selection_implementation']['status']=='BLOCKED'
assert all(r['status']=='PASS' for r in load('evidence/fix6/tests.json'))
report=f'''The checkpoint disk plan is fixed, but this packet must not be submitted. The CPU audit found a second admission refusal: the routing selection still records D0’s implementation closure. Native H1 routing will reject it with `Routing selection belongs to another implementation`. The local tests reproduce that refusal; they do not certify production admission.

The deriver now evaluates the pinned trainer’s `checkpoint_space.plan(recipe, old_reserve_bytes)` whenever the recipe changes. It extracts only that pure function from the SHA-verified archive member, so login derivation needs only Python’s standard library. `build_packet.py` and `rebuild_fix6.py` run native `carrier_c1_run.validate` with p1cpu; `test_admission_config.py` validates the final derived config and reproduces the exact round-5 disk-plan failure. Native validation therefore runs in the CPU build/test environment, not the Orchard login interpreter.

The config retains the 1,000-step LR horizon, stop at 200, milestones 100/200, sampling settings, rows, seed, world size, initialization and 86,400-second recipe cap. The disk guard retains 14 planned full states, two extra states and 200,000,000,000 reserve bytes; weight exports decrease from nine to three. An exact comparison permits only the disk guard and the newly bound review pin to differ from the prior config.

| Current artifact | Value |
|---|---|
| Config identity | `{ids['identity']}` |
| Admission contract | `{ids['contract']}` (unchanged) |
| Config key with PENDING review | `{ids['config_key']}` |
| Run key | `17c4ffa4` (unchanged) |
| Bundle | `/project/community/jjyeung/okh7/i_1be16f28` |
| New KH | `/project/community/jjyeung/okh7/x_3fdda0fb` |
| New persistent root | `/project/community/jjyeung/okh7/r/39504485` |
| Preserved old KH | `/project/community/jjyeung/okh7/x_4b3114cf` |
| Node-local run | `/tmp/jjyeung/a_17c4ffa4/runs/17c4ffa4` |
| Allocation | `advanced`, 1 node, 4 GPUs, 48 CPUs, 800G, 13 hours |
| Job name | `{ids['job_name']}` |
| Trainer archive | `{ids['trainer']['file']}`, SHA256 `{ids['trainer']['sha256']}` (unchanged) |
| Fixture manifest | `{ids['fixture_manifest']}` |
| Upload archive | `build/{up['archive']}`, SHA256 `{up['sha256']}` |
| Operator patch | `build/c_patch.sh`, { (H/'build/c_patch.sh').stat().st_size:,} bytes, SHA256 `{sha('build/c_patch.sh')}` |

The native persistent-run guard rejects a new cold job once an earlier job has claimed the root, even if no checkpoint exists. A local test reproduces that refusal after a mode-p claim. The new persistent root prevents reuse of job 170527’s claim. The old KH and old root remain untouched. The failed job stopped before writing an admission request; if a later attempt has populated the node-local run with a request or binding, preserve that state and use a clean node-local run before launch rather than reusing foreign evidence.

**CPU admission audit**

All executed checks use `/scratch/jjyeung/envs/p1cpu/bin/python`, empty `CUDA_VISIBLE_DEVICES`, offline settings and local files. Local pin relocation preserves the original SHA256 and supplies identical bytes; it does not alter the tested config. `admit()` uses one CPU thread locally; b/w.py requests 16 in production.

| Check and source | Executed result and limits |
|---|---|
| `carrier_c1_run.validate:62–164` | PASS: H1/faithful settings and room pin, trace version, layout, explicit recipe, disk policy, placement/base/FSDP/all-frame settings, exact streams, pose-source guard, route-table/policy shape, weights/LR scales/exclusions/tool flag, final-mode levers, initialization, camera overrides, gate flag and optional validation pins. Absent GX/MDG/pose-only branches are not applicable. |
| `h1.validate`, `h1_faithful.validate`, `data.layout_settings`, `recipe_for` | PASS: stop 200 is inside horizon 1000; sampling starts at 1 with probability .5; recipe reconstruction is exact. Recipe reconstruction also runs routing schedule and E2E budget validation. |
| `s1_route_policy.validate(authenticate=True)` | PASS: actual frozen-table bytes match the embedded route table. |
| `checkpoint_space.plan`, `Budget` | PASS: 14 planned + 2 extra full states, 3 exports; a fourth export is refused. Actual checkpoint byte measurement and available disk space are not tested. |
| `capped_steps` | PASS: returns 29 for the sealed timing estimate and its inherited four-hour calculation. This branch applies only to pose-only training; H1 final mode never invokes it. |
| `trace_version.metadata`, first-step policy | PASS: version 3.14 and `all_rank_native_v1`. |
| `b/i.authorize(p,0)`, `allocation_gpus`, `b/x.ready`, `b/d.contract`, `b/w.tree` | PASS on the derived config: operation/expiry/resource-count/input shapes, 0 preparation GPUs/4 training GPUs, native contract and actual trainer inventory. |
| `b/g.check(p)` | PASS in existing gate/reviewer tests with only review/archive/staging approvals supplied in memory and persistent-state dispatch stubbed. No production approval was manufactured. Native persistent selection is separately tested using local paths and a synthetic job ID. |
| `run.authenticate` | PASS: actual import closure, full trainer inventory, tree seal and archive members, with local paths for identical pinned bytes. |
| `Removals`, `Exclusions`, benchmark/pose/report exclusion loaders | PASS with the available pinned lists; applying those rules to all production rows remains untested. |
| `s1_admission.admit(..., prepare_only=True)` | PARTIAL: real resource limits, attempt identity, world/filter/stream checks, native validate/authenticate, request binding, phase journal and full-LM warm-start shape pass. It stops in `mdg_parent.model_pin` at unavailable pose receipt SHA256 `30612832cc84ad83f9500ecbeac57704767568ff24482475feb42a92c7f166b8`. |
| `s1_routing.build:215–216` implementation equality | BLOCKED: the exact native conditional raises `Routing selection belongs to another implementation` using the actual selection and H1 source closure. Relocation preserves this field, so local path relocation cannot repair it. |
| `milestone_gate`, stop control | Gate function not run: `gate_stop=false`; H1 stops by 200 and fresh training starts at 0. Its resume branch also requires step >=400. Native tiny-model fallback reaches `H1_STOP` at 200 with exports at 100/200 and a verified persistent slot. |
| Wall time | PASS: b/g.py explicitly requires recipe wall 86400 and stop reserve 3600. Launch authorization and wrapper request 46800 seconds; Slurm sends USR1 at 43200. Stop-bridge regression passes; actual Slurm signal delivery and four-rank shutdown remain untested. Reducing the recipe cap would fail b/g.py and change training behavior. |
| Export/session names | PASS: execute the wrapper’s exact validator against 44 dummy local capabilities, including four parts each for m100/m200/mstop. Real session capability validity/expiry is not tested. |
| Full preparation and `b/d.effective`; `run.prepared` | NOT RUN to completion: missing production pose/model/row/frame bytes. Parent metadata/init manifests, stream materialization, selection/filter/census/coverage, faithful-row gate, preparation seals, RGB audit and effective-config equality remain job-side requirements. |
| GPU path before first optimizer step | NOT RUN: CUDA/world/process groups/network, allocation receipt, processor/model/assets/init/depth/FSDP, model-dependent optimizer setup, prepared data, resume/output binding and per-row finite-loss checks need unavailable production assets and GPUs. The native first-step report follows the first update and also remains pending. |

The stale selection changes these seven closure entries:
'''
for name, v in audit['routing_selection_implementation']['changed'].items():
 report+=f"- `{name}`: recorded `{v['recorded'] or 'absent'}`; H1 `{v['actual']}`.\n"
report+='''
The selection has no recorded blockers, but its implementation binding is stale. Replacing the seven hashes would certify unverified selection provenance. A safe correction requires regenerating or verifying the selection under the H1 implementation with its production inputs, checking that approved QIDs, order, source counts and exclusion membership remain unchanged. If they differ, the correction changes training semantics and needs a separate decision. This task did not alter or bless that selection. The resulting selection pin will change the config identity again, so the current identities are review artifacts, not a final deployment approval.

**Operator path**

Do not run `s.sh` for this packet. Resolve the selection blocker first, repeat the admission audit, and regenerate bindings, patch and sums. The guarded patch supplied here concretely applies the disk-plan and fresh-target changes to the stated live round-5 bundle; it is not evidence that the remaining selection problem is resolved.

1. Carry the body of `build/c_patch.sh` through the authorized opaque wrapper. It verifies old immutable hashes and the entire old sums file before changing anything; it checks mutable review/staging records against the old identity. It refuses existing new KH/root/backup targets, links, tampered inputs and repeat application.
2. The patch swaps only the 12 changed small files, including sums.txt, retaining their exact old bytes in `BUN/v_6/`. It also moves p/e/q and p/e/c/archive/gate/ready/result/compare/anon/go records into that private directory. It leaves the old KH, its sess.json, the trainer archive, routing archive and verified t/u extractions untouched. Recheck `sha256sum -c sums.txt` in BUN.
3. Rerun `bash o.sh`: this derives a fresh p, reproduces e from the sealed base, and reruns stage/archive attestation. The staged byte payloads remain reusable; their config-bound evidence must be regenerated. The old persistent root cannot be reused.
4. Rerun `PY_GATE=<same approved interpreter> BW_GATE=<same approved bubblewrap> bash g.sh`. The archive and verified extractions are reused. Gate inputs are unchanged, but the supplied patch deliberately retires the old report and requires a fresh gate result.
5. Obtain a fresh independent `review.json` for the final config identity, unchanged native contract and trainer source. Do not reuse the old PASS record or rename its identity. Review/staging records are mutable inputs outside sums; derive binds their actual hashes.
6. Run `bash z.sh derive`. It must create the new KH and pass final comparison; read its actual config key from `compare.json`, since a real review changes the review pin and filename. Scan the final kit and external records, write an actual CLEAN `anon.json`, then run `bash z.sh certify`. The old certificate cannot be reused; patching BUN changes the external records it covered.
7. `EXPORT_OBJECTS.txt` remains byte-identical: namespace 8865619b, run 17c4ffa4, 44 object names. The already minted create-only sessions remain applicable because none were used and names are unchanged. Preserve the old sess.json and copy its bytes to the new KH/sess.json with mode 0600 using the approved credential handling procedure. No remint is needed for this change; expiry and continued unused status still need operator verification.
8. Obtain a new separate `go.json` bound to the final identity, contract, changed jb.sh hash and the new KH manifest. Only after the selection blocker is cleared, native requirements are met, and that GO is supplied may the operator run `bash s.sh`.

No full trainer re-upload is required. The deterministic full upload remains available for a fresh bundle; `orch_h1.sh` intentionally refuses the existing live BUN. The patch is the smaller live-bundle path. The upload is below 20 MB, as is its embedded script. Local complete-source reproduction still lacks `k/np226_5204b3a0.tar` and `k/t_e6456bcecb8d4a8f4f68158eb68275f8befff128.tar`; fixtures retain their sealed pins and complete derivation refuses their absence. Orchard must reproduce the complete sealed kit.

**Validation and evidence**

The 16 regression scripts pass: four originals, stop_bridge, fix1, visible_names, sealed_modes, runtime_inventory, gate_sandbox, gate_patch, the new config patch test, and four runnable reviewer checks. The new admission test passes its assertions, including the exact old disk-plan refusal and the newly identified selection refusal. Historical permission/inventory tests supply matching historical authorization bytes to their old derivers; current derivers still use the new bindings. The existing gate patch test retains its original round-4-to-round-5 target. Distributed reviewer harnesses and tests/RERUN_CHAIN.sh receive syntax checks only; the existing chain_r1 and runner are unchanged.

`evidence/fix6/tests.json`, `evidence/fix6_admission/results.json`, `evidence/fix6_patch/results.json`, and `evidence/fix6_package/results.json` record results. The rebuild checks byte-identical generator/runtime/transport/patch outputs, a fresh fixture manifest/modes, and the login planner under system Python without torch. `evidence/hash_changes_fix6.json` records changed hashes; SHA256SUMS.txt seals the current deliverables and evidence. All work remained local and CPU-only; no SSH, network, Orchard, GPU, Git or deletion was performed.

**Inherited visible names**

| Location | Sealed inherited exposure |
|---|---|
| `build/fx/b/c.sh:11–13,102` | The sealed project cache prefix and base-model cache name remain unchanged. |
| `build/fx/b/c.sh:7–8`; `payload/g.sh:89–90` | Sealed logical receipt/mount prefixes remain unchanged. |
| `build/fx/b/c.sh:16–17,429`; `build/fx/b/p0.sh:12–31` | Inherited runtime locations, staging arguments and export operation names remain unchanged. |

New remote entrypoints and destinations remain opaque; private parent checks require real mode-0700 directories. Local descriptive delivery filenames are carried as bodies, not remote executable paths. Full content review still covers the trainer archive and private records.
'''
(H/'REPORT.md').write_text(report)
diff='''The deriver recomputes checkpoint storage from the changed recipe and retains the reserve. Native CPU validation now guards the build. The packet binds that config to a fresh kit and persistent root, while retaining the existing run key, trainer and export names. The audit identifies a stale routing-selection implementation binding; that unresolved refusal blocks deployment.

The shipped patch verifies old immutable bytes and retains mutable evidence before replacement. The old KH is untouched. REPORT.md gives the exact operator sequence and remaining production checks.

| Changed deployed member | Old SHA256 | New SHA256 |
|---|---|---|
'''
for n,r in changes.items():diff+=f"| `{n}` | `{r['old']}` | `{r['new']}` |\n"
diff+='\nThe review/staging old hashes above identify the packaged PENDING drafts. Live PASS versions are checked against the old identity and backed up verbatim. The patch never assumes they match the draft bytes.\n\n'
for n in ('tools/derive_kit_h1.py','tools/make_deriver.py','tools/build_packet.py'):
 old=H/'evidence/fix6_before'/n
 diff+='```diff\n'+''.join(difflib.unified_diff(old.read_text().splitlines(True),(H/n).read_text().splitlines(True),fromfile='before/'+n,tofile=n))+'```\n\n'
(H/'DIFF.md').write_text(diff)
fix=[
'Cause: H1 changes milestones to [100,200] but retained D0’s nine-export disk plan; native admission requires three exports.',
'Changes: tools/derive_kit_h1.py:445,643 and payload/d.py:445,643 recompute the pinned checkpoint_space.plan with the old reserve; tools/make_deriver.py:14,18 generates it.',
'Validation: tools/build_packet.py:67,81 and tools/rebuild_fix6.py:16 run native validation in p1cpu; tests/test_admission_config.py:32 reproduces the exact old error and tests the derived config. Login derivation stays stdlib-only.',
'Fresh targets: x_3fdda0fb and r/39504485 avoid the old KH and the failed job’s persistent claim; native tests reproduce cold-restart refusal on an already claimed root.',
'| Audit check | Run | Result |','|---|---|---|',
'| Native validate, H1/faithful, layout, recipe, route policy/table, exclusions/removals | yes | PASS |',
'| b/w tree, authorize(p), input shapes, contract, source authentication | yes | PASS; identical local pinned bytes |',
'| capped_steps / wall / stop / full states / session names | yes | 29 only for pose-only; 86400 required; 13h allocation + USR1; stop 200; 14+2 states; 44 names PASS |',
'| admit(prepare_only) | partial | Config/authentication/request pass; missing production pose receipt blocks parent preparation |',
'| Routing selection implementation | yes | BLOCKED: native “Routing selection belongs to another implementation”; seven D0 closure entries differ |',
'| milestone_gate / full data preparation / effective / GPU pre-step | no | gate_stop=false and stop<400; production data/model/GPU unavailable |',
'Blocker: do not relabel the selection hashes. Regenerate or verify selection with H1 and real inputs; changed accepted rows would change training semantics. REPORT.md lists all seven entries and exact coverage.',
'Tests: 16 regression scripts PASS; admission assertions PASS (including both reproduced refusals); deterministic package/fixture/stdlib planner and guarded patch PASS. Four-rank harness syntax only; runner and chain_r1 unchanged.',
f'Identity: {ids["identity"]}; PENDING-review config key: {ids["config_key"]}. Final review changes the filename; resolving selection changes identity again.',
f'Contract: {ids["contract"]} (unchanged); run_key 17c4ffa4 unchanged.',
f'Deriver SHA256: {sha("payload/d.py")}; all 12 changed member hashes: evidence/fix6_patch_manifest.json and DIFF.md.',
f'sums.txt SHA256: {sha("payload/sums.txt")}.',
f'Upload SHA256: {up["sha256"]}; orch_h1.sh SHA256: {sha("orch_h1.sh")}.',
f'Patch: build/c_patch.sh ({(H/"build/c_patch.sh").stat().st_size} bytes), SHA256 {sha("build/c_patch.sh")}; retains all old bytes/evidence in v_6; old KH untouched.',
'Orchard: STOP until selection is verified and bindings rebuilt; then patch → o.sh prepare/reproduction/stage → g.sh → fresh review.json → z.sh derive → anon scan + z.sh certify → fresh go.json → s.sh.',
'EXPORT_OBJECTS.txt is unchanged; unused create-only sessions still match all names and may be copied privately to new KH (verify expiry/unused status). No full trainer re-upload is needed.',
'Exact audit/results: REPORT.md and evidence/fix6_admission/results.json. No Orchard/SSH/network/GPU/Git/deletion; all changes stayed in this workspace.'
]
assert len(fix)<=25
(H/'FIX6.md').write_text('\n'.join(fix)+'\n')
print('REPORT.md, DIFF.md, FIX6.md written;',len(fix),'FIX6 lines')
