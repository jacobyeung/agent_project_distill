Package `b9ef552934627` requires `entry_sequence_passed=true` before GPU launch. The CPU check installs the process guard, stages its inputs, extracts the actual BATCH.sh bundle, and calls the production `orchard_results.write_test` against `root/wpool`. It verifies the retained 4 MiB file and confirms that the guard wrote `root/6.py` while `root/7.py` kept its sealed hash.

The CPU helper imports `make_dispatch` from the extracted `root/0.py`. It passes an action-1 config with `device=cpu`, `measure_memory=True`, and `rehearsal=True`, using argv ending in `root/a/5.py root/a/1.json`. The bootstrap rewrites the operator path to `root/7.py` and re-hashes it immediately before launching. The unchanged operator already accepts this config. Production admission, argv rewriting and dispatch checks retain their behavior; admission additionally requires the entry-sequence flag.

CPU.json binds the write-test bytes and SHA256, the guard-target SHA256, the operator SHA256 before and after execution, and both requested and dispatched argv. The operator subprocess produces MEMORY.json. The room operator also produces the dev-S1 and R0-dev full-reader records with explicit model stubs. Any failed entry step prevents a passing receipt.

The final suites passed 49 tests with zero failures, errors or skips. Both local entry proofs execute the real guarded write test, bundled bootstrap wrapper and operator subprocess. Allocation, namespace, storage, staging, restore and local path/Python adaptation remain fixtures. The local proof does not establish Orchard staging or real model quality. LOCAL_ENTRY_CHECK.json and LOCAL_REHEARSAL.json identify the executed roots and receipts. The documented pass check accepts these receipts and rejects nine corruptions; TESTS.txt lists exact suite commands.

The token, every 0.tgz payload byte, operator bytes, input descriptors, read settings, item lists, walltimes and margins are unchanged from the W7 baseline in FOLLOWUP_BASE.json. The bootstrap, CPU helper, embedded bundle, package manifest and delivery are resealed. FILE_SHA256_DIFF.tsv lists changed file hashes against that baseline. This explicit baseline comparison is retained because the requested seal audit requires it.

Orchard's allocated CPU check and GPU evaluation remain pending. The local pool test does not test the shared return pool's capacity. Staging availability, shared-pool capacity and b1's five-hour partial-run estimate remain external risks. The operator re-hash does not eliminate the interval between checking a path and the child opening it. No SSH, Git, network, job submission, GPU execution or process termination ran here.

The authoritative outputs are 0.tgz, 1.tgz, PACKAGE.json, READ_PLAN.json, TESTS.txt, FINAL_VERIFICATION.json, LOCAL_ENTRY_CHECK.json and OPERATIONS_TOWER.md. The `sub2` script duplicates the full CPU pass check in `commands_2.sh`. These command scripts are operator instructions; they were parsed locally, not submitted.

`0.tgz` SHA256: `8be887e33af2b39b30e8304c5131ec576d434b22575c9837649605569bbf9cbd`
`1.tgz` SHA256: `57d2a513b6770447680fc088a39fd02c00945491bdde46309e9ade0c84540f3e`
`PACKAGE.json` SHA256: `18e81733a93dd41f750eca3cd2eb042806c970252a900a9a5b1ec0f616fef211`
`READ_PLAN.json` SHA256: `83e335fb1d6c3b124537bde345f91575810738d066f2fe1a74abadf7a80338e8`

Operator SHA256: `0cec6e0e91b8c7dab6d74e68bbca8e6a596e5df76e7f0e9166aec2231ecb3f38`

Package `b9ef552934627` runs read 1 first, followed by read 0 in a separate process. Both list only `g3t` in `perception_memo_modules`. Read 1 uses `candidates_argmax`, distance only, and `verify` on its explicit first 30 distance IDs. Read 0 uses `null_argmax` and memo `on`, with distance, displacement, rotation, movement direction, then room. `READ_PLAN.json` contains the exact IDs. Each read keeps separate settings, identity, journals, and call caps.

The full-plan proxy estimate is 5.167 hours including 30 minutes for staging/loading and a 30-minute stop margin. The 20-minute return margin lies inside that stop margin. Under a five-hour allocation, the expected cut is in room after all 750 distance/camera items and about 14 room items. SAM encodes freshly whenever a read requests it; encode time is unmeasured and no SAM savings are credited. The expected room cut has 381.279 seconds of pre-room slack; unmeasured overhead can move it earlier.

Place the delivery from an existing opaque directory and check metadata. Set `D` to that directory. These commands require the operator to run them on Orchard.

```bash
set -euo pipefail
umask 077
: "${D:?Set D to the existing opaque delivery directory}"
P=/project/community/jjyeung/b9ef552934627
printf '%s  %s\n' 57d2a513b6770447680fc088a39fd02c00945491bdde46309e9ade0c84540f3e "$D/1.tgz" | sha256sum -c -
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00
```

Coordinate staging IO before the allocated CPU check. This requests eight CPUs, 200G, four hours, no GPU, the preempt partition, and excludes orchard-flame-[0-31]. The helper creates a fresh private root, authenticates staging and restore, and runs the real 4 MiB return-pool write test through the process guard under its private `root/wpool`. It then sends the action-1 CPU rehearsal through the embedded bootstrap wrapper, which rewrites `a/5.py` to `7.py` and re-hashes the operator immediately before dispatch. The receipt must bind the write test, guard target, unchanged operator and dispatched argv, with `entry_sequence_passed=true` and `bundle_guard_passed=true`. A failed check must not proceed to GPU submission.

The CPU sequence checks selector wiring and the fixed G3T memory bound; it does not perform a real evaluation decode.

```bash
CPU_REPLY=$(env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" CUDA_VISIBLE_DEVICES= \
  sbatch --parsable --account=mt01 --partition=preempt --nodes=1 --ntasks=1 \
  --job-name=a15_cot_apb9ef552934627 --cpus-per-task=8 --mem=200G \
  --time=04:00:00 --exclude='orchard-flame-[0-31]' --export=ALL --no-requeue \
  --chdir=/tmp --output="$P/a/4.log" --error="$P/a/4.err" \
  --wrap="exec /usr/bin/python3 -I -s -B $P/a/5.py --package $P --sequence $P/a/6.py --results $P/a/c")
CPU_JOB=${CPU_REPLY%%;*}
[[ "$CPU_JOB" =~ ^[0-9]+$ ]]
printf '%s\n' "$CPU_JOB" > "$P/a/4.txt"
```

Wait for the recorded CPU job to exit successfully. Then run this pass check (also saved as `sub2` and `commands_2.sh`); missing or mismatched evidence stops the workflow.

```bash
/usr/bin/python3 -I -s -B - "$P" <<'PYCODE'
import hashlib,json,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]);c=json.loads((p/'a/c/CPU.json').read_text());v=json.loads((p/'0.json').read_text())
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert c['passed'] is True and c['bundle_guard_passed'] is True and c['entry_sequence_passed'] is True
assert c['payload']==v['payload_sha256'] and c['plan']==v['plan_sha256']
assert c['operator_sha256']==sha(p/'a/6.py') and c['inputs']==sha(p/'a/1.json')
g=c['bundle_guard']
assert g['passed'] is True and g['path']=='7.py' and g['guard_target']=='6.py' and g['action']=='test'
assert g['operator_sha256']==sha(p/'a/6.py') and g['batch_sha256']==sha(p/'BATCH.sh')
e=c['entry_sequence'];root=Path(c['root'])
assert e['passed'] is True and e['entry_sequence_passed'] is True
assert e['events']==['guard_installed','write_test','operator_dispatch']
assert e['operator_sha256_before']==e['operator_sha256_after']==c['operator_sha256']
assert e['path']=='7.py' and e['guard_target']=='6.py' and e['action']=='test'
assert e['operator_sha256']==c['operator_sha256'] and e['batch_sha256']==sha(p/'BATCH.sh')
assert e['pool']==str(root/'wpool') and e['token']==v['token']
w=e['write_test']
assert type(w['bytes']) is int and w['bytes']==4*1024**2
assert isinstance(w['sha256'],str) and len(w['sha256'])==64 and all(ch in '0123456789abcdef' for ch in w['sha256'])
with tarfile.open(p/'0.tgz') as archive:
    guard_sha=hashlib.sha256(archive.extractfile('orchard_h10/vendor/return_io.py').read()).hexdigest()
assert e['guard_target_sha256']==guard_sha
assert {k:v for k,v in e.items() if k!='entry_sequence_passed'}==g
assert e['requested_argv'][-2:]==[str(root/'a/5.py'),str(root/'a/1.json')]
assert e['dispatched_argv']==e['requested_argv'][:-2]+[str(root/'7.py'),str(root/'a/1.json')]
m=c['memory']
assert m==json.loads((p/'a/c/MEMORY.json').read_text())
assert m['fits'] is True and m['basis']=='fixed_g3t_shapes'
assert m['perception_memo_modules']==['g3t'] and m['sam_measurement_required'] is False
print('All CPU receipt checks passed')
PYCODE
```

After the CPU check passes, use the existing review requirements and accept the documented partial-run estimate before submitting. Record the shared return pool's usage; the production write test checks its capacity before staging. The following commands check resource types and pending priority jobs, then submit one GPU for five hours.

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

Fetch after the return is published. The transport may mark a clean partial return as failed because the full plan did not finish; inspect its summaries.

```bash
JOB=$(<"$P/a/8.txt")
RET=$(/usr/bin/python3 -I -s -B - "$JOB" <<'PYCODE'
import sys
print('b9ef552934627'+format(int(sys.argv[1]),'08x'))
PYCODE
)
/usr/bin/python3 -I -s -B 3.py fetch --return-token "$RET" --out "$P/a/f"
```

Transfer the bounded `a/f/0.tgz` and `a/f/EXIT.json` through the authorized operator channel into `/scratch/jjyeung/orch_n30/reader_r1/work/fix7/b1/work/f/`. No transfer ran here. Unpack and score locally:

```bash
cd /scratch/jjyeung/orch_n30/reader_r1/work/fix7/b1
/scratch/jjyeung/envs/p1cpu/bin/python -B unpack_return.py \
  --archive work/f/0.tgz --exit work/f/EXIT.json --out work/ret
/scratch/jjyeung/envs/p1cpu/bin/python -B tower_pair.py \
  --package src \
  --own /scratch/jjyeung/orch_n30/reader_r1/work/b1p/in/h10own/170631/items.jsonl /scratch/jjyeung/orch_n30/reader_r1/work/b1p/in/h10own/170706/items.jsonl /scratch/jjyeung/orch_n30/reader_r1/work/b1p/in/h10own/170694/items.jsonl \
  --tower-null work/ret/metadata/reads/0 \
  --tower-candidates work/ret/metadata/reads/1 \
  --out work/scores
```

Unpacking rejects a missing journal or environment for a started segment. Pairing rejects missing journals, mixed rules, mismatched module bindings and changed code hashes. Partial camera journals cannot establish the complete camera comparison. Candidate-rule comparisons remain in-sample. No cross-rule journal merge is permitted.

The sealed delivery is `1.tgz`; its receipt is `PACKAGE.json`. `READ_PLAN.json` records the read settings and commands. `FILE_SHA256_DIFF.tsv` lists every changed sealed member and build source against the source package. Local fixture receipts do not authorize Orchard submission. No Orchard CPU check, network transfer, or GPU job ran during this repair.

W7 currently exceeds the 450 MB cap: retained fixtures occupy about 703 MB of allocated file blocks (680 MB of logical data). HARDLINK_PLAN.json identifies byte-identical fixture copies whose consolidation would preserve every path and byte. Applying that plan awaits an explicit exception to the AGENTS.md no-deletion rule. No fixture copy has been removed or replaced.
