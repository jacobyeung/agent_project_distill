from pathlib import Path
import hashlib,json
W=Path.cwd();O=W/'out';P=O/'package';token=(O/'TOKEN').read_text().strip()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
public=json.loads((P/'0.json').read_text());(O/'PACKAGE.json').write_bytes((P/'PACKAGE.json').read_bytes())
(O/'FILE_SHA256_DIFF.tsv').write_bytes((O/'FILE_SHA256_DIFF_vs_c91bb8ec884e9.tsv').read_bytes())
hashes={n:sha(O/n) for n in ('0.tgz','1.tgz','PACKAGE.json','tower_sequence.py','tower_bootstrap.py','node_check.py','READ_PLAN.json','inputs_tower.json','export_544.json')}
hashes.update(plan_sha256=public['plan_sha256'],BATCH_sha256=sha(P/'BATCH.sh'))
(O/'DELIVERY_SHA256.json').write_text(json.dumps(hashes,indent=2)+'\n')
def loc(name,needle):
 p=O/name;line=next(i for i,s in enumerate(p.read_text().splitlines(),1) if needle in s)
 return f'out/{name}:{line}'
time=json.loads((O/'TIME_PRICE.json').read_text())['case']['one_worker_per_read']
mem=json.loads((O/'MEMORY_BOUND.json').read_text())
scan=json.loads((O/'EAT1_W3_DELTA.json').read_text())
status=dict(token=token,local_required_gates='pass',production_ready=False,
 unresolved=['The 786-read estimate exceeds five hours by 602.702 seconds with the required margins.',
 'Production SAM feature memory and full-model host RSS are not measured; pinned model assets are absent locally.',
 'The allocated CPU restore/memory check and live GPU/device proof have not run.',
 'Legacy K1 suite: 31 passed, 3 failures and 10 errors from absent K1 assets.'],
 eat1_generate_path_new_findings=0,reader_scan_counts={'bf94':39,'c91':45,'new':39},replay_runs=600,replay_mismatches=0,
 expected_replay_errors=8,candidate_remaining_pairs=7)
(O/'GATES.json').write_text(json.dumps(status,indent=2)+'\n')
(O/'EAT1_GATE.json').write_text(json.dumps(dict(passed=True,scope='Generate-path files, including perception_memo.py, with the unchanged EAT-1 allowlist.',new_findings_vs_c91=[],before_c91=45,after=39,
 bf94_moved_findings=['TowerG3T.__call__ -> TowerG3T._fresh: model.safetensors','TowerG3T.__call__ -> TowerG3T._fresh: config.json'],
 moves_verified='Fresh body AST is unchanged; raw added/removed entries are preserved.',
 operator_added_findings=scan['added'],operator_explanation='run_types executes between generate calls. Its deadline comparison admits a new segment; its journal paths only record output and progress. These findings remain in the raw W3-method comparison.',
 raw_files=['EAT1_DELTA.json','EAT1_W3_DELTA.json','REVIEWER_EAT.json']),indent=2)+'\n')
commands=r'''```bash
set -euo pipefail
umask 077
: "${D:?Set D to the existing opaque delivery directory}"
P=/project/community/jjyeung/@TOKEN@
printf '%s  %s\n' @DELIVERY@ "$D/1.tgz" | sha256sum -c -
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00
```

Run the allocated empty-root CPU check once, after coordinating its staging IO. This command requests no GPU. It authenticates and restores the inputs, checks both read settings, rehearses selector wiring, and measures one real SAM encoding in CPU float32. It writes `a/c/CPU.json` and `a/c/MEMORY.json`; the bootstrap requires a measured, fitting memory receipt bound to this payload and operator. It does not decode a real evaluation item.

```bash
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" \
  srun --account=mt01 --partition=general --nodes=1 --ntasks=1 \
  --job-name=a15_cot_ap@TOKEN@ --cpus-per-task=8 --mem=200G \
  --time=04:00:00 --export=ALL \
  /usr/bin/python3 -I -s -B "$P/a/5.py" --package "$P" \
  --sequence "$P/a/6.py" --results "$P/a/c"
```

The submission command below remains conditional on the memory check, existing review requirements, and acceptance of a partial result under the five-hour cap. The current estimate does not support completing all 786 reads. Record the shared return pool's usage before submitting; the production write test also checks capacity before staging. Check the current `general` resource types and pending priority jobs:

```bash
sinfo -N -h -p general -o '%G' > "$P/a/7.txt"
/usr/bin/python3 -I -s -B - "$P/a/7.txt" <<'PYCODE'
import re,sys
from pathlib import Path
rows=[s.strip() for s in Path(sys.argv[1]).read_text().splitlines() if s.strip()]
gpu=[g for row in rows for g in row.split(',') if g.startswith('gpu:')]
assert rows and gpu
assert all(re.fullmatch(r'gpu:[^:]*[Hh]100[^:]*:[0-9]+(?:\([^)]*\))?',g) for g in gpu)
PYCODE
squeue -u "$USER" -h -o '%j %T' > "$P/a/9.txt"
/usr/bin/python3 -I -s -B - "$P/a/9.txt" <<'PYCODE'
import sys
from pathlib import Path
rows=[s.split() for s in Path(sys.argv[1]).read_text().splitlines()]
assert not any(len(r)>=2 and r[0].startswith('jjy_') and r[1] in ('PENDING','PD') for r in rows)
PYCODE
JOB_REPLY=$(/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 05:00:00)
JOB=${JOB_REPLY%%;*}
[[ "$JOB" =~ ^[0-9]+$ ]]
printf '%s\n' "$JOB" > "$P/a/8.txt"
```

Fetch after the return is published. The transport can label a clean partial result as failed because it lacks full-plan completion. Its summaries distinguish that case from a worker failure.

```bash
JOB=$(<"$P/a/8.txt")
RET=$(/usr/bin/python3 -I -s -B - "$JOB" <<'PYCODE'
import sys
print('@TOKEN@'+format(int(sys.argv[1]),'08x'))
PYCODE
)
/usr/bin/python3 -I -s -B 3.py fetch --return-token "$RET" --out "$P/a/f"
```

Transfer the bounded `a/f/0.tgz` and `a/f/EXIT.json` through the authorized operator channel into W4's `work/f/`. No transfer ran here. Then unpack and score locally:

```bash
cd /scratch/jjyeung/orch_n30/reader_r1/work/b1f
/scratch/jjyeung/envs/p1cpu/bin/python -B out/unpack_return.py \
  --archive work/f/0.tgz --exit work/f/EXIT.json --out work/ret
/scratch/jjyeung/envs/p1cpu/bin/python -B out/tower_pair.py \
  --package out/src \
  --own ../b1p/in/h10own/170631/items.jsonl ../b1p/in/h10own/170706/items.jsonl ../b1p/in/h10own/170694/items.jsonl \
  --tower-null work/ret/metadata/reads/0 \
  --tower-candidates work/ret/metadata/reads/1 \
  --out out/tower_results
```

A started segment without a journal makes unpacking fail. A journal-less read makes pairing fail. Valid partial journals remain partial; missing items cannot establish the camera comparison bar. Candidate-rule differences are in-sample.
'''.replace('@TOKEN@',token).replace('@DELIVERY@',hashes['1.tgz'])
operations=f'''Package **{token}** runs two isolated workers in one allocation. Read 0 keeps one generator and memo across distance, camera displacement, camera rotation, camera movement direction, and room; read 1 runs distance only. Read 0 has 636 items under `null_argmax`; read 1 has 150 under `candidates_argmax`. The settings explicitly list the first 30 scheduled distance IDs for verification in read 0. Its other IDs use memo `on`; read 1 uses `on` throughout. `READ_PLAN.json` contains the complete ID list.

The package is a review deliverable. Its local required gates pass, but its 5.167-hour estimate exceeds the five-hour cap and its real SAM memory footprint has not been measured. Production readiness remains unestablished. No job, network operation, SSH, Git command, or process kill ran in this task.

The delivery contains the payload and sealed operator helpers. Input declarations and step-544 SFT export pins remain byte-identical to W3/W2. Reuse their existing staged archives; preserve the fixed private logical namespace required by the policy receipt. Transfer only `1.tgz` into an opaque delivery directory. Public job names are `a15_cot_ap{token}`. Descriptive modules and settings remain inside the sealed payload and private dispatcher.

{commands}
'''
(O/'OPERATIONS_TOWER.md').write_text(operations)
report=f'''Package **{token}** implements F1, F2, F4, explicit-ID memo verification, and one worker per read. The required local suites, 600-run replay, return tests, and generate-path EAT-1 comparison pass. **This is not a production-ready release:** the full 786-read estimate is 5.167 hours with margins, and the real SAM footprint remains unmeasured because its pinned source and weights are absent from the authorized local inputs.

| Fix | Implementation | Evidence |
|---|---|---|
| F1: return every started segment | `{loc('tower_sequence.py',"root=base/'metadata/reads'")}` puts reads below returned metadata. `{loc('src/orchard_h10/runner.py',"config.get('cache_root'")}` keeps caches at `r/cache/<read>`, outside returned members. `{loc('unpack_return.py','def validate_journals')}` refuses missing journals/environments; `{loc('tower_pair.py','if not paths:raise')}` refuses empty reads. | `fixes_final.log`, `RETURN_MEMBERS.json`, `RETURN_CLI.json`: real subprocesses produce six journals; real `chain_save.members()` returns every journal, environment, progress, SUMMARY, STEPS and log, with no cache. The authenticated unpack CLI accepts all six and rejects an archive missing one. |
| F2: share top STOP | `{loc('tower_sequence.py',"'stop_file':")}`, `{loc('src/orchard_h10/runner.py',"'--stop-file'")}`, `{loc('src/orchard_h10/runner.py','marker=Path')}` pass the same `r/metadata/STOP` to runner and worker. | `STOP_PROOF.json`: a parent thread writes top STOP while the real worker subprocess is inside an item; the worker drains cleanly and returns one durable record. The deadline test also retains a partial summary and progress. |
| F4: bind b04 reuse | `{loc('src/h1eval/h10/parity_adapter.py',"for field in ('stage1_select_rule'")}` compares explicit rule, memo mode and verify IDs in `LOAD_RECEIPT.json`. Missing keys refuse reuse. | `test_b04_reuse_rejects_rule_and_memo_from_launcher` in `fixes_final.log` exercises `launch.run --tower-from` and independently rejects all three mismatches with a structurally authenticated b04 receipt. |
| M1: remove reader bookkeeping thresholds | `{loc('src/b/e2e_reader/perception_memo.py','def settings')}`, `{loc('src/b/e2e_reader/perception_memo.py','def store_value')}`, `{loc('src/b/e2e_reader/perception_memo.py','def begin_read')}` use explicit ID membership and an unbounded process-local host store. `{loc('src/b/e2e_reader/parity.py','memo.item_id')}` supplies the item ID. | `memo.log`, `MEMO_BINDING.json`, `MEMORY_BOUND.json`: missing production setting keys fail; ID membership survives out-of-order resume; mutation, no-IO, key sensitivity, process isolation and signed-zero mismatch tests pass. CPU tensor hits retain dtype, shape, device and exact bytes across seven dtypes. CUDA was not available. |
| M2: retain one generator across types | `{loc('src/orchard_h10/runner.py',"if config.get('single_worker'):")}`, `{loc('src/h1eval/h10/launch.py','def run_types')}`, `{loc('src/h1eval/h10/launch.py','if generators is not None:generators')}` route one worker into ordered per-type journals. | `RETURN_MEMBERS.json` proves one subprocess per read and distinct PIDs between reads. `MULTITYPE_AB.json` proves one model load across all five types, response/score parity, cross-type memo hits and the room call cap through the real capped parity reader. |

`in/refute_members.py` and `in/eat.py` are retained unchanged. `work/refute_members.py` adapts only the reproducer's workspace, returned layout and six-type list; it prints all six journals. `work/reviewer_eat.py` preserves the reviewer's scan logic and changes only old/new roots. `reviewer_checks.log` records both runs. The original reproducer hard-codes the obsolete unreturned layout, so it cannot exercise the new layout unchanged.

The four protected source files remain byte-identical to c91: `stage1.py`, `grounding.py`, `servers.py`, and `perception_own.py`. This preserves W3's memo wiring and the reviewed decision/print logic. The fresh G3T body and call-cap factory retain identical ASTs. The tree, heads, parity kit, reader core, items, scorers, statistics and row producers retain their bytes. `DELTA_AUDIT.json` records full protected hashes. The payload has 919 identical members and eight changed members versus c91; it has 913 identical members and 14 changed or added members versus bf94. Both `FILE_SHA256_DIFF_vs_*.tsv` files include identical members as well as changes. Both `PATCH_vs_*.diff` files include payload and operator-kit changes; `PATCH.diff` is the bf94 comparison.

| Artifact | SHA256 |
|---|---|
'''+''.join(f'| `{n}` | `{v}` |\n' for n,v in hashes.items())+f'''
The read schedule is `(0,3),(0,0),(0,1),(0,2),(0,4),(1,3)`. Types 3, 0, 1, 2 and 4 mean distance, displacement, rotation, movement direction and room, respectively. Each type preserves manifest order. Read 0 verifies the explicit first 30 distance IDs and then uses hits without recomputation; read 1 uses memo `on`. Reads use separate processes, rules, settings, identities and journals. A verification mismatch serves the fresh value and disables all memo instances in that process. The settings bind `perception_memo_verify_ids`; production launch refuses a missing mode, ID list or selector rule.

| Local gate | Result |
|---|---|
| Package / constraints | 14 / 9 pass. |
| B1 runtime / stubs / tower wiring | 8 / 6 / 7 pass. |
| Sequence / pairing / B1 report | 5 / 6 / 1 pass. |
| Memo / bindings | 8 / 4 pass; includes A/B, sensitivity, defensive copies, no eviction, no IO, mismatch disable, process isolation, prefill sensitivity and explicit-ID resume. |
| F1/F2/F4/deadline | Five tests pass, plus authenticated unpack CLI tests and the adapted reviewer return reproducer. |
| Multi-type A/B | Twelve reads across all five types per mode. Off/on/verify outputs share one hash; model loads are 1/1/1, G3T calls are 12/2/4 and SAM encodes are 10/2/4. Room reads stop at the unchanged two-call cap. Frozen modules and model forward use CPU stubs. |
| Memory helper / bootstrap | Two CPU tests pass: the probe measures a stub encoding and the bootstrap rejects missing or nonfitting measured receipts. The real production encoding remains unmeasured. |
| Empty-root preparation | Real `prepare.run` writes `d/settings.json`; real launch writes matching environment bindings for both read policies. Restore, manifest construction and version receipt use documented stubs. `LOCAL_REHEARSAL.json` validates payload pins and the two worker argument sets. |
| Pre-memo baseline A/B | The 30-read pre-memo fixture matches the current off/on/verify output hash. |
| Replay | 600 runs, zero mismatches, eight matching expected errors; candidates retain seven not-seen pairs per geometry (six SAM-empty and one raster case). |
| EAT-1 | Zero new A3/A4 findings in generate-path files versus c91. The expanded reader scan falls from 45 to 39. The bf94/e47 count is also 39; two existing file literals move from `TowerG3T.__call__` to `_fresh`, with unchanged fresh-body AST. |
| Broad legacy K1 suite | 31 pass; three failures and ten errors require absent K1 assets, matching W3's limitation. This is not a passing gate. |

`TESTS.txt` records commands, exit codes and logs, including failed setup attempts and their passing final checks. The W3 scan method retains all changed-file findings: {scan['before']} before, {scan['after']} after, {len(scan['added'])} operator additions and {len(scan['removed'])} removals. The additions are journal paths and the segment deadline in `launch.run_types`, outside `generate()`. No allowlist or scanner changed, and no finding was hidden. `EAT1_GATE.json`, the raw scans and `REVIEWER_EAT.json` explain the scope and relocation.

The host-memory plan measures tensor payload directly; it does not infer safety from a byte cap. G3T's fixed shapes bound retained scalar payload at {mem['shape_sensitivity'][0]['g3t_capture_bytes_upper']:,} bytes per capture using eight bytes per scalar. For measured one-frame SAM payload B, a capture retains at most `32*B + G3T + 1 MiB` in this plan. Read 0 retains 84 captures; read 1 retains 60. The plan adds three transient capture copies and a 64 GiB runtime allowance, then compares against the 200 GiB allocation. The runtime allowance is not a measured full-model RSS bound.

`MEMORY_BOUND.json` deliberately reports `production_measurement_available=false`. Its shape sensitivity allocates CPU feature tensors and measures their exact payload: one 256-channel 72×72 level in each of two FP32 pyramids fits; three 288/144/72 levels do not. These are scenarios, not measurements of the pinned SAM model. `{loc('tower_sequence.py','def memory_probe')}` makes the allocated CPU helper encode an authenticated frame using real SAM weights at FP32, writes the measured bound, and refuses an oversized result. The bootstrap requires this measured receipt. CPU copies are bit-identical; a CUDA-device proof and real production memory measurement remain outstanding. The advisory real-item CPU decode gate also remains unrun.

For reference, the measured shape scenarios give these read-0 planning totals. Neither row identifies the pinned model's actual feature shapes.

| CPU FP32 feature scenario | SAM bytes per frame | Retained memo, GiB | Memo + transient copies + runtime allowance, GiB | Fits 200 GiB? |
|---|---:|---:|---:|---|
{''.join(f"| {r['name']} | {r['sam_frame_bytes']:,} | {r['reads'][0]['memo_bytes']/1024**3:.3f} | {r['reads'][0]['host_budget_bytes']/1024**3:.3f} | {r['fits']} |\n" for r in mem['shape_sensitivity'])}

The time estimate uses W2's measured own-read means and the supplied 19.8-second fresh G3T cost. Own-read time totals 11,775.302 seconds. Read 0 needs 84 fresh captures plus 19 verification-hit recomputations; read 1 needs 60 fresh captures. Thus 163 G3T calls add 3,227.4 seconds, giving 15,002.702 seconds (4.167 hours) of reads. Adding 1,800 seconds for staging/loading and the 1,800-second stop margin gives **5.167 hours**, 602.702 seconds above the cap. The 1,200-second return margin lies inside the stop margin. Even staging plus only the return margin gives 5.00075 hours. SAM savings and GPU decode/copy overheads are unmeasured. All 786 reads therefore do not fit under this estimate. The job still stops at the fixed deadline and returns partial journals. Price is five times the approved H100 hourly rate, plus the separate CPU check; no rate was supplied.

The following operator commands are exact and have not run. `OPERATIONS_TOWER.md` contains the same commands and prerequisites.

{commands}
Rebuild from W4 with `out/build_package.py`, `out/build_operator.py`, and `out/build_delivery.py`, using `/scratch/jjyeung/envs/p1cpu/bin/python -B`. Run `work/audit_payload.py` and `work/write_delivery_report.py` to refresh comparisons and report hashes. All task-created files stay in W4; its retained size is below 3 GB. No deletion command ran. `REMOVAL_CANDIDATES.md` lists fixtures and unused copied scripts for user review. The no-archaeology skill governs this report; comparisons with the requested bases remain because they establish identity, not revision history.
'''
(O/'REPORT.md').write_text(report)
(O/'REMOVAL_CANDIDATES.md').write_text('No files were deleted. All paths below are inside W4.\n\n- `work/tmp/`, `work/pytest_tmp/`, and generated directories under `out/tests/` hold reproducible CPU fixtures.\n- `out/reader_repin/`, `out/orchard_h10/`, and `out/package/` are reproducible build intermediates; retain them while reviewing or reproducing the package.\n- `out/baseline/` supports baseline A/B and audit checks.\n- Copied W3 helpers `work/implement.py`, `work/fix_policy.py`, `work/wire_operator.py`, `work/write_reports.py`, `work/static_review.py`, `work/final_verify.py`, and `work/audit_memo.py` are not the W4 build or validation workflow.\n- Failed setup logs remain as evidence in `TESTS.txt`; preserve final passing receipts and all deliverables.\n')
print(json.dumps(dict(token=token,hashes=hashes,status=status),indent=2))
