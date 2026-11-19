from pathlib import Path
import hashlib,json,difflib
R=Path(__file__).resolve().parent;W=R.parent
# Operator-only guards; both delivery archive bytes remain unchanged.
for label in ('A','B'):
 p=R/label/'o_place.sh';s=p.read_text();s=s.replace('case "$D" in /project/community/jjyeung/okh7/a15_cot_ap*) ;; *) exit 1;; esac', '[[ "$D" =~ ^/project/community/jjyeung/okh7/a15_cot_ap[0-9a-f]+$ ]]')
 p.write_text(s)
p=R/'A/o_pullfill.sh';s=p.read_text();needle="assert len(f)==3 and f[0]==b['object'] and f[1].isdigit() and int(f[1])>0 and re.fullmatch('[0-9a-f]{64}',f[2])"
s=s.replace(needle,needle+"\nassert int(f[1])==21583032320 and f[2].startswith('795ef9ef'), 'Completion receipt differs from the R2 handoff'")
p.write_text(s)
# Keep copied evidence visibly separate from results obtained during this rebuild.
keep={'PACKAGE.json','READ_PLAN.json','TOKEN','0.tgz','1.tgz','PATCH.diff','TIME_PRICE.json','PAYLOAD_CHANGES.json','PY36_GUARD.json','RETURN_CLI.json','score_r1route.py','test_score_r1route.py','fill_export.py','tower_sequence.py','tower_bootstrap.py','node_check.py','tower_pair.py','room_pair.py','b1_report.py','gap.py','unpack_return.py','OPERATIONS_R1ROUTE.md','REPORT.md','TESTS.txt'}
for label,k in [('A','b1'),('B','b2')]:
 d=R/label;history=d/'surviving_records';history.mkdir(exist_ok=True)
 for p in list(d.iterdir()):
  if p.is_file() and p.name not in keep and not p.name.startswith('o_') and p.name not in ('R2_OPERATOR_DIFF.patch','R2_FILE_SHA256_DIFF.json'):
   p.rename(history/p.name)
 patch=[];changes=[]
 for name in ('o_place.sh','o_pullfill.sh','o_cpucheck.sh','o_sub.sh','o_fetch.sh','score_r1route.py'):
  old=(W/'out'/k/name) if (W/'out'/k/name).exists() else W/'out'/name
  a=old.read_bytes();b=(d/name).read_bytes()
  changes.append(dict(file=name,original_sha256=hashlib.sha256(a).hexdigest(),delivered_sha256=hashlib.sha256(b).hexdigest(),identical=a==b))
  if a!=b:patch.extend(difflib.unified_diff(a.decode().splitlines(True),b.decode().splitlines(True),fromfile='surviving/'+name,tofile='out2/'+label+'/'+name))
 (d/'R2_OPERATOR_DIFF.patch').write_text(''.join(patch));(d/'R2_FILE_SHA256_DIFF.json').write_text(json.dumps(changes,indent=2)+'\n')
 remote='/project/community/jjyeung/okh7/a15_cot_ap'+(d/'TOKEN').read_text().strip()
 wall='05:00:00' if label=='A' else '02:30:00'
 doc=f'''# R1 step-200 operator commands: package {label}

Package: `{remote}`. Delivery: a separate `/project/community/jjyeung/okh7/a15_cot_ap<hex>` directory created by the operator. Place only this package's `1.tgz` in that delivery directory. The delivery directory must differ from both package directories. No remote action ran during this rebuild.

The operator can create a delivery directory on the Orchard login node with:

```bash
D=/project/community/jjyeung/okh7/a15_cot_ap$(/usr/bin/python3 -I -s -B -c 'import os; print(os.urandom(8).hex())')
mkdir -m 700 "$D"
printf '%s\\n' "$D"
```

Transfer `1.tgz` there through the lane's authorized transfer procedure. In the following local commands, set `D` to that exact remote directory and use the lane's existing `ossh.sh` path:

```bash
cd {d}
D=/project/community/jjyeung/okh7/a15_cot_ap<hex>
{{ printf 'D=%q\\n' "$D"; cat o_place.sh; }} | bash ossh.sh 'bash -s'
```

Place **both A and B** before filling either. Run A's fill first; B must wait until A finishes successfully. A downloads the four parts sequentially once. B reads the same files under A's `a/e/` directory and checks them again. Retain A's files through both jobs.

```bash
bash ossh.sh 'bash -s' < o_pullfill.sh
```

The fill starts under `nohup`. Check its completion with this read-only command, at most once per minute:

```bash
bash ossh.sh 'test "$(cat {remote}/a/1.txt)" = 0'
```

On failure, inspect `{remote}/a/0.log`; there is no retry loop. A requires the handoff's `.done` object, 21,583,032,320 bytes, and SHA256 prefix `795ef9ef`. The fill computes and compares the entire SHA256 against `.done`. The full handoff SHA and `.done` bytes were not supplied locally.

The fill requires the exact config (`3b0051c4…`), S1 receipt (`4c0dd9d6…`) and data receipt (`7f654d2f…`). The physical receipt is `x_69d2930d/runs/673bc60f/inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0/prepared/s1_receipt.json` beneath `/project/community/jjyeung/okh7`. Its internal logical path remains unchanged. The exact data receipt is absent from the rebuild workspace; fixture receipts cannot pass the delivered package's fill.

After fill completes, submit the allocated CPU check:

```bash
bash ossh.sh 'bash -s' < o_cpucheck.sh
```

Wait for the CPU job to complete successfully. Then submit this package's GPU job:

```bash
bash ossh.sh 'bash -s' < o_sub.sh
```

The script requires the exact CPU receipt, an empty `jjyeung` general queue, and a return pool of at most 75,000,000 bytes. It requests one GPU for `{wall}` and records the job ID in `a/8.txt`. Run the A and B GPU jobs sequentially. Fixture receipts do not authorize submission.

After the GPU job finishes:

```bash
bash ossh.sh 'bash -s' < o_fetch.sh
```

Transfer `{remote}/a/f/0.tgz` and `EXIT.json` into `{d}/f/` through the lane's authorized transfer procedure. Unpack locally:

```bash
cd {d}
/scratch/jjyeung/envs/p1cpu/bin/python -B unpack_return.py --archive f/0.tgz --exit f/EXIT.json --out {d}/ret
```

Scoring requires the authentic job-171253 and job-172456 returns, which are missing here. Restore them under `{R}/bases/b1/work/ret` and `{R}/bases/b2/work/ret`, plus the authentic job-172456 `scores.json` under `{R}/bases/b2/work/scores`. The base payloads, plans, and operator bytes are already reconstructed there. Do not use the synthetic fixtures under `gates/` or `test_tmp/` as baseline returns.

```bash
cd {R}
OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 /scratch/jjyeung/envs/p1cpu/bin/python -B score_r1route.py --baseline-root bases --self-test --out baseline_check
OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 /scratch/jjyeung/envs/p1cpu/bin/python -B score_r1route.py --baseline-root bases --a A/ret --b B/ret --out scores
```

The scorer uses job 171253 read 0 for camera and dev-S1 room, read 1 for distance, and job 172456 read 0 for both room sets. It preserves the 450-camera and 107-non-metre populations, 10,000 physical-room bootstrap draws, both confidence intervals, and room `mra_answer`. Partial results cannot certify H3. Review `../REPORT.md` and `R2_OPERATOR_DIFF.patch` before remote execution.
'''
 (d/'OPERATIONS_R1ROUTE.md').write_text(doc)
print('Delivery scripts and operator instructions finalized')
