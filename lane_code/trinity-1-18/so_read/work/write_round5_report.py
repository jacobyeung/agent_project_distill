"""Write the current delivery contract with exact CPU outputs."""
import json,re,shlex,subprocess
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out';C=O/'checks'
m=json.loads((O/'patches/MANIFEST.json').read_text());r=json.loads((C/'RESULTS.json').read_text())
cost=json.loads((C/'CACHE_COST3.json').read_text());old=(L/'out_round5/REPORT.md').read_text()
count=lambda rows:sum(int(re.search(r'Ran (\d+) tests?',(C/x['output']).read_text()).group(1)) for x in rows)
workspace=count(r['results']);applied=count(m['applied_cpu_suites'])
stamp=subprocess.check_output(['date','-u'],text=True).strip();size=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0])
bench='\n'.join('| '+str(v['parameter_count'])+' | '+str(v['parameter_tensors'])+'/'+str(v['buffer_tensors'])+' | '+str(v['weight_and_buffer_bytes'])+' | '+f"{v['before_per_call']['median_seconds']*1000:.3f}"+' | '+f"{v['after_per_call']['median_seconds']*1000:.3f}"+' | '+f"{v['after_install_seconds']:.3f}"+' | '+f"{v['boundary']['median_seconds']:.3f}"+' |' for v in cost['cases'])
patches='\n'.join('| ['+name+'](patches/'+name+') | '+str(pin['bytes'])+' | `'+pin['sha256']+'` |' for name,pin in m['patches'].items())
review5=(O/'kit_parity50/README.md').read_text().split('## Review round 5: finding -> fix -> test')[1]
review4=old[old.index('## Review round 4: finding -> fix -> test'):old.index('The requested findings are fixed.')]
prior=old[old.index('### Review round 1: finding -> fix -> test'):old.index('## Patches and measured resource bounds')]
equality=old[old.index('## Equality and mutation limits'):old.index('## Measured CPU guard overhead')]
profile=old[old.index('## Measured profile and forecast'):old.index('## Framework evidence')]
profile=profile.replace('354.53 / 239.33','354.53 / 239.53')
profile=profile[:profile.index('**Estimated forecast:**')]+'''**Estimate for what a19 builds:** the 636-item A4 schedule takes about **7,351.824 s (2 h 02 min 32 s; 11.559 s/item including fixed overhead)** if the supplied A4 throughput carries forward, with zero assumed cache saving. This is not a step-600 measurement. Target weights, cache guard/copy costs, actual reuse and staging can change it.

**Separate Package D estimate:** the 580-item distance read is a B5 fork with a 03:30 walltime and has **no ON route in a19**. Using 23.599762 s/item plus 75.446133 s loading and 49.761372 s overhead gives an estimate of **13,813.069 s (3 h 50 min)** on one card. Ideal two/four balanced-shard estimates are 6,969.138 / 3,547.173 s; they require an undelivered multi-card operator and exclude scene imbalance, staging, queues and preemption. The fixed 50-item reuse-heavy sample cannot establish these throughput estimates.

'''
report=f'''VERDICT: DONE All requested round-5 fixes pass CPU verification; production adoption still requires the GPU byte gate.

Measured validation: **{workspace} workspace tests and {applied} fresh-application tests pass**. Five patches apply with zero fuzz; all original reader files remain unchanged. Complete original/OFF fixture output bytes match, including source hashes. ON CPU fixtures retain exact answers and traces. The seven round-5 tests produce eleven expected assertion failures against the reviewed implementation; all nine fail-before controls reproduce.

The bound step-600 package preserves A4's 636-item, single-card, cache-only profile and export binding. Its batch includes cont_ops' exclusion, EXIT log return and USR1 forwarding. Its builder authenticates the reviewed payload, patched operators, extension inventory and alias bases before copying. The handover includes executable binding/delivery/operation helpers and pins the GPU gate to the actual prepared profile.

The full-suite driver completed every test, then **failed its final workspace-size assertion**. An interim measurement was **3,004,528,639 bytes**, above the 3,000,000,000-byte cap. Identical files in completed retained fixtures now share inodes; every path and byte was preserved. The measured workspace at report generation is **{size:,} bytes**. This exception is recorded, not treated as a test pass. [run_checks5.txt](checks/run_checks5.txt) retains the failed driver output; [finish_checks5.txt](checks/finish_checks5.txt) records the corrected resource check. The driver's peak RSS was not captured before its assertion.

Measured environment: torch {r['torch']}, transformers {r['transformers']}, eight torch threads, CUDA hidden. All compute used nice -n 10 and the prescribed thread/cache environment. The separate CPU guard benchmark measured peak RSS **{cost['max_rss_bytes']:,} bytes**, below 30 GiB. No GPU, Git, SSH, scheduler action, paid API, file-deletion command or input-tree edit ran. Network reads were confined to official PyTorch documentation.

The untouched delivery backup is [out_round5](../out_round5/). Work began at 13:56:45 UTC; the deadline is 15:26:45 UTC on 2026-11-19. This report was generated at {stamp}.

## Review round 5: finding -> fix -> test
{review5}

The wrapper is vendored verbatim from cont_ops17/work/build_r10.py:73–84, without importing that script's executable body. The built wrapper equals the reference output and passes the real bundle guard. Input mutations are stopped before copying: self-consistent replacement base, each operator file, extension content/inventory, disagreement between review inventories and alias-base pins.

The operation helper derives binding fields from authenticated artifact/receipt/preparation files while preserving reviewed done/prep_paths. The generated submission checker runs as real Python in tests: it refuses missing cache-memory evidence and a simulated pool size of 75,000,001 bytes; exactly 75,000,000 passes. Generated shell syntax, Python-3.6 syntax, delivery contents and the queue/CPU/dry-check ordering are tested. No scheduler or large export fetch is exercised by those CPU tests.

The GPU gate checks both all-cache and processor-only profiles. It rejects changed run settings, selectors, numeric types, budget or plan pin. Changed prepared bytes fail the READY proof check. An additional integration check feeds the real applied A4 CPU proof and its exact SETTINGS.json into this gate. Each RUN.json records the adopted plan/profile. Finding 7 uses the review's documented success-output rule; unpack extraction behavior is unchanged. Finding 6 remains A4's reviewed fill-time whole-archive enforcement; job/unpack compare against inputs.archives[0].

## Adoption contract

Follow [README.md](kit_parity50/README.md) in order: apply patches to fresh A4 copies; derive the reviewed target binding; build; generate and place the pinned delivery; fetch/fill and run both dry checks; run the allocated CPU proof; derive/seal the exact prepared profile; pass the GPU gate; guarded submit; fetch and authenticate/unpack. A real target export and owner-authorized transport/allocation remain external inputs. The synthetic CPU binding is not production evidence.

```bash
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \\
  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \\
  --manifest "$DELIVERY/patches/MANIFEST.json" --extension-pins "$DELIVERY/kit_parity50/EXTENSION_PINS.json" \\
  --export-binding "$STEP600_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/step600"
```

Add --processor-only for the 4 GiB processor cache; the full profile uses 12 GiB. Both disable atomic journals and sharding. The intended GPU read uses general/no-requeue, one GPU and 04:30:00. The separate CPU-proof allocation uses preempt without a GPU, as in A4 operations.

The submit preflight requires CPU payload/plan/inputs/operator bindings and entry/bundle success, both dry-check passes, the exact cache allowance with fits=true, an empty general queue and a return pool at most 75,000,000 bytes. The unchanged bootstrap does not independently require read_cache_bytes. The GPU gate seals candidates_argmax, memo on, g3t, empty verify IDs, save_own_depth=false and the exact cache switches/budget from the built package. Processor-only adoption needs its own gate.

A refused unpack leaves its extracted tree behind. Scorers consume only success output after exit status 0. A successful partial return remains partial. No multi-card A4 operator is delivered; persistent-storage requeue remains a separate prerequisite for preempt/sharded adoption.

{equality}
{profile}
## Measured CPU guard overhead

Each stub uses bf16 parameters shaped 2048×1024 and a 1024-element buffer per module. Forward returns a 32-element tensor without model-sized matrix work. Each implementation runs one miss and a warm hit, then seven timed hits; boundary cost is the median of three hashes. These are CPU validation/cache costs, not GPU speedups.

| Parameters | Parameter/buffer tensors | Weight+buffer bytes | Per-call hashing ms | Boundary guard ms/call | Install s | Boundary s |
|---:|---:|---:|---:|---:|---:|---:|---:|
{bench}

Exact samples are in [CACHE_COST3.json](checks/CACHE_COST3.json), rerun during this task. Actual H100 costs and full-process GPU/host peaks remain unmeasured. Cache caps bound cache-owned storage and transient copies, not all model/caller memory.

## Framework evidence

[FRAMEWORK_EVIDENCE.md](FRAMEWORK_EVIDENCE.md) records installed torch/transformers file:line citations. This task reread torch TensorImpl.h:291–305, 413–418 and 2046–2056; autograd/graph.py:242–258; optim/sgd.py:378–380; and InferenceMode.h:30–50 under `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/`. Tracked in-place operations update counters; detach shares them; .data/set_data and raw storage writes need additional guards. Inference tensors lack counters.

The official [increment_version documentation](https://docs.pytorch.org/docs/2.11/generated/torch.autograd.graph.increment_version.html) and [inference_mode reference](https://docs.pytorch.org/docs/2.11/generated/torch.autograd.grad_mode.inference_mode.html) were checked on 2026-11-19. [TORCH_VERSIONS3.json](checks/TORCH_VERSIONS3.json) contains the rerun probes and source hashes. Packaging and profile validation introduce no new framework behavior.

## Patches and authentication

A4 source base: `{m['base_pin']['sha256']}` over {m['base_pin']['files']} files. Reviewed A4 payload: `{m['a4_payload_pin']['sha256']}`, {m['a4_payload_pin']['bytes']} bytes. B5 archive: `{m['b5_base_archive_sha256']}`. B5 application proves patch applicability; the GPU kit authenticates A4 only.

| Patch | Bytes | SHA256 |
|---|---:|---|
{patches}

Reader patches 01–03 add 35 files under u0; original reader bytes remain unchanged. Operator patches 04–05 apply outside src and affect tower_sequence.py, unpack_return.py and package/a/5.py behind read_extensions. The bootstrap remains byte-identical. Tests ship in the reader patches. The kit and verbatim cont_ops dry helpers are separately pinned in [MANIFEST.json](patches/MANIFEST.json).

Every workspace suite ran. The affected round-5 suite reran after strict profile-type checks were added. Fresh-application OFF, round-4, round-5 and comparator suites pass; other applied source bytes match their tested workspace counterparts. The fixture storage wrapper shares reviewed immutable source bytes and repeated archives, detaching shared files before edits. Retained fixtures were also shared without removing any path. [FIXTURE_STORAGE5.json](checks/FIXTURE_STORAGE5.json) and the storage command outputs document the resource correction.

## What could go wrong and how to notice

| Risk | Detection/action |
|---|---|
| Wrong base, skipped operator patch or modified overlay | a19 refuses payload/operator/extension/alias mismatches before copying. |
| Wrong target export/preparation or stale CPU proof | Binding derivation, sealed fill constants, package/admission pins and submit preflight reject mismatches. Never use the synthetic binding. |
| GPU gate tests a different read/cache profile | Prepared-settings proof and parent/worker validation reject it; RUN.json retains the plan/profile. |
| Pool full, queue occupied or memory allowance missing | Generated submit refuses before submission. Pool tests simulate stat sizes. |
| Refused or partial return gets scored | Require unpack exit 0 and success JSON; treat complete=false separately. A directory alone is not admission. |
| GPU kernels, eager SAM, layout or RNG change bytes | Require zero answer/trace differences; equal scores do not waive the gate. |
| Hash/copy cost erases savings or cache caps miss process memory | Require useful hits, lower full worker_wall_seconds and measured full-process headroom. |
| Hard death or untracked mutation | Unverified receipts fail ON unpack; fresh journals may be needed. Restored-between-boundary raw writes remain unsupported. |
| Real transport, restore, namespace or requeue differs from stubs | Validate on the intended system; no preempt/sharded adoption before persistent-storage requeue checks. |
| Fixture storage approaches the cap | Check unique-inode bytes with du -sb. The aggregate driver caught an overrun; the exact failure is retained and corrected checks pass. |

## Not done

No real step-600 export/binding build, weight restore, production namespace/storage/transport, GPU parity/performance/memory, scheduler action, upload, return publication or persistent-storage requeue ran. No batching or multi-card A4 operator is delivered. The array policy remains approved=false. No delivered CPU suite requires local OS sockets; socket-backed integrations remain unrun. The ON GPU byte gate remains required.

## Required review audit sections

{review4}
{prior}
## Commands and exact outputs

Commands ran from `/scratch/jjyeung/orch_n30/so_read`. work/cpu.sh exports CUDA_VISIBLE_DEVICES="", OMP/MKL/OPENBLAS threads=8, TOKENIZERS_PARALLELISM=false, PYTHONDONTWRITEBYTECODE=1 and scratch caches, then runs nice -n 10 with the required Python -I -s -B. Children inherit the environment/priority. Tests also receive READ_INPUT_SRC={m['base']} and READ_TEST_TMP={L/'work/test-artifacts'}. Fresh-application commands additionally set READ_OPERATOR_SOURCE and READ_OPERATOR4_SOURCE from MANIFEST's verification root/operator. work/run_fixture5.py changes only fixture storage while preserving bytes.

'''
def block(command,name):
 return '```bash\n'+command+'\n```\n\nExact output:\n\n```text\n'+(C/name).read_text().rstrip()+'\n```\n\n'
for command,name in [('bash work/cpu.sh work/gate_integration5.py','gate_integration5.txt'),('bash work/cpu.sh work/profile.py','profile_rerun.txt'),('bash work/cpu.sh work/torch_versions3.py','torch_versions3.txt'),('bash work/cpu.sh work/benchmark_round3.py','cache_cost3.txt'),('bash work/cpu.sh work/run_checks.py','run_checks5.txt'),('bash work/cpu.sh work/finish_checks5.py','finish_checks5.txt'),('bash work/cpu.sh work/dedup_fixture5.py','fixture_storage5.txt'),('bash work/cpu.sh work/share_retained5.py','retained_storage5.txt'),('bash work/cpu.sh work/run_fixture5.py work/build_patches.py','build_patches5.txt')]:report+=block(command,name)
for row in [*r['results'],*m['applied_cpu_suites']]:report+=block(shlex.join(row['command']),row['output'])
for name,script,var,args in [('round1_before','test_round1.py','READ_REVIEW_BEFORE',[]),('round2_before','test_round2.py','READ_ROUND2_BEFORE',[]),('round3_before','test_round3.py','READ_ROUND3_BEFORE',[]),('operator3_before','test_operator_round3.py','READ_ROUND3_BEFORE',[]),('lock3_before','test_lock_round3.py','READ_LOCK_BEFORE',[]),('round5_before','test_round5.py','READ_ROUND5_BEFORE',[]),('round4_before','test_round4.py','READ_ROUND4_BEFORE',[]),('node4_before','test_round4.py','READ_NODE4_BEFORE',['Round4Tests.test_f2_step600_real_job_and_rehearsal_memory']),('f16_behavior_before','test_round3.py','READ_F16_BEFORE',['Round3Tests.test_f4_worker_uses_settings_argv_without_environment_side_effect'])]:
 report+=block(var+'=1 bash work/cpu.sh work/run_fixture5.py work/src/u0/tests/'+script+(' '+shlex.join(args) if args else ''),name+'.txt')
report+='The final seal is checked by `bash work/cpu.sh work/integrity5.py`. Its exact output is in [integrity5.txt](checks/integrity5.txt); [FINAL_INTEGRITY.json](checks/FINAL_INTEGRITY.json) pins the report, NOTE, README, framework evidence, MANIFEST, patches, operations and checks. The integrity output remains external to avoid a report/hash cycle.\n'
(O/'REPORT.md').write_text(report)
with (L/'work/STATUS.md').open('a') as f:f.write(stamp+'\nRegenerated five patches and MANIFEST; 21 fresh-application tests passed. REPORT and NOTE record requested fixes, exact outputs, scoped estimates, the storage exception and unrun GPU gate. Final integrity seal pending.\n')
print('Report written:',workspace,'workspace tests;',applied,'fresh-application tests;',len(report.encode()),'report bytes.')
print('Workspace sample:',size,'bytes; report time:',stamp)
