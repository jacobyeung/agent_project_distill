# Operator commands

Run Trinity commands from `/scratch/jjyeung/orch_n30/evalx27/work`. The builder has not submitted a job or contacted Orchard. All local output goes under `kit_revsi/`. The operator must authorize heavy media IO and register the single archive upload before running it. Do not upload during other `/data*` reads.

```bash
export PYTHONDONTWRITEBYTECODE=1
PY="$PWD/kit_revsi/.venv312/bin/python"
LAUNCHER="$PWD/kit_revsi/launcher/orchard_launcher.py"
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
POOL=/project/community/jjyeung/okh7/x27ret
MEDIA_HEX=$(python3 -c 'import secrets;print(secrets.token_hex(8))')
MEDIA=/project/community/jjyeung/okh7/$MEDIA_HEX
ARCHIVE="$PWD/kit_revsi/media/$MEDIA_HEX.tar"
"$PY" kit_revsi/media/make_archive.py --output "$ARCHIVE" > "$ARCHIVE.receipt.json"
```

`NEED_261.json` names exactly 261 tier-32 files (318,248,080 source bytes). The builder read no MP4 from `/data2`. The source list explicitly pins 189 needed files; 72 source paths use the user-supplied tier-32 directory and remain unverified until this command succeeds. The archive builder reads each source once, verifies size/SHA256 while streaming, limits reads to 8 MB/s, and hashes the tar as it writes. A failed build leaves a partial archive and no successful receipt; do not upload it or retry a killed transfer without the operator's approval.

Print the exact governed upload command; register that command with the operator's transfer governor, then execute it once. The archive path on Orchard is neutral. This uploads one archive, never a media folder.

```bash
"$PY" - "$OSSH" "$ARCHIVE" "$MEDIA" <<'PY'
import shlex,sys
ossh,archive,media=sys.argv[1:]
remote='set -e; test ! -e '+shlex.quote(media+'.tar')+'; umask 077; set -C; cat > '+shlex.quote(media+'.tar')
print('pv -q -L 8m '+shlex.quote(archive)+' | timeout 300 bash '+shlex.quote(ossh)+' '+shlex.quote(remote))
PY
# After governor registration, execute the printed command once with: set -o pipefail
SHA=$("$PY" -c 'import json,sys;print(json.load(open(sys.argv[1]))["sha256"])' "$ARCHIVE.receipt.json")
timeout 300 bash "$OSSH" "set -e; printf '%s  %s\n' '$SHA' '$MEDIA.tar' | sha256sum -c -; mkdir '$MEDIA'; tar -xf '$MEDIA.tar' -C '$MEDIA'"
```

Verify the extracted root with the stdlib checker. This sends only checker code and the small manifest through stdin; it creates no named helper files on Orchard.

```bash
"$PY" - "$MEDIA" <<'PY' | timeout 300 bash "$OSSH" 'python3 -I -s -B -'
from pathlib import Path
import base64,json,sys
code=Path('kit_revsi/media/check_on_orchard.py').read_text()
raw=Path('kit_revsi/media/NEED_261.json').read_bytes()
print("import base64,json; ns={'__name__':'checker'}; exec("+repr(code)+",ns)")
print("ns['manifest']=lambda unused: json.loads(base64.b64decode("+repr(base64.b64encode(raw).decode())+"))")
print("print(json.dumps(ns['check']("+repr(sys.argv[1])+",None)))")
PY
```

Prepare the proof. `--skip-phase-b` disables only the dev-S1 real-engine phase; omit it when that phase is wanted. Phase A still uses real staging, all 261 media hashes, all 261 decoded frame plans, real processor prompt parity, and exactly two items per category through the fake engine. The 10 proof IDs reach every evaluator caller through the same loader filter. Production uses all 679 IDs. Both modes ship identical payload code.

```bash
TOKEN=$(python3 -c 'import secrets;print("p"+secrets.token_hex(5))')
DEST="$PWD/kit_revsi/build/$TOKEN"
"$PY" "$LAUNCHER" prepare --mode proof --media-root "$MEDIA" --skip-phase-b --pool "$POOL" --token "$TOKEN" --destination "$DEST"
SUBMIT_COMMAND=$("$PY" "$LAUNCHER" submit-command --destination "$DEST")
printf '%s\n' "$SUBMIT_COMMAND"
timeout 300 bash "$OSSH" "$SUBMIT_COMMAND" < "$DEST/BATCH.sh" > "$DEST/SUBMIT.out" 2> "$DEST/SUBMIT.err"
"$PY" "$LAUNCHER" record-submission --destination "$DEST"
JOB=$("$PY" -c 'import json,sys;print(json.load(open(sys.argv[1]))["job"])' "$DEST/SUBMISSION.json")
timeout 300 bash "$OSSH" "TZ=UTC sacct -j $JOB --format=JobID,JobName,State,ExitCode,Elapsed,Start,End -P"
# Poll at most once per minute. After completion:
"$PY" "$LAUNCHER" fetch --destination "$DEST"
```

Production uses the same commands with a fresh token and `--mode production`; omit `--skip-phase-b`. Production requests one H100, general, 16 CPUs, 200G, six hours. Proof requests the same resources for two hours. Pool/GCS publication, write-test deadlines, caps and fetch governance remain the VSI launcher's code. The pool is `/project/community/jjyeung/okh7/x27ret`; GCS is `gs://cmu-gpucloud-jjyeung/q8/x27r/<token>/`. Fetch prints a governed command and stops before archive transfers of 20 MB or more. The operator registers and runs that command once.

```bash
"$PY" - "$DEST" <<'PY'
import json,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]);out=p/'packet';out.mkdir()
with tarfile.open(p/'fetched/result.tar.gz') as archive:archive.extractall(out,filter='data')
assert json.loads((p/'fetched/EXIT.json').read_text())['status']=='COMPLETE'
print((out/'COMPLETE.json').read_text())
print((out/'report/SUMMARY.txt').read_text())
PY
"$PY" kit_revsi/proof/lines_report.py "$DEST/fetched/TRACE.json.gz" --json "$DEST/LINES.json" > "$DEST/LINES.txt"
```

After production returns, supply the parent's merged `budget_2048/0/items_*.jsonl` to compute paired scene intervals. The parent may contain all 999 IDs; the scorer requires all 679 selected IDs, rejects duplicates and conflicting task metadata, and ignores excluded categories. It records the parent file's SHA256. Parent answers are unavailable in this workspace, so no real parent comparison or reproduction of its reported seven-category result is claimed.

```bash
"$PY" kit_revsi/reader/official_score.py --dest "$DEST/packet/a0" --output "$DEST/rescored" --parent-answers /path/to/parent/items.jsonl
```

The scorer uses native per-item scores, equal subtype means within each category, and the equal mean of the five categories. It reports B2048 first, ON16k and B4096 second, plus direction toward/away determined only from question text. All intervals use 10,000 scene-cluster draws and seed 544; paired draws use identical scene weights for both models. Undefined replicates are omitted only from the affected interval, with their valid count reported. Failed/missing answers score zero and remain in denominators. Proof uses present subtypes and is explicitly synthetic; it is not a performance estimate. Absolute distance and room size are marked “not read here: native reader required.” Native intermediate merge summaries retain their unchanged schema; the reader-facing report is `report/SUMMARY.txt` and the three arm JSON files.
