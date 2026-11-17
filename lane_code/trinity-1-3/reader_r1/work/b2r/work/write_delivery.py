"""Write the reviewable package audit, operator runbook, and bounded size receipt."""
from pathlib import Path
import difflib,hashlib,json,re,tarfile
W=Path(__file__).resolve().parents[1];O=W/'out';P=O/'src';B=W.parent/'b1g/out'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def line(p,needle):return next(i for i,s in enumerate(p.read_text().splitlines(),1) if needle in s)
token=(O/'TOKEN').read_text().strip();price=json.loads((O/'TIME_PRICE.json').read_text());plan=json.loads((O/'READ_PLAN.json').read_text())
files=['0.tgz','1.tgz','PACKAGE.json','READ_PLAN.json','inputs_tower.json','export_544.json','tower_sequence.py','tower_bootstrap.py','node_check.py','room_pair.py','unpack_return.py','src/items/room134.json','src/inputs/room_captures.json']
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

The local dev-S1 full-reader rehearsal requires its pinned frame tar. `REPORT.md` records that gate's current status. Resolve that gate before submission. The real allocated CPU check and GPU run have not run in this lane.

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

Coordinate staging IO before this allocated CPU check. It requests eight CPUs and no GPU. The helper creates a fresh private root, authenticates archives, restores the export, checks one read's settings, verifies and decodes the first item’s frames from each set, and writes the CPU and memory receipts. Model decoding remains a separate GPU operation. The CPU allocation limit permits staging; it is not a timing estimate.

```bash
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" CUDA_VISIBLE_DEVICES= \\
  srun --account=mt01 --partition=general --nodes=1 --ntasks=1 \\
  --job-name=a15_cot_ap{token} --cpus-per-task=8 --mem=200G \\
  --time=02:30:00 --export=ALL \\
  /usr/bin/python3 -I -s -B "$P/a/5.py" --package "$P" \\
  --sequence "$P/a/6.py" --results "$P/a/c"
```

Submit only after the passing receipt exists. Record the shared return pool's current usage in the operator ledger; the production write test checks capacity before staging. Check the H100 resource type and pending priority jobs, then submit one GPU for 02:30:00.

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
status=dict(passed_tests=passed,failed_tests=failed,suites=latest,unresolved=['First dev-S1 full-reader CPU rehearsal lacks local pinned RGB frames.'] if not (O/'FULL_DEVS1.json').exists() else [])
(O/'TEST_SUMMARY.json').write_text(json.dumps(status,indent=2)+'\n')
refs=[('Room admission','src/h1eval/room134.py','def validate'),('Mixed frame binding','src/h1eval/room134.py','def bind'),('Manifest dispatch','src/h1eval/items.py',"if m['name']=='room134'"),('Frame-root extraction admission','src/orchard_h10/job.py','str(target) not in'),('Durable type binding','src/h1eval/h10/launch.py','types=args.types'),('One read and settings','tower_sequence.py','RULES='),('Allocated frame check','tower_sequence.py',"if config.get('measure_memory')"),('Scoring and pairing','room_pair.py','def score_return')]
report=f'''Package `{token}` contains one room-only tower read for 134 items. Its payload and delivery are sealed in `0.tgz` and `1.tgz`. The package is **not fully validated for submission**: the local first-dev-S1 full-reader rehearsal needs the pinned dev-S1 frame tar. The R0 full-reader rehearsal passes. No GPU run or remote action occurred.

| Implementation | File and line |
|---|---|
'''+''.join(f'| {label} | `out/{name}:{line(O/name,needle)}` |\n' for label,name,needle in refs)+f'''
The item manifest contains the exact 36 W5 dev-S1 room rows and 98 room rows from the supplied R0-dev qset. It preserves the questions verbatim, f32 indices, source FPS and frame totals, and records source line, qid, qset SHA256 and `gt.area_m2` label provenance. The ID sets and physical-room sets do not overlap across the two sources. The 36 dev-S1 captures span nine physical rooms; together the read spans 107 physical rooms. R0-dev and the combined manifest are development-only, with fitting forbidden. No fitting ran.

`item_set_sha256` is `{plan['item_set_sha256']}`. The plan digest is `{plan['plan_sha256']}`. `READ_PLAN.json` lists every key and the requested settings. Only `items/room134.json` appears under `items/` in the payload. The null selector slot and room's two-call cap remain unchanged.

The step-544 export descriptor, all artifact file pins, G3T weights/config, reader, heads, native tree, parity kit, official scorer and return implementation match W5 byte for byte. `PAYLOAD_AUDIT.json` records {len(same)} identical members and {len(protected)} protected identical members. `PATCH.diff` compares the sealed payload with W5/out/src and the operator files with W5/out. Configuration and item/frame adapters are the only runtime changes outside the operator.

The supplied R0 tar has SHA256 `2ad8c67c111d5f286aa96ea688efd5c88218e116a8c09ae1a9b4bc71be893a21` and 797,685,760 bytes. Its actual members use opaque 24-hex room/frame names, rather than the source layout `frames/scannetpp/<scene>/<frame>.png`. The producer's `evidence/ID_MAP.json` maps qset line and qid to `assets/e52a690b.jsonl`; `kit/launcher/EXTRA.json` supplies each member's digest. `FRAME_CHECK.json` proves all 3,136 requested PNGs exist, match those digests, and are 640×480. `R0_FRAME_PROVENANCE.json` pins the mapping sources; the identifier key was neither read nor copied. The source scene-manifest digests are retained as provenance; they are not incorrectly claimed to be members of this opaque tar.

Staging extracts the R0 archive directly under the existing frame root, adding 795,282,085 expanded bytes. All 3,136 tar members are needed by this room read. W5’s other archives and template groups remain: the restore contract requires all pinned dependencies, and the existing stage function extracts whole authenticated archives. The unchanged reader can construct SAM/selector components even for a direct room read. No unverified archive was dropped or rewritten. The 798 MB tar stays outside W6 and is read in place.

Room evaluation requires no external per-frame intrinsics or pose files. `src/b/e2e_reader/parity.py:35` builds the trainer input from RGB paths/digests, indices, timestamps, FPS, frame total and question. `src/tree/evalpath/runtime.py:126` uses the VQA prompt path; `src/tree/student_pilot/carrier_c1_data.py:416` builds camera targets only for the pose-training stream. Its frame loader reads PNGs. `src/b/e2e_reader/generate.py:30` constructs geometry lazily from in-memory predicted tensors if a call requests it. The direct R0 rehearsal forbids G3T invocation and reaches EOS without any camera-data input. Unexpected generated camera/ground calls could still invoke a tower; the zero-call timing estimate is an assumption from W5's room rows, not a hard reader restriction. The fixed memo memory bound admits up to 134 captures, below 200 GiB.

The timing proxy uses W5's measured room mean, 27.3328118579 seconds/item. Reads need {price['read_seconds']:.3f} seconds. Staging/loading retains W5's 1,800-second allowance and adds 120 seconds for the new archive. The overlapping stop/return margins require {price['required_seconds']:.3f} seconds in total. Of 02:00:00, 02:30:00 and 03:00:00, **02:30:00** is the smallest fitting walltime. It leaves {price['stop_deadline_slack_seconds']:.3f} seconds before stop admission under the proxy. Production throughput, RSS and staging time remain unmeasured. Price is 2.5 times the H100 hourly rate plus the CPU check; rates were not supplied.

The 134 replay rows imply 2,492,400 raw bytes and 428,800 compressed bytes. The archive estimate adds a 10 MB metadata/log allowance, totaling **10,428,800 bytes**. This leaves 79,471,200 bytes against the conservative 89.9 MB archive allowance and 89,571,200 bytes against an empty 100 MB pool. The production limiter actually caps compressed archives at 89,999,999 bytes. The shared pool's occupancy remains an operator check.

| Gate | Latest result | Tests | Log |
|---|---|---:|---|
'''+ '\n'.join(details)+f'''

Latest tests: **{passed} passed, {failed} failed**. `TESTS.txt` retains the command ledger, including failed setup assertions and their follow-up checks. `FRAME_CHECK.json` also records the full archive/member verification performed by `work/build_items.py`.

`FULL_R0.json` contains the finished R0 record from real launch, mixed native mapping, frame SHA256 checks and PIL decoding, capped ParityGenerator, generate_real, CallHook, decode loop and official scoring. Artifact audit, weights/model forward, tokenizer and prompt tensor construction are explicit CPU stubs. The first dev-S1 attempt stops at a missing pinned PNG before generation; no substitute image or hash bypass was used. `MEMO_BINDING.json` exercises real empty-root prepare and launch with restore, manifest creation and runtime-version stubs. `LOCAL_REHEARSAL.json` covers extraction, every payload pin, step-544 admission, one read and null-slot wiring. `RETURN_MEMBERS.json`, `STOP_PROOF.json` and `RETURN_CLI.json` cover journal return, draining, partial persistence and authenticated unpack. `SCORING_TEST.json` proves the synthetic 36/98/134 pairing, MRA, cap/malformed counts and refusal checks.

`room_pair.py` recomputes MRA from ground_truth using the unchanged official scorer and the parity think-close/strict-no-answer rule; it does not trust serialized native-answer scores. Malformed-call counts describe recorded diagnostics containing “malformed”; an unserved call without a diagnostic is not classified as malformed. Scores from missing items remain absent and each set reports completion separately.

All writes stayed in W6. CPU tests used the supplied Python with one thread per numerical library; no agent, SSH, Git, network, submission, process kill or deletion ran. Rebuild with `out/build_package.py`, `out/build_operator.py`, and `out/build_delivery.py`. `REMOVAL_CANDIDATES.md` records optional cleanup for the user. The report uses the no-archaeology and summary skills; the requested W5 comparison is retained because it establishes code identity.

| Artifact | Bytes | SHA256 |
|---|---:|---|
'''+''.join(f"| `{n}` | {v['bytes']} | `{v['sha256']}` |\n" for n,v in hashes.items())+'\n'+ops
(O/'REPORT.md').write_text(report)
(O/'REMOVAL_CANDIDATES.md').write_text('No files were deleted. W5 is read-only. After accepting the delivery and evidence, the user may review W6/work/tmp CPU fixtures, W6/work/frames rehearsal PNGs, out/reader_repin, out/package duplicate payload, and unused copied legacy test scripts. Preserve out/src, build scripts, TOKEN, BASE_INVENTORY.json, reports, logs, all test receipts, 0.tgz and 1.tgz for reproducibility. The source R0 tar is outside W6 and is not a removal candidate.\n')
size=sum(p.stat().st_size for p in W.rglob('*') if p.is_file());assert size<2500000000
(O/'WORKSPACE_SIZE.json').write_text(json.dumps(dict(bytes=size,cap_bytes=2500000000,source_tar_copied=False),indent=2)+'\n')
print(json.dumps(dict(token=token,bytes=size,passed=passed,failed=failed,payload=hashes['0.tgz']['sha256'],delivery=hashes['1.tgz']['sha256'])))
