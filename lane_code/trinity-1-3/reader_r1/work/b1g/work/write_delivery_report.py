from pathlib import Path
import hashlib,json,re,shutil
W=Path.cwd();O=W/'out';P=O/'package';token=(O/'TOKEN').read_text().strip()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(O/'PACKAGE.json').write_bytes((P/'PACKAGE.json').read_bytes())
files=['0.tgz','1.tgz','PACKAGE.json','tower_sequence.py','tower_bootstrap.py','node_check.py','tower_pair.py','unpack_return.py','READ_PLAN.json','inputs_tower.json','export_544.json']
hashes={n:sha(O/n) for n in files};hashes.update(plan_sha256=json.loads((P/'0.json').read_text())['plan_sha256'],BATCH_sha256=sha(P/'BATCH.sh'))
(O/'DELIVERY_SHA256.json').write_text(json.dumps(hashes,indent=2)+'\n')
# Reuse the exact reviewed command bodies, with only delivery identity and local destination changed.
old=(W.parent/'b1f/out/REPORT.md').read_text();section=old[old.index('The following operator commands'):]
blocks=re.findall(r'```bash\n(.*?)```',section,re.S)
assert len(blocks)==5
blocks=[b.replace('a9439d0fb0487',token).replace('/work/b1f','/work/b1g').replace('50c7ae132db7ba3960a7c123420a7eadf6aaf9a85e416d5964bdf2e5cc1ffa79',hashes['1.tgz']) for b in blocks]
ops=f'''Package `{token}` runs read 1 first, followed by read 0 in a separate process. Both list only `g3t` in `perception_memo_modules`. Read 1 uses `candidates_argmax`, distance only, and `verify` on its explicit first 30 distance IDs. Read 0 uses `null_argmax` and memo `on`, with distance, displacement, rotation, movement direction, then room. `READ_PLAN.json` contains the exact IDs. Each read keeps separate settings, identity, journals, and call caps.

The full-plan proxy estimate is 5.167 hours including 30 minutes for staging/loading and a 30-minute stop margin. The 20-minute return margin lies inside that stop margin. Under a five-hour allocation, the expected cut is in room after all 750 distance/camera items and about 14 room items. SAM encodes freshly whenever a read requests it; encode time is unmeasured and no SAM savings are credited. The expected room cut has 381.279 seconds of pre-room slack; unmeasured overhead can move it earlier.

Place the delivery from an existing opaque directory and check metadata. Set `D` to that directory. These commands have not run in this lane.

```bash
{blocks[0]}```

Coordinate staging IO before the allocated empty-root CPU check. This requests eight CPUs and no GPU. The helper restores authenticated inputs, checks default and per-read settings, rehearses selector wiring, and writes `a/c/CPU.json` and `a/c/MEMORY.json`. It checks the fixed G3T memo bound against 200 GiB without loading SAM for a memory measurement. The bootstrap requires the passing receipt bound to this payload, input descriptor and operator. A real evaluation-item decode remains outside this check.

```bash
{blocks[1]}```

After the CPU check passes, use the existing review requirements and accept the documented partial-run estimate before submitting. Record the shared return pool's usage; the production write test checks its capacity before staging. The following commands check resource types and pending priority jobs, then submit one GPU for five hours.

```bash
{blocks[2]}```

Fetch after the return is published. The transport may mark a clean partial return as failed because the full plan did not finish; inspect its summaries.

```bash
{blocks[3]}```

Transfer the bounded `a/f/0.tgz` and `a/f/EXIT.json` through the authorized operator channel into W5's `work/f/`. No transfer ran here. Unpack and score locally:

```bash
{blocks[4]}```

Unpacking rejects a missing journal or environment for a started segment. Pairing rejects missing journals, mixed rules, mismatched module bindings and changed code hashes. Partial camera journals cannot establish the complete camera comparison. Candidate-rule comparisons remain in-sample. No cross-rule journal merge is permitted.
'''
(O/'OPERATIONS_TOWER.md').write_text(ops)
def ref(name,needle):
 p=O/name
 return f'`out/{name}:{next(i for i,l in enumerate(p.read_text().splitlines(),1) if needle in l)}`'
mem=json.loads((O/'MEMORY_BOUND.json').read_text());tim=json.loads((O/'TIME_PRICE.json').read_text());audit=json.loads((O/'DELTA_AUDIT.json').read_text())
changes=[
 ('Module membership',ref('src/b/e2e_reader/perception_memo.py',"modules = value['perception_memo_modules']")+'; '+ref('src/b/e2e_reader/perception_memo.py','if module not in self.modules'), 'A missing module-list key fails even in off mode. Only listed modules enter the host store; an unlisted module skips hashing, lookup, copy and storage. Explicit-ID verification applies only to listed modules.'),
 ('Production wiring',ref('src/b/e2e_reader/parity.py',"perception_memo_modules=settings")+'; '+ref('src/b/e2e_reader/real.py','memo = process_memo'), 'The parity factory passes the mandatory list into the real reader. This kit lists g3t; SAM encodes freshly in every read that requests it.'),
 ('Bindings and reuse',ref('src/orchard_h10/prepare.py',"perception_memo_modules=config")+'; '+ref('src/orchard_h10/runner.py',"perception_memo_modules=actual")+'; '+ref('src/h1eval/h10/launch.py',"perception_memo_modules=settings")+'; '+ref('src/h1eval/h10/parity_adapter.py',"for field in ('stage1_select_rule'")+'; '+ref('tower_pair.py',"fields=('export_sha256'"), 'Prepared settings, environment bindings, worker identity, resume, b04 reuse, and per-read journal pairing include the module list.'),
 ('Read order',ref('tower_sequence.py','SCHEDULE=')+'; '+ref('tower_sequence.py',"perception_memo='verify'")+'; '+ref('tower_sequence.py','for i in (1,0)'), 'Read 1 runs first with verify on its first 30 distance IDs. Read 0 then runs all five types in one worker with memo on. The two processes retain independent rules, identities, journals and margins.'),
 ('Memory admission',ref('tower_sequence.py','def memory_bound')+'; '+ref('tower_sequence.py','def memory_probe')+'; '+ref('tower_bootstrap.py',"get('basis')")+'; '+ref('node_check.py',"settings['perception_memo_modules']"), 'The operator computes the fixed-shape G3T bound and checks the allocation. Bootstrap and the CPU helper require no measured SAM memory receipt. The reader contains no new numeric memory cap.')]
report=f'''Package **{token}** memoizes only G3T and runs the selector comparison first. The local gates and retained evidence are listed below. The expected five-hour cut falls in room; the full 786-item plan does not fit the timing proxy. SAM encode time and production peak RSS remain unmeasured.

| Change | Implementation | Behavior |
|---|---|---|
'''+''.join(f'| {a} | {b} | {c} |\n' for a,b,c in changes)+f'''
| Execution order | Read | Rule | Types | Memo | Verification IDs |
|---|---|---|---|---|---|
| 1 | 1 | candidates_argmax | 150 distance items | verify, then on by membership | Explicit first 30 distance IDs |
| 2 | 0 | null_argmax | 150 distance, 150 displacement, 150 rotation, 150 movement direction, 36 room | on | Empty list |

Both reads use tower, mode none, `perception_memo_modules=["g3t"]`, and `save_own_depth=false`. The verification list spans 11 captures and causes 19 hit recomputations. A mismatch serves the fresh value and disables memoization throughout that process. SAM results never enter this kit's memo. The worker preserves per-type manifest order and the existing call caps. Room has no served call in leg R1 and is scheduled last. `RETURN_MEMBERS.json` proves distinct process IDs for the two reads and one load per read; every started segment remains in the return.

| Local gate | Result and evidence |
|---|---|
| Package / constraints | 14 / 9 pass. |
| B1 runtime / stubs / tower wiring | 8 / 6 / 7 pass. |
| Sequence / pairing / B1 report | 5 / 7 / 1 pass. Sequence asserts the literal requested order; pairing includes missing and mixed module-list refusal. |
| Memo / bindings / module selection | 8 / 4 / 3 pass. Includes explicit-ID resume, mutation, no IO, process isolation, bit identity, missing key failure, listed hits and unlisted fresh calls. |
| F1/F2/F4 / return CLI | Five tests pass; real subprocess journals return, top STOP drains the active item, deadline results persist, and b04 reuse rejects rule, mode, IDs and modules independently. Authenticated unpack accepts all six journals and rejects a missing one. |
| Multi-type A/B | Twelve reads across five types per mode. One model load per mode; G3T calls are 12/2/4 for off/on/verify, SAM calls are 10/10/10. Outputs and scores match, and room retains its call cap. Frozen modules and model forward are CPU stubs. |
| Empty-root preparation | Real prepare writes `d/settings.json`; real launch writes matching rule, mode, modules and verify IDs for both reads. Restore, manifest building and runtime-version receipts use documented stubs. `MEMO_BINDING.json` and `LOCAL_REHEARSAL.json` hold the receipts. |
| Memory admission | Two tests pass. SAM construction is forbidden during the fixed-bound helper test; bootstrap accepts a fitting fixed-shape receipt without a SAM measurement and rejects missing, nonfitting or mismatched policies. Seven CPU tensor dtypes retain bit-identical payload, shape, dtype and device. CUDA is untested. |
| Pre-memo baseline A/B | The 30-read baseline output hash matches current off/on/verify. |
| Replay | 600 runs, zero mismatches, eight matching expected errors, seven remaining candidate not-seen pairs per geometry. |
| EAT-1 | Zero new generate-path A3/A4 behavior versus a943 and e47. The raw a943 comparison has zero additions. The raw e47 comparison has two additions and two removals caused by the unchanged G3T body moving from __call__ to _fresh; AST equality proves the relocation. Raw scans and the unchanged reviewer scanner outputs remain available. |
| Broad legacy K1 suite | 31 pass; three failures and ten errors require absent K1 assets, matching W4. This is not a passing gate. See `legacy.log` and `TESTS.txt`. |

`TESTS.txt` records commands, exit codes, durations and logs, including setup failures and their passing follow-up checks. `EAT1_GATE.json` preserves the raw e47 delta and the AST relocation proof; no scanner or allowlist changed. Comparisons with the requested bases establish identity and are the only historical references retained under the no-archaeology skill.

The payload changes {len(audit['a9439d0fb0487']['changed'])} members and retains {audit['a9439d0fb0487']['unchanged']} identical members versus a943. It changes {len(audit['bf94a7976a7e9']['changed'])} members and retains {audit['bf94a7976a7e9']['unchanged']} identical members versus bf94. `PATCH.diff` and `FILE_SHA256_DIFF.tsv` use a943 as the default base; the explicitly named variants cover both requested bases. The PATCH diffs include operator-kit changes; the FILE_SHA256_DIFF tables cover sealed payload members. Protected decision/print files, frozen tree, heads, parity kit, reader core, items, scorers, statistics and row producers retain their bytes. `DELTA_AUDIT.json` records their hashes and the unchanged fresh-body and call-cap AST checks. Input and export descriptors remain pinned to their reviewed bytes; their internal logical namespace is unchanged.

| Artifact | SHA256 |
|---|---|
'''+''.join(f'| `{n}` | `{h}` |\n' for n,h in hashes.items())+f'''
The fixed G3T shapes bound payload at **3,335,080 bytes per capture**. The operator adds 1 MiB per capture for Python/allocator overhead, three transient capture copies, and a 64 GiB runtime allowance. Read 0 retains at most 84 captures and read 1 at most 60; their planning totals are **{mem['reads'][0]['host_budget_bytes']/1024**3:.3f} GiB** and **{mem['reads'][1]['host_budget_bytes']/1024**3:.3f} GiB**, below the 200 GiB allocation. Separate worker lifetimes keep these totals separate. SAM memo retention is zero. This bounds retained memo data; the runtime allowance is not a measured full-model peak RSS bound. Fresh SAM activations are transient runtime memory.

The estimate uses measured own-read means as timing proxies and 19.8 seconds per fresh G3T call. Fresh SAM work is present in those own-read measurements, but its encode-only contribution is **unmeasured**. The estimate credits no SAM memo savings and does not double-count an additional SAM time. G3T needs 79 calls for read 1 and 84 for read 0, including verification. Reads total **15,002.702 seconds**; staging/loading and stop margin add 3,600 seconds, yielding **5.167 hours**. The 1,200-second return margin lies inside the 1,800-second stop margin.

| Segment | Estimated incremental seconds | Fresh G3T calls |
|---|---:|---:|
'''+''.join(f"| Read {r['read']}: {r['type']} | {r['seconds']:.3f} | {r['g3t_calls']} |\n" for r in tim['segments'])+f'''
With 1,800 seconds for staging/loading, the stop deadline leaves 14,400 seconds for reads. Both distance reads and all camera types consume 14,018.721 seconds, leaving **381.279 seconds for room**. Thirteen room items finish before the proxy stop time; the fourteenth, `{tim['expected_cut']['id']}`, starts before it and may drain within the return margin. The expected return therefore contains about **764 of 786 items**, including every distance and camera item. Unmeasured overhead above the pre-room slack could move the cut earlier; ordering protects the selector comparison by running it first. Price is five times the approved H100 hourly rate plus the CPU check; no rate was supplied.

All work stayed in W5 and used the supplied CPU Python. No SSH, Git, network, submission, process kill or deletion ran. The real allocated CPU check and GPU reads remain operator actions. Rebuild with `out/build_package.py`, `out/build_operator.py`, then `out/build_delivery.py`; refresh audits with `work/audit_payload.py` and this report with `work/write_delivery_report.py`. `REMOVAL_CANDIDATES.md` identifies retained fixtures and unused copied scripts for user review.

'''+ops[ops.index('Place the delivery'): ]
(O/'REPORT.md').write_text(report)
(O/'REMOVAL_CANDIDATES.md').write_text('''All files remain in W5. No deletion ran or is requested by this delivery.

- `work/tmp/` and generated directories under `out/tests/` contain test fixtures; retain them while reviewing receipts that reference their paths.
- `work/existing_full/` and `work/pytest_tmp/` contain the legacy test harness and fixtures.
- `out/baseline/` is the read-only comparison snapshot copied into W5.
- `out/reader_repin/` and `out/orchard_h10/` are rebuild intermediates.
- Copied W4 implementation scripts in `work/` are provenance inputs, not W5 rebuild steps. Use only the rebuild and verification commands named in REPORT.md.

The user can remove these after review. The sealed archives, manifests, hashes, diffs, logs and evidence should remain together.
''')
print(json.dumps(dict(token=token,hashes=hashes),indent=2))
