"""Write the reviewable package audit, operator runbook, and bounded size receipt."""
from pathlib import Path
import difflib,hashlib,json,re,tarfile
W=Path(__file__).resolve().parents[1];O=W/'out';P=O/'src';B=W.parent/'b1g/out'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def line(p,needle):return next(i for i,s in enumerate(p.read_text().splitlines(),1) if needle in s)
token=(O/'TOKEN').read_text().strip();price=json.loads((O/'TIME_PRICE.json').read_text());plan=json.loads((O/'READ_PLAN.json').read_text())
files=['0.tgz','1.tgz','PACKAGE.json','READ_PLAN.json','inputs_tower.json','export_544.json','tower_sequence.py','tower_bootstrap.py','node_check.py','room_pair.py','unpack_return.py','src/items/room134.json','src/inputs/room_captures.json','LOCAL_CPU_CHECK.json','LOCAL_NATIVE_CPU_CHECK.json','CPU_HELPER_TEST.json','W5_BINDING_EQUIVALENCE.json','OPERATOR_ONLY_AUDIT.json']
hashes={n:dict(bytes=(O/n).stat().st_size,sha256=sha(O/n)) for n in files}
(O/'HASHES.json').write_text(json.dumps(hashes,indent=2,sort_keys=True)+'\n')
with tarfile.open(O/'0.tgz') as t:new={m.name:t.extractfile(m).read() for m in t}
with tarfile.open(B/'0.tgz') as t:old={m.name:t.extractfile(m).read() for m in t}
changed=sorted(n for n in old.keys()|new.keys() if old.get(n)!=new.get(n));same=sorted(n for n in old.keys()&new.keys() if old[n]==new[n])
protected=[n for n in old if n.startswith(('b/e2e_reader/','b/parity_kit/','b/heads/','tree/')) or n in ('h1eval/scorers.py','h1eval/statistics.py')]
assert all(old[n]==new[n] for n in protected)
patch=[]
for n in changed:
 a=(old.get(n,b'')).decode();b=(new.get(n,b'')).decode()
 patch.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='W5/out/src/'+n,tofile='W6/out/src/'+n))
for n in ('build_package.py','build_operator.py','build_delivery.py','tower_sequence.py','tower_bootstrap.py','node_check.py','inputs_tower.json','unpack_return.py'):
 a=(B/n).read_text();b=(O/n).read_text()
 if a!=b:patch.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='W5/out/'+n,tofile='W6/out/'+n))
patch.extend(difflib.unified_diff([], (O/'room_pair.py').read_text().splitlines(True),fromfile='/dev/null',tofile='W6/out/room_pair.py'))
(O/'PATCH.diff').write_text(''.join(patch))
(O/'PAYLOAD_AUDIT.json').write_text(json.dumps(dict(changed=changed,identical=len(same),protected_identical=len(protected),one_item_file=[n for n in new if n.startswith('items/')],base_sha256=sha(B/'0.tgz'),payload_sha256=sha(O/'0.tgz')),indent=2)+'\n')
ops=f'''Package `{token}` runs one development-only, 134-item room read at SFT step 544. The read uses tower, mode none, null_argmax, memo on for G3T only, no verification IDs, and no own-depth output. R0-dev must never supply fitting data.

The allocated Orchard CPU check must pass before submission. It runs the first dev-S1 and first R0-dev item after authenticated staging and export restore. Local fixtures validate the check implementation; they do not authenticate Orchard-only dev-S1 image bytes. No Orchard check or GPU run occurred in this lane.

Place the delivery from an existing opaque delivery directory. Set `D` to that directory. These are operator commands; this lane ran none of them.

```bash
set -euo pipefail
umask 077
: "${{D:?Set D to the existing opaque delivery directory}}"
P=/project/community/jjyeung/{token}
printf '%s  %s\\n' {hashes['1.tgz']['sha256']} "$D/1.tgz" | sha256sum -c -
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 02:30:00
```

Coordinate staging IO before this allocated CPU check. It requests eight CPUs and no GPU. The helper creates a fresh private root, authenticates archives, restores the export, then runs both items through real launch, mixed native mapping, SHA256 verification, PNG decoding, ParityGenerator, CallHook, the decode loop and official scoring. Model forward, weights, tokenizer, prompt tensors, audit enforcement and decode budget use explicit CPU stubs. Any failure exits nonzero and prevents a passing CPU receipt. The allocation matches W5: general, eight CPUs, 200G, four hours, no GPU. The four-hour limit permits staging; it is not a timing estimate.

```bash
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" CUDA_VISIBLE_DEVICES= \\
  srun --account=mt01 --partition=general --nodes=1 --ntasks=1 \\
  --job-name=a15_cot_ap{token} --cpus-per-task=8 --mem=200G \\
  --time=04:00:00 --export=ALL \\
  /usr/bin/python3 -I -s -B "$P/a/5.py" --package "$P" \\
  --sequence "$P/a/6.py" --results "$P/a/c"
```

Read and verify the pass flag and both finished records after the CPU command exits successfully. `CPU.json` embeds the records under `full_reader.records`; `FULL_READER.json` repeats that proof. These scores validate the stub path, not model quality.

```bash
/usr/bin/python3 -I -s -B - "$P" <<'PYCODE'
import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1]);c=json.loads((p/'a/c/CPU.json').read_text());v=json.loads((p/'0.json').read_text())
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert c['passed'] is True and c['full_reader_passed'] is True
assert c['full_reader']['passed'] is True and c['full_reader']['device']=='cpu'
assert c['payload']==v['payload_sha256'] and c['plan']==v['plan_sha256']
assert c['operator_sha256']==sha(p/'a/6.py') and c['inputs']==sha(p/'a/1.json')
rows=c['full_reader']['records']
assert [(r['set'],r['item']) for r in rows]==[('dev-S1','room_scene0155_00'),('R0-dev','r0_015bd4aaf6870d79bade')]
assert all(r['passed'] is True and r['record']['complete'] is True and r['record']['output']['finish']=='eos' for r in rows)
print('full_reader_passed=true')
for r in rows:print(r['set'],r['item'],r['record']['output']['finish'],r['ground_truth_score']['score'])
PYCODE
```

Submit only after this command passes. The bootstrap also refuses receipts without `full_reader_passed=true`, the full-reader pass, matching payload, plan, inputs and operator hashes, and the passing memory bound. Record the shared return pool's current usage in the operator ledger; the production write test checks capacity before staging. Check the H100 resource type and pending priority jobs, then submit one GPU for 02:30:00.

```bash
sinfo -N -h -p general -o '%G' > "$P/a/7.txt"
/usr/bin/python3 -I -s -B - "$P/a/7.txt" <<'PYCODE'
import re,sys
from pathlib import Path
rows=[s.strip() for s in Path(sys.argv[1]).read_text().splitlines() if s.strip()]
gpu=[g for row in rows for g in row.split(',') if g.startswith('gpu:')]
assert rows and gpu
assert all(re.fullmatch(r'gpu:[^:]*[Hh]100[^:]*:[0-9]+(?:\\([^)]*\\))?',g) for g in gpu)
PYCODE
squeue -u "$USER" -h -o '%j %T' > "$P/a/9.txt"
/usr/bin/python3 -I -s -B - "$P/a/9.txt" <<'PYCODE'
import sys
from pathlib import Path
rows=[s.split() for s in Path(sys.argv[1]).read_text().splitlines()]
assert not any(len(r)>=2 and r[0].startswith('jjy_') and r[1] in ('PENDING','PD') for r in rows)
PYCODE
JOB_REPLY=$(/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 02:30:00)
JOB=${{JOB_REPLY%%;*}}
[[ "$JOB" =~ ^[0-9]+$ ]]
printf '%s\\n' "$JOB" > "$P/a/8.txt"
```

Fetch after publication. The original pool and GCS transport remain pinned to W5.

```bash
JOB=$(<"$P/a/8.txt")
RET=$(/usr/bin/python3 -I -s -B - "$JOB" <<'PYCODE'
import sys
print('{token}'+format(int(sys.argv[1]),'08x'))
PYCODE
)
/usr/bin/python3 -I -s -B 3.py fetch --return-token "$RET" --out "$P/a/f"
```

Transfer only `a/f/0.tgz` and `a/f/EXIT.json` through the authorized operator channel into W6's `work/f/`. No transfer ran here. On Trinity, unpack and score:

```bash
cd {W}
/scratch/jjyeung/envs/p1cpu/bin/python -B out/unpack_return.py \\
  --archive work/f/0.tgz --exit work/f/EXIT.json --out work/ret
/scratch/jjyeung/envs/p1cpu/bin/python -B out/room_pair.py \\
  --return-root work/ret --out out/scores
```

The scorer reports per-item MRA, dev-S1 (36), R0-dev (98), and all (134), plus capped reads and recorded malformed-call diagnostics. It recomputes MRA against each item's ground_truth with the unchanged official scorer. It pairs by exact ID and physical-room key, rejects changed bindings and duplicates, and lists missing items without inventing scores. A partial return remains explicitly incomplete. `--allow-fixture` is reserved for the synthetic test.

The stop margin is 1,800 seconds; the return margin is 1,200 seconds within it. The read estimate is {price['read_seconds']:.1f} seconds, staging/loading is 1,920 seconds, and the minimum total is {price['required_seconds']:.1f} seconds. Two hours fails; 02:30:00 leaves {price['stop_deadline_slack_seconds']:.1f} seconds of estimated slack. Price is 2.5 H100-hours plus the CPU check; no hourly rate was supplied.

The row estimate is 2,492,400 raw bytes and 428,800 compressed bytes. Adding 10,000,000 bytes for metadata and logs gives a 10,428,800-byte planning estimate, below the 89,900,000-byte archive allowance and 100,000,000-byte shared pool cap. These are estimates, not measured production returns. Shared pool occupancy can still prevent a return.
'''
(O/'OPERATIONS_ROOM.md').write_text(ops)
# Record latest suite outcomes; keep the command ledger intact.
latest={}
for row in (O/'TESTS.txt').read_text().splitlines():
 match=re.match(r'(PASS|FAIL) (\S+) .*log=(\S+)',row)
 if match:latest[match[2]]=dict(status=match[1],log=match[3])
passed=failed=0;details=[]
for name,v in latest.items():
 text=(O/v['log']).read_text();n=re.search(r'Ran (\d+) tests?',text);n=int(n[1]) if n else 1
 if v['status']=='PASS':passed+=n
 else:
  errors=re.search(r'FAILED \((.*?)\)',text);count=sum(map(int,re.findall(r'=(\d+)',errors[1]))) if errors else n
  failed+=count;passed+=n-count
 details.append(f"| `{name}` | {v['status']} | {n} | `{v['log']}` |")
status=dict(passed_tests=passed,failed_tests=failed,suites=latest,unresolved=['Allocated Orchard CPU check on real staged dev-S1 frames has not run; submission requires its passing receipt.'])
(O/'TEST_SUMMARY.json').write_text(json.dumps(status,indent=2)+'\n')
refs=[('Room admission','src/h1eval/room134.py','def validate'),('Mixed frame binding','src/h1eval/room134.py','def bind'),('Manifest dispatch','src/h1eval/items.py',"if m['name']=='room134'"),('Frame-root extraction admission','src/orchard_h10/job.py','str(target) not in'),('Durable type binding','src/h1eval/h10/launch.py','types=args.types'),('One read and settings','tower_sequence.py','RULES='),('Allocated full-reader check','tower_sequence.py','def full_reader_rehearsal'),('CPU receipt validation','node_check.py','def validate_full_reader'),('Scoring and pairing','room_pair.py','def score_return')]
report=f'''Package `{token}` is resealed with an Orchard CPU check for both first items. **Local checks pass; submission requires the real Orchard CPU receipt.** No remote action or GPU run occurred.

The token stays unchanged because all 928 payload members and `0.tgz` remain byte-identical. Only operator files and their enclosing seals change. `OPERATOR_ONLY_AUDIT.json` records this comparison; `HASHES.json` records the final hashes.

| Implementation | File and line |
|---|---|
'''+''.join(f'| {label} | `out/{name}:{line(O/name,needle)}` |\n' for label,name,needle in refs)+f'''
The allocated helper stages authenticated archives and restores the export before rehearsing `room_scene0155_00` and `r0_015bd4aaf6870d79bade`. It uses W5's allocation recipe: `general`, eight CPUs, 200G, `04:00:00`, and no GPU.

Both items run through real launch, mixed native mapping, frame SHA256 verification and PNG decoding, capped ParityGenerator, CallHook, the decode loop and official scoring. Weights, model forward, tokenizer, prompt tensors, audit enforcement and decode budget use explicit CPU stubs.

The helper embeds both finished records in `a/c/CPU.json` under `full_reader.records` and sets `full_reader_passed=true`. It also writes `FULL_READER.json`. Any failure aborts the check. The bootstrap requires both pass flags and matching payload, plan, input and operator hashes.

The first dev-S1 item has distinct native-answer and evaluation-ground-truth labels. The check records both official scores without changing either label. Stub scores establish execution, not model quality.

| Evidence | Result |
|---|---|
| `LOCAL_CPU_CHECK.json` | Both records finish on an initially empty local root with the real R0 tar and synthetic dev-S1 PNGs. |
| `LOCAL_NATIVE_CPU_CHECK.json` | The same check finishes with native `d1/scene0155_00` frame paths. |
| `CPU_HELPER_TEST.json` | The helper enforces stage/restore/rehearsal order and writes both records; failures publish no passing receipt. |
| `W5_BINDING_EQUIVALENCE.json` | All 36 dev-S1 room bindings match W5. |
| `OPERATOR_ONLY_AUDIT.json` | All 928 payload members remain identical; the same token is valid. |

The local fixture uses the production extractor and admitted `d` and `d/f` destinations. It reads the authenticated R0 tar in place. The synthetic dev-S1 fixture preserves the native `d1/<scene>` key and tests both native paths and the pinned metadata's content-addressed PNG paths. Synthetic digests exist only in fixture settings; no digest verifier is bypassed.

Local preparation stubs unavailable export weights, artifact construction and runtime versions. The helper orchestration test also stubs the allocation, namespace and storage proof. These tests validate the check implementation; the allocated Orchard run must validate the actual archives, restore and namespace.

The W5 comparison runs each source tree in an isolated interpreter. Native tasks, resolved anchor/dense paths, pinned SHA256 values, indices, slots, mapping digests, effective types, settings and finished journal types match for all 36 rows. W6 explicitly persists the effective type list; W5's settings and journals establish the same selection.

The plan still contains one development-only room read: 36 dev-S1 and 98 R0-dev items, tower, mode none, null_argmax, G3T memo on, no verification IDs, and no own-depth output. The item-set digest is `{plan['item_set_sha256']}`. No fitting ran.

The payload retains the reader, scorer, step-544 export, frame binding and input descriptors. `PATCH.diff` compares source and operator files against W5. `PAYLOAD_AUDIT.json` records the payload's W5 comparison separately from the operator-only reseal audit.

Latest suite results: **{passed} passed, {failed} failed**. `TESTS.txt` preserves the execution ledger; this table reports each suite's latest result. Unchanged reader/memo suites retain their passing evidence.

| Gate | Latest result | Tests | Log |
|---|---|---:|---|
'''+ '\n'.join(details)+f'''

Production walltime remains `02:30:00`; the CPU check uses `04:00:00`. The read estimate is {price['read_seconds']:.1f} seconds. The return estimate is 10,428,800 bytes, below the 89.9 MB archive allowance and 100 MB pool cap. Production throughput, RSS and pool occupancy remain unmeasured.

`OPERATIONS_ROOM.md` gives exact placement, metadata-check, allocated CPU-check, pass-flag inspection, submit, fetch, unpack and scoring commands. It requires the passing Orchard receipt before submission.

All writes stayed inside W6. Tests used the supplied CPU Python with at most eight workers. No SSH, Git, network, submission, process kill or deletion ran. Rebuild the operator delivery with `out/build_operator.py` and `out/build_delivery.py`; verify it with `work/audit_operator_only.py` and `work/final_check.py`.

The report applies the no-archaeology and summary skills. The W5 comparison and reseal baseline remain because the requested equivalence and token checks require them.

| Artifact | Bytes | SHA256 |
|---|---:|---|
'''+''.join(f"| `{n}` | {v['bytes']} | `{v['sha256']}` |\n" for n,v in hashes.items())
(O/'REPORT.md').write_text(report)
(O/'REMOVAL_CANDIDATES.md').write_text('No files were deleted. W5 is read-only. After accepting the delivery and evidence, the user may review W6/work/tmp CPU fixtures, W6/work/frames rehearsal PNGs, out/reader_repin, out/package duplicate payload, and unused copied legacy test scripts. Preserve out/src, build scripts, TOKEN, BASE_INVENTORY.json, reports, logs, all test receipts, 0.tgz and 1.tgz for reproducibility. The source R0 tar is outside W6 and is not a removal candidate.\n')
size=sum(p.stat().st_size for p in W.rglob('*') if p.is_file());assert size<2500000000
(O/'WORKSPACE_SIZE.json').write_text(json.dumps(dict(bytes=size,cap_bytes=2500000000,source_tar_copied=False),indent=2)+'\n')
print(json.dumps(dict(token=token,bytes=size,passed=passed,failed=failed,payload=hashes['0.tgz']['sha256'],delivery=hashes['1.tgz']['sha256'])))
