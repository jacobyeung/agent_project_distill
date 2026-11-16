Comparison base: `ea1a1b2d5b965017f7cacce9c02c13cbbe5522d87be8cc55ab755176ecd55d3b` (`package.tar`, 125 regular members).

Scope: kit source members, new analysis/test/build tools, reports, and the local ledger. Generated evidence and DIFF.md itself are BEYOND artifacts, not recursive diff inputs. Every added or removed line below has one classification. PATH/ENV covers checkpoint paths, step binding, names, transport, and diagnostic encoding. BEYOND covers deadlines, retaining write-test evidence, analysis, documentation, and offline validation. Unchanged lines appear only as diff context.

### kit/PROOF_JOB.md — BEYOND

```diff
--- ea1a1b2d/PROOF_JOB.md
+++ kit/PROOF_JOB.md
@@ -1,84 +1 @@
[BEYOND] -# Operator commands
[BEYOND] -
[BEYOND] -Run Trinity commands from `/scratch/jjyeung/orch_n30/evalx27/work`. The builder has not submitted a job or contacted Orchard. All local output goes under `kit_revsi/`. The operator must authorize heavy media IO and register the single archive upload before running it. Do not upload during other `/data*` reads.
[BEYOND] -
[BEYOND] -```bash
[BEYOND] -export PYTHONDONTWRITEBYTECODE=1
[BEYOND] -PY="$PWD/kit_revsi/.venv312/bin/python"
[BEYOND] -LAUNCHER="$PWD/kit_revsi/launcher/orchard_launcher.py"
[BEYOND] -OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
[BEYOND] -POOL=/project/community/jjyeung/okh7/x27ret
[BEYOND] -MEDIA_HEX=$(python3 -c 'import secrets;print(secrets.token_hex(8))')
[BEYOND] -MEDIA=/project/community/jjyeung/okh7/$MEDIA_HEX
[BEYOND] -ARCHIVE="$PWD/kit_revsi/media/$MEDIA_HEX.tar"
[BEYOND] -"$PY" kit_revsi/media/make_archive.py --output "$ARCHIVE" > "$ARCHIVE.receipt.json"
[BEYOND] -```
[BEYOND] -
[BEYOND] -`NEED_261.json` names exactly 261 tier-32 files (318,248,080 source bytes). The builder read no MP4 from `/data2`. The source list explicitly pins 189 needed files; 72 source paths use the user-supplied tier-32 directory and remain unverified until this command succeeds. The archive builder reads each source once, verifies size/SHA256 while streaming, limits reads to 8 MB/s, and hashes the tar as it writes. A failed build leaves a partial archive and no successful receipt; do not upload it or retry a killed transfer without the operator's approval.
[BEYOND] -
[BEYOND] -Print the exact governed upload command; register that command with the operator's transfer governor, then execute it once. The archive path on Orchard is neutral. This uploads one archive, never a media folder.
[BEYOND] -
[BEYOND] -```bash
[BEYOND] -"$PY" - "$OSSH" "$ARCHIVE" "$MEDIA" <<'PY'
[BEYOND] -import shlex,sys
[BEYOND] -ossh,archive,media=sys.argv[1:]
[BEYOND] -remote='set -e; test ! -e '+shlex.quote(media+'.tar')+'; umask 077; set -C; cat > '+shlex.quote(media+'.tar')
[BEYOND] -print('pv -q -L 8m '+shlex.quote(archive)+' | timeout 300 bash '+shlex.quote(ossh)+' '+shlex.quote(remote))
[BEYOND] -PY
[BEYOND] -# After governor registration, execute the printed command once with: set -o pipefail
[BEYOND] -SHA=$("$PY" -c 'import json,sys;print(json.load(open(sys.argv[1]))["sha256"])' "$ARCHIVE.receipt.json")
[BEYOND] -timeout 300 bash "$OSSH" "set -e; printf '%s  %s\n' '$SHA' '$MEDIA.tar' | sha256sum -c -; mkdir '$MEDIA'; tar -xf '$MEDIA.tar' -C '$MEDIA'"
[BEYOND] -```
[BEYOND] -
[BEYOND] -Verify the extracted root with the stdlib checker. This sends only checker code and the small manifest through stdin; it creates no named helper files on Orchard.
[BEYOND] -
[BEYOND] -```bash
[BEYOND] -"$PY" - "$MEDIA" <<'PY' | timeout 300 bash "$OSSH" 'python3 -I -s -B -'
[BEYOND] -from pathlib import Path
[BEYOND] -import base64,json,sys
[BEYOND] -code=Path('kit_revsi/media/check_on_orchard.py').read_text()
[BEYOND] -raw=Path('kit_revsi/media/NEED_261.json').read_bytes()
[BEYOND] -print("import base64,json; ns={'__name__':'checker'}; exec("+repr(code)+",ns)")
[BEYOND] -print("ns['manifest']=lambda unused: json.loads(base64.b64decode("+repr(base64.b64encode(raw).decode())+"))")
[BEYOND] -print("print(json.dumps(ns['check']("+repr(sys.argv[1])+",None)))")
[BEYOND] -PY
[BEYOND] -```
[BEYOND] -
[BEYOND] -Prepare the proof. `--skip-phase-b` disables only the dev-S1 real-engine phase; omit it when that phase is wanted. Phase A still uses real staging, all 261 media hashes, all 261 decoded frame plans, real processor prompt parity, and exactly two items per category through the fake engine. The 10 proof IDs reach every evaluator caller through the same loader filter. Production uses all 679 IDs. Both modes ship identical payload code.
[BEYOND] -
[BEYOND] -```bash
[BEYOND] -TOKEN=$(python3 -c 'import secrets;print("p"+secrets.token_hex(5))')
[BEYOND] -DEST="$PWD/kit_revsi/build/$TOKEN"
[BEYOND] -"$PY" "$LAUNCHER" prepare --mode proof --media-root "$MEDIA" --skip-phase-b --pool "$POOL" --token "$TOKEN" --destination "$DEST"
[BEYOND] -SUBMIT_COMMAND=$("$PY" "$LAUNCHER" submit-command --destination "$DEST")
[BEYOND] -printf '%s\n' "$SUBMIT_COMMAND"
[BEYOND] -timeout 300 bash "$OSSH" "$SUBMIT_COMMAND" < "$DEST/BATCH.sh" > "$DEST/SUBMIT.out" 2> "$DEST/SUBMIT.err"
[BEYOND] -"$PY" "$LAUNCHER" record-submission --destination "$DEST"
[BEYOND] -JOB=$("$PY" -c 'import json,sys;print(json.load(open(sys.argv[1]))["job"])' "$DEST/SUBMISSION.json")
[BEYOND] -timeout 300 bash "$OSSH" "TZ=UTC sacct -j $JOB --format=JobID,JobName,State,ExitCode,Elapsed,Start,End -P"
[BEYOND] -# Poll at most once per minute. After completion:
[BEYOND] -"$PY" "$LAUNCHER" fetch --destination "$DEST"
[BEYOND] -```
[BEYOND] -
[BEYOND] -Production uses the same commands with a fresh token and `--mode production`; omit `--skip-phase-b`. Production requests one H100, general, 16 CPUs, 200G, six hours. Proof requests the same resources for two hours. Pool/GCS publication, write-test deadlines, caps and fetch governance remain the VSI launcher's code. The pool is `/project/community/jjyeung/okh7/x27ret`; GCS is `gs://cmu-gpucloud-jjyeung/q8/x27r/<token>/`. Fetch prints a governed command and stops before archive transfers of 20 MB or more. The operator registers and runs that command once.
[BEYOND] -
[BEYOND] -```bash
[BEYOND] -"$PY" - "$DEST" <<'PY'
[BEYOND] -import json,sys,tarfile
[BEYOND] -from pathlib import Path
[BEYOND] -p=Path(sys.argv[1]);out=p/'packet';out.mkdir()
[BEYOND] -with tarfile.open(p/'fetched/result.tar.gz') as archive:archive.extractall(out,filter='data')
[BEYOND] -assert json.loads((p/'fetched/EXIT.json').read_text())['status']=='COMPLETE'
[BEYOND] -print((out/'COMPLETE.json').read_text())
[BEYOND] -print((out/'report/SUMMARY.txt').read_text())
[BEYOND] -PY
[BEYOND] -"$PY" kit_revsi/proof/lines_report.py "$DEST/fetched/TRACE.json.gz" --json "$DEST/LINES.json" > "$DEST/LINES.txt"
[BEYOND] -```
[BEYOND] -
[BEYOND] -After production returns, supply the parent's merged `budget_2048/0/items_*.jsonl` to compute paired scene intervals. The parent may contain all 999 IDs; the scorer requires all 679 selected IDs, rejects duplicates and conflicting task metadata, and ignores excluded categories. It records the parent file's SHA256. Parent answers are unavailable in this workspace, so no real parent comparison or reproduction of its reported seven-category result is claimed.
[BEYOND] -
[BEYOND] -```bash
[BEYOND] -"$PY" kit_revsi/reader/official_score.py --dest "$DEST/packet/a0" --output "$DEST/rescored" --parent-answers /path/to/parent/items.jsonl
[BEYOND] -```
[BEYOND] -
[BEYOND] -The scorer uses native per-item scores, equal subtype means within each category, and the equal mean of the five categories. It reports B2048 first, ON16k and B4096 second, plus direction toward/away determined only from question text. All intervals use 10,000 scene-cluster draws and seed 544; paired draws use identical scene weights for both models. Undefined replicates are omitted only from the affected interval, with their valid count reported. Failed/missing answers score zero and remain in denominators. Proof uses present subtypes and is explicitly synthetic; it is not a performance estimate. Absolute distance and room size are marked “not read here: native reader required.” Native intermediate merge summaries retain their unchanged schema; the reader-facing report is `report/SUMMARY.txt` and the three arm JSON files.
[BEYOND] +Use [the operator report](../REPORT.md) for preparation, proof dependency, submission, fetch, and local validation commands. The supported steps are 200, 400, 600, 800, and 1000. The guarded synthetic proof entry is `proof/run.py --work <fresh local directory>`.
```

### kit/launcher/MODELS.json — PATH/ENV

```diff
--- ea1a1b2d/launcher/MODELS.json
+++ kit/launcher/MODELS.json
@@ -9,7 +9,7 @@
   },
   "cp1m200": {
     "kind": "c1_export",
[PATH/ENV] -    "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/469ddece/m544/artifact.json",
[PATH/ENV] -    "sha256": "1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef"
[PATH/ENV] +    "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/359fcc3c/m400/artifact.json",
[PATH/ENV] +    "sha256": null
   }
 }
```

### kit/launcher/TRANSPORT.json — PATH/ENV

```diff
--- ea1a1b2d/launcher/TRANSPORT.json
+++ kit/launcher/TRANSPORT.json
@@ -1,122 +1 @@
[PATH/ENV] -{
[PATH/ENV] -  "archive_bytes": 21583032320,
[PATH/ENV] -  "archive_sha256": "3ed73aead82cb0bb6468321256ea25e8fdaa5a2963da31062fdf8874bda2d4c7",
[PATH/ENV] -  "members": [
[PATH/ENV] -    {
[PATH/ENV] -      "header_offset": 0,
[PATH/ENV] -      "mode": 448,
[PATH/ENV] -      "name": "m544",
[PATH/ENV] -      "size": 0,
[PATH/ENV] -      "type": "5"
[PATH/ENV] -    },
[PATH/ENV] -    {
[PATH/ENV] -      "header_offset": 512,
[PATH/ENV] -      "mode": 384,
[PATH/ENV] -      "name": "m544/artifact.json",
[PATH/ENV] -      "size": 11474,
[PATH/ENV] -      "type": "0"
[PATH/ENV] -    },
[PATH/ENV] -    {
[PATH/ENV] -      "header_offset": 12800,
[PATH/ENV] -      "mode": 448,
[PATH/ENV] -      "name": "m544/full_weights",
[PATH/ENV] -      "size": 0,
[PATH/ENV] -      "type": "5"
[PATH/ENV] -    },
[PATH/ENV] -    {
[PATH/ENV] -      "header_offset": 13312,
[PATH/ENV] -      "mode": 384,
[PATH/ENV] -      "name": "m544/full_weights/model-00004-of-00005.safetensors",
[PATH/ENV] -      "size": 4290296144,
[PATH/ENV] -      "type": "0"
[PATH/ENV] -    },
[PATH/ENV] -    {
[PATH/ENV] -      "header_offset": 4290310144,
[PATH/ENV] -      "mode": 384,
[PATH/ENV] -      "name": "m544/full_weights/full_weights.json",
[PATH/ENV] -      "size": 1794,
[PATH/ENV] -      "type": "0"
[PATH/ENV] -    },
[PATH/ENV] -    {
[PATH/ENV] -      "header_offset": 4290312704,
[PATH/ENV] -      "mode": 384,
[PATH/ENV] -      "name": "m544/full_weights/model-00001-of-00005.safetensors",
[PATH/ENV] -      "size": 4203292568,
[PATH/ENV] -      "type": "0"
[PATH/ENV] -    },
[PATH/ENV] -    {
[PATH/ENV] -      "header_offset": 8493605888,
[PATH/ENV] -      "mode": 384,
[PATH/ENV] -      "name": "m544/full_weights/model-00002-of-00005.safetensors",
[PATH/ENV] -      "size": 4266317352,
[PATH/ENV] -      "type": "0"
[PATH/ENV] -    },
[PATH/ENV] -    {
[PATH/ENV] -      "header_offset": 12759924224,
[PATH/ENV] -      "mode": 384,
[PATH/ENV] -      "name": "m544/full_weights/model.safetensors.index.json",
[PATH/ENV] -      "size": 67691,
[PATH/ENV] -      "type": "0"
[PATH/ENV] -    },
[PATH/ENV] -    {
[PATH/ENV] -      "header_offset": 12759992832,
[PATH/ENV] -      "mode": 384,
[PATH/ENV] -      "name": "m544/full_weights/model-00003-of-00005.safetensors",
[PATH/ENV] -      "size": 4265727264,
[PATH/ENV] -      "type": "0"
[PATH/ENV] -    },
[PATH/ENV] -    {
[PATH/ENV] -      "header_offset": 17025720832,
[PATH/ENV] -      "mode": 384,
[PATH/ENV] -      "name": "m544/full_weights/model-00005-of-00005.safetensors",
[PATH/ENV] -      "size": 1794087688,
[PATH/ENV] -      "type": "0"
[PATH/ENV] -    },
[PATH/ENV] -    {
[PATH/ENV] -      "header_offset": 18819809280,
[PATH/ENV] -      "mode": 384,
[PATH/ENV] -      "name": "m544/heads.pt",
[PATH/ENV] -      "size": 2763214343,
[PATH/ENV] -      "type": "0"
[PATH/ENV] -    }
[PATH/ENV] -  ],
[PATH/ENV] -  "schema": "transport-rebuilt-v1",
[PATH/ENV] -  "step": 544,
[PATH/ENV] -  "artifact_sha256": "1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef",
[PATH/ENV] -  "parts": [
[PATH/ENV] -    {
[PATH/ENV] -      "name": "q8/8865619b/469ddece_mstop.tar.part00-of-04",
[PATH/ENV] -      "generation": "1794665056278014",
[PATH/ENV] -      "sha256": "5cd24e72f5b8a4f7ad6cb73d27dd426042be25e7600dcf00e4038de4c129f31a",
[PATH/ENV] -      "bytes": 5395758080,
[PATH/ENV] -      "md5": "Xi20/vGu9vdj15wMHN+O6g==",
[PATH/ENV] -      "offset": 0
[PATH/ENV] -    },
[PATH/ENV] -    {
[PATH/ENV] -      "name": "q8/8865619b/469ddece_mstop.tar.part01-of-04",
[PATH/ENV] -      "generation": "1794665041985097",
[PATH/ENV] -      "sha256": "6ed00d4724b1cfc57d0af6a017639d88284a139479ebf8b9943f280dc6c5df9f",
[PATH/ENV] -      "bytes": 5395758080,
[PATH/ENV] -      "md5": "SC1jCb+r3+hOIxmdQf/RJw==",
[PATH/ENV] -      "offset": 5395758080
[PATH/ENV] -    },
[PATH/ENV] -    {
[PATH/ENV] -      "name": "q8/8865619b/469ddece_mstop.tar.part02-of-04",
[PATH/ENV] -      "generation": "1794665039963627",
[PATH/ENV] -      "sha256": "557d8f649b964bd81a1c022dd87db18bdca0c2b61e420c2eccb1fc446a58f7bf",
[PATH/ENV] -      "bytes": 5395758080,
[PATH/ENV] -      "md5": "pee0rwP+yLJnYro5Y5c1OA==",
[PATH/ENV] -      "offset": 10791516160
[PATH/ENV] -    },
[PATH/ENV] -    {
[PATH/ENV] -      "name": "q8/8865619b/469ddece_mstop.tar.part03-of-04",
[PATH/ENV] -      "generation": "1794665051797628",
[PATH/ENV] -      "sha256": "37e64c63c294a3eda298c61f637087c84851afa17f42ad18a4d24c8823c7f686",
[PATH/ENV] -      "bytes": 5395758080,
[PATH/ENV] -      "md5": "2zzgIpB5yO/jWVnCfIHnDw==",
[PATH/ENV] -      "offset": 16187274240
[PATH/ENV] -    }
[PATH/ENV] -  ],
[PATH/ENV] -  "provenance_sha256": "c93417069ddddf0256869d04e0413dff9069a9457275f3e95fd54f688a3722cb",
[PATH/ENV] -  "historical_attestation_recovered": false
[PATH/ENV] -}
[PATH/ENV] +{"run": "359fcc3c", "lineage": "8865619b", "steps": [200, 400, 600, 800, 1000], "parts": 4}
```

### kit/launcher/export_stage.py — PATH/ENV

```diff
--- ea1a1b2d/launcher/export_stage.py
+++ kit/launcher/export_stage.py
@@ -0,0 +1,227 @@
[PATH/ENV] +"""Authenticated archive admission using the reviewed stage_export function."""
[PATH/ENV] +import argparse
[PATH/ENV] +from contextlib import contextmanager
[PATH/ENV] +import fcntl
[PATH/ENV] +import hashlib
[PATH/ENV] +import json
[PATH/ENV] +import os
[PATH/ENV] +from pathlib import Path, PurePosixPath
[PATH/ENV] +import re
[PATH/ENV] +import shutil
[PATH/ENV] +import subprocess
[PATH/ENV] +import tarfile
[PATH/ENV] +import time
[PATH/ENV] +from types import SimpleNamespace as NS
[PATH/ENV] +import orchard_stage as S
[PATH/ENV] +import orchard_job as J
[PATH/ENV] +import chain_save as A
[PATH/ENV] +
[PATH/ENV] +CHECKER = Path('reader/out/export_check.py')
[PATH/ENV] +CHECKER_PINS = {
[PATH/ENV] +    'export_check.py': '0400842c559565b66db50d6c8fde7c323e8600a82d70685d469a4b316d7ec8d2',
[PATH/ENV] +    'common.py': '1954de01cc935fb744ebc92a3ede19a94658d2ce4fefb3c1e1ba40b03d2508c4',
[PATH/ENV] +}
[PATH/ENV] +
[PATH/ENV] +@contextmanager
[PATH/ENV] +def lock(path):
[PATH/ENV] +    with Path(path).open('a+b') as f:
[PATH/ENV] +        fcntl.flock(f, fcntl.LOCK_EX)
[PATH/ENV] +        yield
[PATH/ENV] +
[PATH/ENV] +
[PATH/ENV] +def writable(path):
[PATH/ENV] +    path = Path(path).absolute()
[PATH/ENV] +    if path.resolve() != path or not path.is_relative_to('/tmp'):
[PATH/ENV] +        raise ValueError('Require canonical job-local storage')
[PATH/ENV] +    return path
[PATH/ENV] +
[PATH/ENV] +
[PATH/ENV] +def logical_artifact(root, path, step):
[PATH/ENV] +    allowed = {str(J.FSW/'ap/8865619b/runs'/run/('m'+str(step))/'artifact.json') for run in ('469ddece', '359fcc3c')}
[PATH/ENV] +    if path not in allowed or type(step) is not int or step <= 0:
[PATH/ENV] +        raise ValueError('Export lineage differs')
[PATH/ENV] +    return path
[PATH/ENV] +
[PATH/ENV] +
[PATH/ENV] +T = NS(writable=writable, EXPORT_RUNS=('469ddece', '359fcc3c'),
[PATH/ENV] +       FSW=J.FSW, logical_artifact=logical_artifact, physical=J.physical,
[PATH/ENV] +       load=lambda p: json.loads(Path(p).read_text()), sha=S.sha, lock=lock,
[PATH/ENV] +       kit_stage=lambda: S, dump=A.atomic_json)
[PATH/ENV] +
[PATH/ENV] +
[PATH/ENV] +def completed_local(value, tar=False):
[PATH/ENV] +    path = writable(value)
[PATH/ENV] +    if '.part' in path.name or not path.is_file() or (tar and path.suffix != '.tar'):
[PATH/ENV] +        raise ValueError('Require a completed regular local file')
[PATH/ENV] +    return path
[PATH/ENV] +
[PATH/ENV] +
[PATH/ENV] +def run_export_checker(root, artifact, digest, step, full, receipt_dir, bwrap):
[PATH/ENV] +    if not full:
[PATH/ENV] +        raise ValueError('Full verification is required')
[PATH/ENV] +    config = T.load(root/'bootstrap/CONFIG.json')
[PATH/ENV] +    checker = Path(config['spec']['package'])/CHECKER
[PATH/ENV] +    for name, pin in CHECKER_PINS.items():
[PATH/ENV] +        if S.sha(J.physical(root, checker.parent/name)) != pin:
[PATH/ENV] +            raise ValueError('Checker source changed')
[PATH/ENV] +    output = receipt_dir/'CHECK.json'
[PATH/ENV] +    command = J.namespace(root)+[config['spec']['interpreters']['p1cpu'], '-B', str(checker),
[PATH/ENV] +        '--export', artifact, '--sha256', digest, '--base', config['spec']['models']['base']['path'],
[PATH/ENV] +        '--step', str(step), '--output', str(output)]
[PATH/ENV] +    A.atomic_json(receipt_dir/'COMMAND.json', dict(argv=command, full=True, pins=CHECKER_PINS))
[PATH/ENV] +    # The checker prints model metadata; retain it as encoded evidence.
[PATH/ENV] +    result = subprocess.run(command, env=J.environment(root), cwd=root, capture_output=True)
[PATH/ENV] +    (receipt_dir/'check.hex').write_text(result.stdout.hex()+'\n'+result.stderr.hex()+'\n')
[PATH/ENV] +    if result.returncode:
[PATH/ENV] +        raise RuntimeError('Full export check failed')
[PATH/ENV] +    checked = T.load(output)
[PATH/ENV] +    if checked.get('status') != 'VERIFIED' or checked.get('step') != step:
[PATH/ENV] +        raise ValueError('Unexpected checker result')
[PATH/ENV] +    return checked
[PATH/ENV] +
[PATH/ENV] +
[PATH/ENV] +def stage_export(args):
[PATH/ENV] +    root = T.writable(args.root)
[PATH/ENV] +    if args.run not in T.EXPORT_RUNS or type(args.step) is not int or args.step <= 0:
[PATH/ENV] +        raise ValueError('Require an allowed run and positive step')
[PATH/ENV] +    source = completed_local(args.tar, tar=True); done_path = completed_local(args.done)
[PATH/ENV] +    done = T.load(done_path)
[PATH/ENV] +    if (not isinstance(done, dict) or not isinstance(done.get('object'), str) or not done['object'].strip() or
[PATH/ENV] +            type(done.get('bytes')) is not int or done['bytes'] <= 0 or
[PATH/ENV] +            not isinstance(done.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', done['sha256'])):
[PATH/ENV] +        raise ValueError('Done record requires object, positive integer bytes, and whole-tar sha256')
[PATH/ENV] +    logical = str(T.FSW/'ap/8865619b/runs'/args.run/('m'+str(args.step))/'artifact.json')
[PATH/ENV] +    T.logical_artifact(root, logical, args.step)
[PATH/ENV] +    dest = T.physical(root, logical).parent
[PATH/ENV] +    if dest.resolve() != dest: raise ValueError('Export destination has a symlink')
[PATH/ENV] +    receipt_dir = root/'exports'/(args.run+'_m'+str(args.step))
[PATH/ENV] +    if receipt_dir.resolve() != receipt_dir: raise ValueError('Receipt destination has a symlink')
[PATH/ENV] +    root.mkdir(parents=True, exist_ok=True)
[PATH/ENV] +    with T.lock(root/'.stage-export.lock'):
[PATH/ENV] +        if dest.exists() or receipt_dir.exists(): raise ValueError('Milestone or receipt exists; no overwrite or retry')
[PATH/ENV] +        # Hash and parse the same open file, never the arriving partial name.
[PATH/ENV] +        with source.open('rb') as stream:
[PATH/ENV] +            before = source.stat()
[PATH/ENV] +            if before.st_size != done['bytes']: raise ValueError('Tar bytes differ from done record')
[PATH/ENV] +            h = hashlib.sha256()
[PATH/ENV] +            for chunk in iter(lambda: stream.read(1024*1024), b''): h.update(chunk)
[PATH/ENV] +            if h.hexdigest() != done['sha256']: raise ValueError('Tar SHA256 differs from done record')
[PATH/ENV] +            stream.seek(0)
[PATH/ENV] +            with tarfile.open(fileobj=stream, mode='r:') as archive:
[PATH/ENV] +                members = []; names = set(); sizes = 0
[PATH/ENV] +                for member in archive:
[PATH/ENV] +                    path = PurePosixPath(member.name)
[PATH/ENV] +                    if (path.is_absolute() or '..' in path.parts or not path.parts or
[PATH/ENV] +                            path.parts[0] != dest.name or not (member.isfile() or member.isdir())):
[PATH/ENV] +                        raise ValueError('Unsafe member or unexpected milestone layout: '+member.name)
[PATH/ENV] +                    name = str(path)
[PATH/ENV] +                    if name in names: raise ValueError('Duplicate tar member: '+name)
[PATH/ENV] +                    names.add(name)
[PATH/ENV] +                    rel = path.parts[1:]
[PATH/ENV] +                    if rel and (rel[0] not in ('artifact.json', 'heads.pt', 'full_weights') or
[PATH/ENV] +                                (rel[0] != 'full_weights' and (len(rel) != 1 or not member.isfile()))):
[PATH/ENV] +                        raise ValueError('Unexpected milestone layout: '+name)
[PATH/ENV] +                    if not rel and not member.isdir(): raise ValueError('Milestone root must be a directory')
[PATH/ENV] +                    if rel == ('full_weights',) and not member.isdir(): raise ValueError('Weights must be a directory')
[PATH/ENV] +                    members.append((member, path))
[PATH/ENV] +                    if member.isfile(): sizes += member.size
[PATH/ENV] +                files = {str(p) for m, p in members if m.isfile()}
[PATH/ENV] +                required = {dest.name+'/'+p for p in ('artifact.json', 'heads.pt', 'full_weights/full_weights.json')}
[PATH/ENV] +                if not required <= files: raise ValueError('Missing required milestone layout')
[PATH/ENV] +                for name in names:
[PATH/ENV] +                    if any(str(p) in files for p in PurePosixPath(name).parents):
[PATH/ENV] +                        raise ValueError('File/directory collision in tar')
[PATH/ENV] +                T.kit_stage().room(root, sizes)
[PATH/ENV] +                receipt_dir.mkdir(parents=True)
[PATH/ENV] +                receipt = dict(schema=1, status='extracting', run=args.run, step=args.step,
[PATH/ENV] +                    source=str(source), done_path=str(done_path), done_sha256=T.sha(done_path), done=done,
[PATH/ENV] +                    tar_bytes=before.st_size, tar_sha256=h.hexdigest(), extracted_bytes=sizes,
[PATH/ENV] +                    artifact=logical, checker_mode='full' if args.full else 'header-only',
[PATH/ENV] +                    members=len(members), started=time.time())
[PATH/ENV] +                T.dump(receipt_dir/'RECEIPT.json', receipt)
[PATH/ENV] +                try:
[PATH/ENV] +                    dest.mkdir(parents=True)
[PATH/ENV] +                    for member, path in members:
[PATH/ENV] +                        target = dest.parent/str(path)
[PATH/ENV] +                        if member.isdir(): target.mkdir(parents=True, exist_ok=True)
[PATH/ENV] +                        else:
[PATH/ENV] +                            target.parent.mkdir(parents=True, exist_ok=True)
[PATH/ENV] +                            with archive.extractfile(member) as inp, target.open('xb') as out:
[PATH/ENV] +                                shutil.copyfileobj(inp, out, 1024*1024)
[PATH/ENV] +                            target.chmod(0o600)
[PATH/ENV] +                    after = source.stat()
[PATH/ENV] +                    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
[PATH/ENV] +                        raise ValueError('Tar changed during staging')
[PATH/ENV] +                    receipt['status'] = 'extracted'
[PATH/ENV] +                    receipt['artifact_sha256'] = T.sha(dest/'artifact.json')
[PATH/ENV] +                    T.dump(receipt_dir/'RECEIPT.json', receipt)
[PATH/ENV] +                    receipt['checker'] = run_export_checker(root, logical, receipt['artifact_sha256'], args.step,
[PATH/ENV] +                                                           args.full, receipt_dir, args.bwrap)
[PATH/ENV] +                    receipt['status'] = 'complete'
[PATH/ENV] +                    return receipt
[PATH/ENV] +                except Exception as error:
[PATH/ENV] +                    receipt.update(status='failed', error=str(error))
[PATH/ENV] +                    raise
[PATH/ENV] +                finally:
[PATH/ENV] +                    receipt['finished'] = time.time()
[PATH/ENV] +                    T.dump(receipt_dir/'RECEIPT.json', receipt)
[PATH/ENV] +
[PATH/ENV] +
[PATH/ENV] +def parse_done(raw, run, step):
[PATH/ENV] +    """Read the uploader's one-line receipt; bytes and SHA cover the whole tar."""
[PATH/ENV] +    if run not in T.EXPORT_RUNS or type(step) is not int or step <= 0:
[PATH/ENV] +        raise ValueError('Invalid completion receipt identity')
[PATH/ENV] +    obj = 'q8/8865619b/'+run+'_m'+str(step)+'.tar'
[PATH/ENV] +    match = re.fullmatch(re.escape(obj).encode()+rb' ([1-9][0-9]*) ([0-9a-f]{64})\n?', raw)
[PATH/ENV] +    if match is None:
[PATH/ENV] +        raise ValueError('Completion receipt identity or format differs')
[PATH/ENV] +    return dict(object=obj, bytes=int(match[1]), sha256=match[2].decode('ascii'))
[PATH/ENV] +
[PATH/ENV] +
[PATH/ENV] +def fetch_and_stage(root, config):
[PATH/ENV] +    root = Path(root)
[PATH/ENV] +    step = config['spec']['step']
[PATH/ENV] +    receipt = Path('/project/community/jjyeung/okh7/x_f5c353f7/o')/('gcs_359fcc3c_m'+str(step)+'.done')
[PATH/ENV] +    if receipt.is_symlink() or receipt.stat().st_size > 65536:
[PATH/ENV] +        raise ValueError('Invalid completion receipt')
[PATH/ENV] +    raw = receipt.read_bytes()
[PATH/ENV] +    done = parse_done(raw, '359fcc3c', step)
[PATH/ENV] +    uri = 'gs://cmu-gpucloud-jjyeung/'+done['object']
[PATH/ENV] +    (root/'archives/COMPLETE.done').write_bytes(raw)
[PATH/ENV] +    target = root/'archives/export.tar'
[PATH/ENV] +    partial = target.with_suffix('.partial')
[PATH/ENV] +    if target.exists() or partial.exists():
[PATH/ENV] +        raise ValueError('Export already attempted')
[PATH/ENV] +    S.room(root, 2*done['bytes'])
[PATH/ENV] +    env = S.cloud_environment(config['assets']['gcloud_config'])
[PATH/ENV] +    started = time.monotonic(); count = 0; h = hashlib.sha256()
[PATH/ENV] +    with partial.open('xb') as out:
[PATH/ENV] +        for part in range(4):
[PATH/ENV] +            obj = uri+'.part%02d-of-04'%part
[PATH/ENV] +            with S.process_stream(['gcloud', 'storage', 'cat', obj], env, root/'staging.log') as inp:
[PATH/ENV] +                for chunk in iter(lambda: inp.read(S.CHUNK), b''):
[PATH/ENV] +                    count += len(chunk)
[PATH/ENV] +                    if count > done['bytes']:
[PATH/ENV] +                        raise ValueError('Export exceeds receipt size')
[PATH/ENV] +                    h.update(chunk)
[PATH/ENV] +                    if out.write(chunk) != len(chunk):
[PATH/ENV] +                        raise OSError('Short export write')
[PATH/ENV] +        out.flush(); os.fsync(out.fileno())
[PATH/ENV] +    if count != done['bytes'] or h.hexdigest() != done['sha256']:
[PATH/ENV] +        raise ValueError('Whole archive differs from completion receipt')
[PATH/ENV] +    os.rename(partial, target)
[PATH/ENV] +    local_done = root/'archives/COMPLETE.json'
[PATH/ENV] +    A.atomic_json(local_done, done)
[PATH/ENV] +    transfer_seconds = time.monotonic()-started
[PATH/ENV] +    result = stage_export(NS(root=str(root), run='359fcc3c', step=step, tar=str(target),
[PATH/ENV] +                             done=str(local_done), full=True, bwrap=str(root/'bwrap')))
[PATH/ENV] +    result['transfer_seconds'] = transfer_seconds
[PATH/ENV] +    result['transfer_and_admission_seconds'] = time.monotonic()-started
[PATH/ENV] +    config['spec']['artifact']['sha256'] = result['artifact_sha256']
[PATH/ENV] +    config['spec']['models']['cp1m200'] = dict(config['spec']['artifact'])
[PATH/ENV] +    config['admission'] = result
[PATH/ENV] +    package = J.physical(root, config['spec']['package'])
[PATH/ENV] +    A.atomic_json(package/'launcher/MODELS.json',config['spec']['models'])
[PATH/ENV] +    # The submitted plan binds step and input receipt; resolved bytes are recorded separately.
[PATH/ENV] +    A.atomic_json(root/'bootstrap/CONFIG.json', config)
[PATH/ENV] +    return result
```

### kit/launcher/opaque_io.py — PATH/ENV

```diff
--- ea1a1b2d/launcher/opaque_io.py
+++ kit/launcher/opaque_io.py
@@ -0,0 +1,41 @@
[PATH/ENV] +"""Preserve diagnostics as hex without exposing their text in job logs."""
[PATH/ENV] +import os
[PATH/ENV] +import sys
[PATH/ENV] +import threading
[PATH/ENV] +from contextlib import contextmanager
[PATH/ENV] +
[PATH/ENV] +
[PATH/ENV] +def encode(source, destination):
[PATH/ENV] +    while True:
[PATH/ENV] +        chunk=source.read(4096)
[PATH/ENV] +        if not chunk:break
[PATH/ENV] +        destination.write(chunk.hex().encode()+b'\n')
[PATH/ENV] +        destination.flush()
[PATH/ENV] +
[PATH/ENV] +
[PATH/ENV] +def install():
[PATH/ENV] +    """Capture native writes and inherited child descriptors as well as Python output."""
[PATH/ENV] +    sys.stdout.flush();sys.stderr.flush()
[PATH/ENV] +    workers=[]
[PATH/ENV] +    for descriptor in (1,2):
[PATH/ENV] +        restore_fd=os.dup(descriptor)
[PATH/ENV] +        saved=os.dup(descriptor)
[PATH/ENV] +        reader,writer=os.pipe()
[PATH/ENV] +        os.dup2(writer,descriptor);os.close(writer)
[PATH/ENV] +        source=os.fdopen(reader,'rb',buffering=0)
[PATH/ENV] +        output=os.fdopen(saved,'wb',buffering=0)
[PATH/ENV] +        def pump(source=source,output=output):
[PATH/ENV] +            with source,output:encode(source,output)
[PATH/ENV] +        worker=threading.Thread(target=pump,daemon=True);worker.start();workers.append((descriptor,restore_fd,worker))
[PATH/ENV] +    return workers
[PATH/ENV] +
[PATH/ENV] +
[PATH/ENV] +@contextmanager
[PATH/ENV] +def redirect():
[PATH/ENV] +    workers=install()
[PATH/ENV] +    try:yield
[PATH/ENV] +    finally:
[PATH/ENV] +        sys.stdout.flush();sys.stderr.flush()
[PATH/ENV] +        for descriptor,restore_fd,worker in workers:
[PATH/ENV] +            os.dup2(restore_fd,descriptor);os.close(restore_fd)
[PATH/ENV] +        for descriptor,restore_fd,worker in workers:worker.join(timeout=5)
```

### kit/launcher/orchard_job.py — BEYOND

```diff
--- ea1a1b2d/launcher/orchard_job.py
+++ kit/launcher/orchard_job.py
@@ -179,6 +179,9 @@
 
     for number in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1):
         signal.signal(number, interrupted)
[BEYOND] +    deadline=time.monotonic()+config.get('wall_seconds',1500)
[BEYOND] +    signal.signal(signal.SIGALRM, interrupted)
[BEYOND] +    signal.alarm(config.get('wall_seconds',1500)-180)
     try:
         evidence['pool_write_test'] = R.write_test(config.get('pool',str(R.AUTHORIZED_POOL)), config['token'])
         evidence['storage'] = storage_proof(root, job=os.environ['SLURM_JOB_ID'])
@@ -212,6 +215,8 @@
             evidence['storage_refusal'] = error.evidence
         stop(process)
     finally:
[BEYOND] +        signal.signal(signal.SIGALRM, lambda n,f: (_ for _ in ()).throw(TimeoutError('Return deadline')))
[BEYOND] +        signal.alarm(max(1,int(deadline-time.monotonic()-30)))
         source.mkdir(parents=True, exist_ok=True)
         (source/'metadata').mkdir(exist_ok=True)
         (source/'logs').mkdir(exist_ok=True)
@@ -252,6 +257,7 @@
         except Exception as error:
             A.atomic_json(root/'RETURN_INCOMPLETE.json', dict(error=str(error), returncode=code or 1))
             code = code or 1
[BEYOND] +        signal.alarm(0)
         return code
 
 
```

### kit/launcher/orchard_launcher.py — BEYOND

```diff
--- ea1a1b2d/launcher/orchard_launcher.py
+++ kit/launcher/orchard_launcher.py
@@ -20,8 +20,8 @@
 
 ROOT = Path(__file__).resolve().parent
 CORE = ('orchard_launcher.py', 'orchard_job.py', 'orchard_stage.py', 'orchard_results.py',
[BEYOND] -        'chain_save.py', 'stdout_transfer.py', 'trace_runtime.py', 'return_io.py', 'ORCHARD_ASSETS.json')
[BEYOND] -SSH = ['bash', '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh']
[BEYOND] +        'chain_save.py', 'stdout_transfer.py', 'trace_runtime.py', 'return_io.py', 'export_stage.py', 'opaque_io.py', 'ORCHARD_ASSETS.json')
[BEYOND] +SSH = ['timeout', '300', 'bash', '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh']
 
 
 def canonical(value):
@@ -33,7 +33,7 @@
 
 
 def valid_token(token):
[BEYOND] -    if not re.fullmatch('[a-z][0-9a-f]{8,32}', token):
[BEYOND] +    if not re.fullmatch('[0-9a-f]{10,32}', token):
         raise ValueError('Invalid one-use read token')
     return token
 
@@ -56,7 +56,7 @@
         raise ValueError('The embedded batch package exceeds its 3 MiB limit')
     return '''#!/bin/bash
 set -euo pipefail
[BEYOND] -exec python3 -I -s -B - <<'EVALX_BATCH_BOOTSTRAP'
[BEYOND] +exec python3 -I -s -B - <<'A_BATCH_BOOTSTRAP'
 import base64,hashlib,io,os,sys,tarfile
 from pathlib import Path,PurePosixPath
 job=os.environ.get('SLURM_JOB_ID','')
@@ -82,27 +82,29 @@
 os.chdir(root)
 os.execv(sys.executable,[sys.executable,'-I','-s','-B',str(root/'bootstrap/trace_runtime.py'),
     '--script',str(root/'bootstrap/orchard_job.py'),'--root',str(root),'--config',str(root/'bootstrap/CONFIG.json')])
[BEYOND] -EVALX_BATCH_BOOTSTRAP
[BEYOND] +A_BATCH_BOOTSTRAP
 ''' % (encoded, hashlib.sha256(bundle).hexdigest(), root_parent, token)
 
 
[BEYOND] -def submit_argv(script, token, proof=False):
[BEYOND] +def submit_argv(script, token, proof=False, afterok=None):
     valid_token(token)
[BEYOND] +    if not proof and (type(afterok) is not int or afterok <= 0):
[BEYOND] +        raise ValueError('Require successful proof dependency')
     return ['sbatch', '--parsable', '--account=mt01', '--partition=general', '--nodes=1',
[BEYOND] -            '--ntasks=1', *(['--gres=gpu:1', '--cpus-per-task=16', '--mem=200G', '--time=02:00:00'] if proof else
[BEYOND] -            ['--gres=gpu:1', '--cpus-per-task=16', '--mem=200G', '--time=06:00:00']),
[BEYOND] -            '--signal=B:USR1@300', '--no-requeue', '--output=/dev/null', '--error=/dev/null',
[BEYOND] -            '--chdir=/tmp', '--job-name=a15_cot_ap'+token]+([script] if script is not None else [])
[BEYOND] -
[BEYOND] -
[BEYOND] -def submit_command(token, proof=False):
[BEYOND] +            '--ntasks=1', *(['--gres=gpu:1', '--cpus-per-task=16', '--mem=200G', '--time=00:21:00'] if proof else
[BEYOND] +            ['--gres=gpu:1', '--cpus-per-task=16', '--mem=200G', '--time=00:25:00']),
[BEYOND] +            '--signal=B:USR1@180', '--no-requeue', '--output=/dev/null', '--error=/dev/null',
[BEYOND] +            '--chdir=/tmp', '--job-name=a15_cot_ap'+token]+([] if proof else ['--dependency=afterok:'+str(afterok)])+([script] if script is not None else [])
[BEYOND] +
[BEYOND] +
[BEYOND] +def submit_command(token, proof=False, afterok=None):
     code = (
         "import subprocess,sys\n"
         "body=sys.stdin.buffer.read(4*1024**2+1)\n"
         "if not body or len(body)>4*1024**2: raise ValueError('Invalid batch size')\n"
[BEYOND] -        "argv="+repr(submit_argv(None, token, proof=proof))+"\n"
[BEYOND] +        "argv="+repr(submit_argv(None, token, proof=proof, afterok=afterok))+"\n"
         "test=subprocess.run(argv+['--test-only'],input=body,capture_output=True,timeout=50)\n"
[BEYOND] -        "sys.stderr.buffer.write(b'EVALX_TEST_ONLY_RC='+str(test.returncode).encode()+b'\\n'+test.stdout+test.stderr)\n"
[BEYOND] +        "sys.stderr.buffer.write(b'A_TEST_ONLY_RC='+str(test.returncode).encode()+b'\\n'+test.stdout+test.stderr)\n"
         "if test.returncode: sys.exit(test.returncode)\n"
         "result=subprocess.run(argv,input=body,capture_output=True,timeout=50)\n"
         "sys.stdout.buffer.write(result.stdout)\n"
@@ -145,12 +147,17 @@
         raise ValueError('Proof configurations cannot be submitted')
     if config.get('mode', 'production') not in ('proof', 'production'):
         raise ValueError('Invalid execution mode')
[BEYOND] -    if config.get('schema') != 'evalx-orchard-batch-v1' or config['spec']['step']!=544:
[BEYOND] +    if config.get('schema') != 'evalx-orchard-batch-v1' or config['spec']['step'] not in (200,400,600,800,1000):
         raise ValueError('Invalid job contract')
     if canonical(config['spec'])!=config['plan_sha256']:
         raise ValueError('Plan differs')
[BEYOND] -    if config['spec']['artifact']['sha256']!='1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef':
[BEYOND] +    expected = str(J.FSW/'ap/8865619b/runs/359fcc3c'/('m'+str(config['spec']['step']))/'artifact.json')
[BEYOND] +    if config['spec']['artifact'] != dict(kind='c1_export',path=expected,sha256=None):
         raise ValueError('Artifact differs')
[BEYOND] +    if config.get('phase_b'):
[BEYOND] +        raise ValueError('Unregistered optional phase')
[BEYOND] +    if config['mode']=='production' and (type(config.get('afterok')) is not int or config['afterok']<=0):
[BEYOND] +        raise ValueError('Require proof dependency')
 
 
 def validate_payload(raw, config):
@@ -165,8 +172,18 @@
         raise ValueError('Payload inventory differs')
 
 
[BEYOND] -def prepare(token, destination, frame_plan=None, mode="production", pool="/project/community/jjyeung/okh7/x27ret", media_root=None, phase_b=True):
[BEYOND] -    if not Path(pool).is_absolute() or any(c in pool for c in "\n\r\x00"):raise ValueError("Invalid pool path")
[BEYOND] +def prepare(token, destination, frame_plan=None, mode="production", pool="/project/community/jjyeung/okh7/6e29a4bc", media_root=None, phase_b=False, step=400, proof_destination=None):
[BEYOND] +    if not re.fullmatch(r'/project/community/jjyeung/okh7/[0-9a-f]{8,64}',pool):raise ValueError('Invalid pool path')
[BEYOND] +    if type(step) is not int or step not in (200,400,600,800,1000):raise ValueError('Invalid step')
[BEYOND] +    afterok=None
[BEYOND] +    if mode=='production':
[BEYOND] +        if proof_destination is None:raise ValueError('Require proof preparation')
[BEYOND] +        pd=Path(proof_destination);pc=json.loads((pd/'CONFIG.json').read_text());pr=json.loads((pd/'SUBMISSION.json').read_text())
[BEYOND] +        validate_request(pc);validate_batch((pd/'BATCH.sh').read_text(),pc)
[BEYOND] +        if (pc['mode']!='proof' or pc['spec']['step']!=step or pc['media_root']!=media_root
[BEYOND] +            or pr.get('status')!='SUBMITTED' or pr.get('plan_sha256')!=pc['plan_sha256']
[BEYOND] +            or pr.get('token')!=pc['token'] or pc['token']==token):raise ValueError('Proof identity differs')
[BEYOND] +        afterok=pr['job']
     if not isinstance(media_root,str) or not re.fullmatch(r'/project/community/jjyeung/okh7/[0-9a-f]{8,64}/?',media_root):
         raise ValueError('Require an opaque --media-root under /project/community/jjyeung/okh7/')
     valid_token(token)
@@ -193,9 +210,10 @@
     logical=J.SJ/('a'+token)
     payload_root=logical/'p'
     models=json.loads((ROOT/'MODELS.json').read_text())
[BEYOND] -    spec=dict(schema='a1',step=544,scope='direct',artifact=models['cp1m200'],models=models,
[BEYOND] +    models['cp1m200']=dict(kind='c1_export',path=str(J.FSW/'ap/8865619b/runs/359fcc3c'/('m'+str(step))/'artifact.json'),sha256=None)
[BEYOND] +    spec=dict(schema='a1',step=step,scope='direct',artifact=models['cp1m200'],models=models,
         run=str(logical/'r'),package=str(payload_root),
[BEYOND] -        interpreters=dict(p1cpu='/scratch/jjyeung/envs/p1cpu/bin/python',vllm=str(logical/'p/vllm_isolated.sh')),
[BEYOND] +        interpreters=dict(p1cpu='/scratch/jjyeung/envs/p1cpu/bin/python',vllm=str(logical/'p/a1.sh')),
         inputs=dict(rows=str(payload_root/'inputs/i1.json'),video_root=str(logical/'v0'),
                     frame_plan=str(payload_root/'cohort/FRAME_PLAN.json')))
     files={}
@@ -205,25 +223,31 @@
     for directory in ('reader','cohort','parity','inputs'):
         for p in sorted((package/directory).rglob('*')):
             rel=p.relative_to(package)
[BEYOND] -            if p.is_file() and p.suffix in ('.py','.json','.jsonl') and p.name not in ('meta_5130.jsonl','COHORT_OFFICIAL6.jsonl','FRAME_PLAN.json','REVSI_PUSH_FILES.json','REVSI999_PROVENANCE.json','cells_rv999_d32_cp1m200_on.json','cells_tr_rv999_cp1on.json'):
[BEYOND] +            if p.is_file() and p.suffix in ('.py','.json','.jsonl') and p.name not in ('cells_cp1m200.json','cells_f17.json','meta_5130.jsonl','COHORT_OFFICIAL6.jsonl','FRAME_PLAN.json','REVSI_PUSH_FILES.json','REVSI999_PROVENANCE.json','cells_rv999_d32_cp1m200_on.json','cells_tr_rv999_cp1on.json'):
                 add(rel,p.read_bytes())
     if frame_plan is not None:add(Path('cohort/FRAME_PLAN.json'),Path(frame_plan).read_bytes())
     for name in ('fakes.py','selection.py','runtime_checks.py','phase_b.py','pull.py'):
         add(Path('proof')/name,(package/'proof'/name).read_bytes())
[BEYOND] -    add(Path('launcher/MODELS.json'),(ROOT/'MODELS.json').read_bytes())
[BEYOND] -    add(Path('TRANSPORT.json'),(ROOT/'TRANSPORT.json').read_bytes())
[BEYOND] -    add(Path('vllm_isolated.sh'),('#!/bin/sh\nexec '+shlex.quote(str(J.AP/'19252904/e/bin/python'))+' -I "$@"\n').encode())
[BEYOND] +    add(Path('launcher/MODELS.json'),(json.dumps(models,sort_keys=True)+'\n').encode())
[BEYOND] +    transport=(json.dumps(dict(step=step,run='359fcc3c',lineage='8865619b',parts=4,receipt='/project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m'+str(step)+'.done'),sort_keys=True)+'\n').encode()
[BEYOND] +    add(Path('TRANSPORT.json'),transport)
[BEYOND] +    add(Path('a1.sh'),('#!/bin/sh\nexec '+shlex.quote(str(J.AP/'19252904/e/bin/python'))+' -I "$@"\n').encode())
     payload=tar_bytes(files)
     pins={n:S.sha(ROOT/n) for n in CORE}
     review=dict(schema='new-build-integrity-v1',code_pins_sha256=canonical(pins),historical_review_recovered=False)
     review_raw=(json.dumps(review,sort_keys=True)+'\n').encode()
     assets=json.loads((ROOT/'ORCHARD_ASSETS.json').read_text())
[BEYOND] -    config=dict(schema='evalx-orchard-batch-v1',mode=mode,phase_b=mode=='proof' and phase_b,media_root=media_root,pool=pool,token=token,spec=spec,output=str(logical/'o'),
[BEYOND] -        plan_sha256=canonical(spec),assets=assets,release=dict(transport=dict(path=str(payload_root/'TRANSPORT.json'),sha256=S.sha(ROOT/'TRANSPORT.json'))),
[BEYOND] +    config=dict(schema='evalx-orchard-batch-v1',mode=mode,afterok=afterok,wall_seconds=1260 if mode=='proof' else 1500,phase_b=mode=='proof' and phase_b,media_root=media_root,pool=pool,token=token,spec=spec,output=str(logical/'o'),
[BEYOND] +        plan_sha256=canonical(spec),assets=assets,release=dict(transport=dict(path=str(payload_root/'TRANSPORT.json'),sha256=hashlib.sha256(transport).hexdigest())),
         payload_pins={n:hashlib.sha256(v).hexdigest() for n,v in files.items()},
         payload_sha256=hashlib.sha256(payload).hexdigest(),launcher_pins=pins,
         launcher_review_pin=dict(path='REVIEW.json',sha256=hashlib.sha256(review_raw).hexdigest()),
         launcher_review=review,records={})
[BEYOND] +    if mode=='production':
[BEYOND] +        if pc['launcher_pins']!=pins:raise ValueError('Proof code differs')
[BEYOND] +        # Token prefixes differ; compare every payload byte by its relative path.
[BEYOND] +        def normalized(pins):return {n.split('/p/',1)[1]:v for n,v in pins.items()}
[BEYOND] +        if normalized(pc['payload_pins'])!=normalized(config['payload_pins']):raise ValueError('Proof payload differs')
     validate_request(config);validate_payload(payload,config)
     boot={'bootstrap/'+n:(ROOT/n).read_bytes() for n in CORE}
     boot.update({'bootstrap/payload.tar.gz':payload,'bootstrap/CONFIG.json':(json.dumps(config,sort_keys=True)+'\n').encode(),
@@ -233,6 +257,9 @@
     (destination/'BATCH.sh').write_text(script)
     (destination/'CONFIG.json').write_text(json.dumps(config,sort_keys=True,indent=2)+'\n')
     (destination/'BATCH.pin.json').write_text(json.dumps(dict(pin(destination/'BATCH.sh'),config_sha256=S.sha(destination/'CONFIG.json')))+'\n')
[BEYOND] +    ledger=ROOT.parent.parent/'LEDGER.jsonl'
[BEYOND] +    with ledger.open('a') as stream:
[BEYOND] +        stream.write(json.dumps(dict(token=token,step=step,mode=mode,purpose='ReVSI official999 direct ranking; no stopping decision',run='359fcc3c',lineage='8865619b',prepared=str(destination.resolve()),pool=pool,media=media_root,afterok=afterok),sort_keys=True)+'\n')
     return config
 
 
@@ -271,7 +298,7 @@
                  batch_sha256=hashlib.sha256(script).hexdigest(), status='SUBMIT_INTENT')
     with (destination/'SUBMIT_INTENT.json').open('x') as stream:
         json.dump(value, stream, indent=2, sort_keys=True)
[BEYOND] -    result = remote(submit_command(config['token'], proof=config.get('mode')=='proof'), input=script)
[BEYOND] +    result = remote(submit_command(config['token'], proof=config.get('mode')=='proof',afterok=config.get('afterok')), input=script)
     answer = result.stdout.decode(errors='replace').strip()
     job = answer.split(';')[0]
     value.update(status='SUBMITTED' if result.returncode == 0 and job.isdigit() else 'UNCERTAIN',
@@ -386,10 +413,12 @@
     prepare_parser = actions.add_parser('prepare')
     for name in ('token', 'destination'):
         prepare_parser.add_argument('--'+name, required=True)
[BEYOND] -    prepare_parser.add_argument('--media-root',required=True)
[BEYOND] +    prepare_parser.add_argument('--step',type=int,choices=(200,400,600,800,1000),default=400)
[BEYOND] +    prepare_parser.add_argument('--proof-destination')
[BEYOND] +    prepare_parser.add_argument('--media-root',default='/project/community/jjyeung/okh7/313db5a47f11ff0c')
     prepare_parser.add_argument('--skip-phase-b',action='store_true')
     prepare_parser.add_argument('--frame-plan')
[BEYOND] -    prepare_parser.add_argument('--pool',default='/project/community/jjyeung/okh7/x27ret')
[BEYOND] +    prepare_parser.add_argument('--pool',default='/project/community/jjyeung/okh7/6e29a4bc')
     prepare_parser.add_argument('--mode',choices=('proof','production'),default='production')
     submit_parser = actions.add_parser('submit')
     submit_parser.add_argument('--destination', required=True)
@@ -401,12 +430,12 @@
     fetch_parser.add_argument('--destination', required=True)
     args = parser.parse_args()
     if args.action == 'prepare':
[BEYOND] -        value = prepare(args.token, args.destination, args.frame_plan, args.mode, args.pool, args.media_root, not args.skip_phase_b)
[BEYOND] +        value = prepare(args.token, args.destination, args.frame_plan, args.mode, args.pool, args.media_root, False, args.step, args.proof_destination)
         print(json.dumps(dict(token=value['token'], plan_sha256=value['plan_sha256'])))
     elif args.action == 'submit-command':
         cfg=json.loads((Path(args.destination)/'CONFIG.json').read_text())
         validate_request(cfg);validate_batch((Path(args.destination)/'BATCH.sh').read_text(),cfg)
[BEYOND] -        print(shlex.join(submit_command(cfg['token'],proof=cfg['mode']=='proof')))
[BEYOND] +        print(shlex.join(submit_command(cfg['token'],proof=cfg['mode']=='proof',afterok=cfg.get('afterok'))))
     elif args.action == 'record-submission':
         print(json.dumps(submission_record(args.destination),sort_keys=True))
     elif args.action == 'submit':
```

### kit/launcher/orchard_results.py — PATH/ENV

```diff
--- ea1a1b2d/launcher/orchard_results.py
+++ kit/launcher/orchard_results.py
@@ -11,8 +11,8 @@
 import uuid
 import chain_save as S
 
[PATH/ENV] -AUTHORIZED_POOL = Path('/project/community/jjyeung/okh7/x27ret')
[PATH/ENV] -GCS_ROOT = 'gs://cmu-gpucloud-jjyeung/q8/x27r'
[PATH/ENV] +AUTHORIZED_POOL = Path('/project/community/jjyeung/okh7/6e29a4bc')
[PATH/ENV] +GCS_ROOT = 'gs://cmu-gpucloud-jjyeung/q8/6e29a4bc'
 CLOUD_CONFIG = '/project/community/jjyeung/gcloud'
 POOL_LIMIT = 100_000_000
 READ_LIMIT = 90_000_000
@@ -86,17 +86,17 @@
                 raise ValueError('GCS object SHA256 differs')
             objects[name]['verified']=True
             with (Path(local)/'JOB.log').open('a') as log:
[PATH/ENV] -                log.write(json.dumps(dict(upload=objects[name]),sort_keys=True)+'\n')
[PATH/ENV] +                log.write(json.dumps(dict(upload=objects[name]),sort_keys=True).encode().hex()+'\n')
     except Exception as error:
         with (Path(local)/'JOB.log').open('a') as log:
[PATH/ENV] -            log.write(json.dumps(dict(upload_error=str(error),objects=objects),sort_keys=True)+'\n')
[PATH/ENV] +            log.write(json.dumps(dict(upload_error=str(error),objects=objects),sort_keys=True).encode().hex()+'\n')
         raise UploadError(error,objects) from error
     return dict(verified=True,objects=objects)
 
 
 def publish(source,pool,token,plan_sha256,returncode,synthetic=False,rate=4*1024**2,mode='production'):
     source,pool=Path(source),Path(pool)
[PATH/ENV] -    if (not re.fullmatch('[a-z][0-9a-f]{8,32}',token) or rate<=0
[PATH/ENV] +    if (not re.fullmatch('[0-9a-f]{10,32}',token) or rate<=0
         or not re.fullmatch('[0-9a-f]{64}',plan_sha256) or not pool.is_absolute()):
         raise ValueError('Invalid return identity or pool')
     cap=20_000_000 if mode=='proof' else 90_000_000
@@ -116,7 +116,7 @@
     value.update(archive=dict(name=archive.name,bytes=archive.stat().st_size,sha256=sha(archive)),
                  archive_bytes=archive.stat().st_size,archive_sha256=sha(archive))
     S.atomic_json(local/'EXIT.json',value)
[PATH/ENV] -    (local/'JOB.log').write_text(json.dumps(value,sort_keys=True)+'\n')
[PATH/ENV] +    (local/'JOB.log').write_text(json.dumps(value,sort_keys=True).encode().hex()+'\n')
     receipt=dict(schema=1,token=token,plan_sha256=plan_sha256,job=value['job'],channels={},returned=False)
     try:receipt['channels']['pool']=pool_operation('publish',pool,token,local,timeout=120)
     except Exception as error:receipt['channels']['pool']=dict(verified=False,error=str(error))
@@ -126,7 +126,7 @@
     receipt['verified_channels']=[k for k,v in receipt['channels'].items() if v.get('verified')]
     S.atomic_json(local/'RETURN_RECEIPT.json',receipt)
     S.atomic_json(source/'RETURN_RECEIPT.json',receipt)
[PATH/ENV] -    with (local/'JOB.log').open('a') as log:log.write(json.dumps(receipt,sort_keys=True)+'\n')
[PATH/ENV] +    with (local/'JOB.log').open('a') as log:log.write(json.dumps(receipt,sort_keys=True).encode().hex()+'\n')
     if usage(local)-sum(p.stat().st_size for p in local.glob('*.gcs-check'))>=cap:
         raise S.BudgetError('Return files exceed mode cap')
     try:pool_operation('receipt',pool,token,local,timeout=60)
```

### kit/launcher/orchard_stage.py — PATH/ENV

```diff
--- ea1a1b2d/launcher/orchard_stage.py
+++ kit/launcher/orchard_stage.py
@@ -10,6 +10,8 @@
 import subprocess
 import tarfile
 import time
[PATH/ENV] +import threading
[PATH/ENV] +import opaque_io
 
 import chain_save as A
 
@@ -164,8 +166,10 @@
 @contextmanager
 def process_stream(argv, environment, log):
     with Path(log).open('ab') as output:
[PATH/ENV] -        process = subprocess.Popen(argv, env=environment, stdout=subprocess.PIPE, stderr=output,
[PATH/ENV] +        process = subprocess.Popen(argv, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    start_new_session=True)
[PATH/ENV] +        pump=threading.Thread(target=opaque_io.encode,args=(process.stderr,output),daemon=True)
[PATH/ENV] +        pump.start()
         try:
             yield ProcessStream(process)
             if process.wait(timeout=60):
@@ -179,6 +183,8 @@
                     os.killpg(process.pid, signal.SIGKILL)
                     process.wait(timeout=20)
             process.stdout.close()
[PATH/ENV] +            pump.join(timeout=5)
[PATH/ENV] +            process.stderr.close()
 
 
 def unpack(path, root, **kwargs):
@@ -223,7 +229,7 @@
     phase('start')
     archives = root/'archives'
     archives.mkdir()
[PATH/ENV] -    for index, group in enumerate(assets['groups']):
[PATH/ENV] +    for index, group in enumerate(assets['groups'][:2]):
         parts = [dict(path=p, bytes=n, sha256=h) for p, n, h in group]
         archive = archives/f'runtime_{index}.tar'
         receipts['runtime_'+str(index)] = copy_parts(
@@ -231,11 +237,7 @@
             rate=0)
         unpack(archive, root, links=True)
         phase('runtime_'+str(index))
[PATH/ENV] -    camera = assets['camera_archive']
[PATH/ENV] -    archive = archives/'a0.tar'
[PATH/ENV] -    receipts['camera'] = copy_parts([camera], archive, lambda part: Path(part['path']).open('rb'))
[PATH/ENV] -    unpack(archive, root)
[PATH/ENV] -    phase('a0')
[PATH/ENV] +    # The packaged reader supplies the code closure; no unused legacy tree is extracted.
     payload = root/'bootstrap/payload.tar.gz'
     if sha(payload) != config['payload_sha256']:
         raise ValueError('Reader payload differs from the submitted package')
@@ -262,35 +264,9 @@
             raise ValueError('Base snapshot payload differs from its frozen manifest')
     receipts['base'] = dict(manifest_sha256=sha(manifest), files=len(inventory))
     phase('base_snapshot')
[PATH/ENV] -    transport = json.loads(physical(root, config['release']['transport']['path']).read_text())
[PATH/ENV] -    receipts['export_transport'] = transport
[PATH/ENV] -    environment = cloud_environment(assets['gcloud_config'])
[PATH/ENV] -
[PATH/ENV] -    def cloud(part):
[PATH/ENV] -        uri = 'gs://cmu-gpucloud-jjyeung/'+part['name']+'#'+str(part['generation'])
[PATH/ENV] -        return process_stream(['gcloud', 'storage', 'cat', uri], environment, root/'staging.log')
[PATH/ENV] -
[PATH/ENV] -    archive = archives/'export.tar'
[PATH/ENV] -    before = config_metadata(assets['gcloud_config'])
[PATH/ENV] -    try:
[PATH/ENV] -        receipts['export'] = copy_parts(transport['parts'], archive, cloud,
[PATH/ENV] -                                        expected_sha=transport['archive_sha256'])
[PATH/ENV] -    finally:
[PATH/ENV] -        after = config_metadata(assets['gcloud_config'])
[PATH/ENV] -        receipts['gcloud_config_observation'] = dict(
[PATH/ENV] -            before=before, after=after, shared_config=True, attribution_exclusive=False,
[PATH/ENV] -            changed=[name for name in sorted(set(before) | set(after)) if before.get(name) != after.get(name)])
[PATH/ENV] -        phase('export_fetch')
[PATH/ENV] -    if receipts['export']['bytes'] != transport['archive_bytes']:
[PATH/ENV] -        raise ValueError('Export byte count differs')
[PATH/ENV] -    destination = physical(root, config['spec']['artifact']['path']).parent.parent
[PATH/ENV] -    destination.mkdir(parents=True)
[PATH/ENV] -    room(root, archive.stat().st_size)
[PATH/ENV] -    with archive.open('rb') as stream:
[PATH/ENV] -        extract_stream(stream, destination, config['spec']['step'], archive.stat().st_size)
[PATH/ENV] -    if sha(physical(root, config['spec']['artifact']['path'])) != config['spec']['artifact']['sha256']:
[PATH/ENV] -        raise ValueError('Downloaded production artifact differs')
[PATH/ENV] -    phase('export_extract')
[PATH/ENV] +    import export_stage
[PATH/ENV] +    receipts['export'] = export_stage.fetch_and_stage(root, config)
[PATH/ENV] +    phase('export_admission')
     receipts['videos'] = stage_videos(root, config, physical)
     phase('videos')
     room(root)
```

### kit/launcher/return_io.py — BEYOND

```diff
--- ea1a1b2d/launcher/return_io.py
+++ kit/launcher/return_io.py
@@ -1,4 +1,4 @@
[BEYOND] -"""Bounded pool operations; only the explicitly authorized .wtest is removed."""
[BEYOND] +"""Bounded pool operations; the .wtest evidence is retained."""
 import argparse
 import fcntl
 import hashlib
@@ -45,8 +45,7 @@
                 f.flush(); os.fsync(f.fileno())
             digest = sha(test)
             if digest != hashlib.sha256(data).hexdigest(): raise ValueError('Write test SHA256 differs')
[BEYOND] -            # The user authorizes removal of this one test file only.
[BEYOND] -            test.unlink()
[BEYOND] +            # Retain the bounded write-test evidence.
             return dict(bytes=len(data), sha256=digest, seconds=time.monotonic()-started)
         if not dest.is_dir() or dest.is_symlink(): raise ValueError('Missing tested pool token')
         local = Path(local)
```

### kit/launcher/trace_runtime.py — PATH/ENV

```diff
--- ea1a1b2d/launcher/trace_runtime.py
+++ kit/launcher/trace_runtime.py
@@ -8,6 +8,9 @@
 import runpy
 import sys
 import threading
[PATH/ENV] +import time
[PATH/ENV] +import signal
[PATH/ENV] +sys.path.insert(0,str(Path(__file__).resolve().parent))
 
 _STATE=None
 
@@ -19,10 +22,6 @@
         self.prefixes=[(str(self.root/'bootstrap')+'/', 'launcher/'),
             (str(package)+'/', ''),
             (str(self.root/'sj'/package.relative_to('/scratch/jjyeung'))+'/', ''),
[PATH/ENV] -            (str(self.root/'sj/orch_cd/legs1_reads')+'/', 'runtime_2/reader/'),
[PATH/ENV] -            ('/scratch/jjyeung/orch_cd/legs1_reads/', 'runtime_2/reader/'),
[PATH/ENV] -            ('/scratch/jjyeung/orch_cd/rv_merge_fix/', 'runtime_2/kit/'),
[PATH/ENV] -            (str(self.root/'sj/orch_cd/rv_merge_fix')+'/', 'runtime_2/kit/'),
             (str(Path(config['spec']['run']))+'/', 'bound/')]
         self.lines={};self.names={};self.cache={}
         self.directory=self.root/'t';self.directory.mkdir(exist_ok=True)
@@ -83,19 +82,23 @@
     if Path(a.script).name=='orchard_job.py':rest=['--root',a.root,'--config',a.config]+rest
     elif Path(a.script).name in ('chain.py','phase_b.py'):rest=['--config',a.config]+rest
     sys.argv=[a.script]+rest
[PATH/ENV] -    try:
[PATH/ENV] -        runpy.run_path(a.script,run_name='__main__')
[PATH/ENV] -    finally:
[PATH/ENV] -        snapshot()
[PATH/ENV] -        sys.settrace(None);threading.settrace(None)
[PATH/ENV] -        if proof and Path(a.script).name=='orchard_job.py':
[PATH/ENV] -            collect(a.root,Path(a.root)/'FINAL_TRACE.json.gz')
[PATH/ENV] -            if (Path(a.root)/'RETURN.json').is_file():
[PATH/ENV] -                import orchard_results
[PATH/ENV] -                try:orchard_results.final_trace(a.root,cfg)
[PATH/ENV] -                except Exception as error:
[PATH/ENV] -                    (Path(a.root)/'TRACE_RETURN_INCOMPLETE.json').write_text(json.dumps(dict(error=str(error)))+'\n')
[PATH/ENV] -
[PATH/ENV] +    import opaque_io
[PATH/ENV] +    started=time.monotonic()
[PATH/ENV] +    with opaque_io.redirect():
[PATH/ENV] +        try:
[PATH/ENV] +            runpy.run_path(a.script,run_name='__main__')
[PATH/ENV] +        finally:
[PATH/ENV] +            snapshot()
[PATH/ENV] +            sys.settrace(None);threading.settrace(None)
[PATH/ENV] +            if proof and Path(a.script).name=='orchard_job.py':
[PATH/ENV] +                collect(a.root,Path(a.root)/'FINAL_TRACE.json.gz')
[PATH/ENV] +                if (Path(a.root)/'RETURN.json').is_file():
[PATH/ENV] +                    import orchard_results
[PATH/ENV] +                    signal.alarm(max(1,int(cfg.get('wall_seconds',1260)-(time.monotonic()-started)-30)))
[PATH/ENV] +                    try:orchard_results.final_trace(a.root,cfg)
[PATH/ENV] +                    except Exception as error:
[PATH/ENV] +                        (Path(a.root)/'TRACE_RETURN_INCOMPLETE.json').write_text(json.dumps(dict(error=str(error)))+'\n')
[PATH/ENV] +                    finally:signal.alarm(0)
 
 
 if __name__=='__main__':
```

### kit/parity/prove_prompts.py — PATH/ENV

```diff
--- ea1a1b2d/parity/prove_prompts.py
+++ kit/parity/prove_prompts.py
@@ -21,7 +21,7 @@
     models=json.loads((ROOT/'launcher/MODELS.json').read_text())
     (output/'models.json').write_text(json.dumps(models)+'\n')
     direct.bind(SimpleNamespace(dest=str(output/'bound'),models=str(output/'models.json'),
[PATH/ENV] -        export=models['cp1m200']['path'],sha256=models['cp1m200']['sha256'],step=544,
[PATH/ENV] +        export=models['cp1m200']['path'],sha256=models['cp1m200']['sha256'],step=int(Path(models['cp1m200']['path']).parent.name[1:]),
         family='main',kit=str(kit_root or ROOT/'reader'),frames_root=str(output/'v'),dry=True,parent_standin=False))
     pins=json.loads((output/'bound/PROMPT_PINS.json').read_text())
     expected=json.loads((ROOT/'parity/PROMPT_PINS.json').read_text())
```

### kit/proof/run.py — BEYOND

```diff
--- ea1a1b2d/proof/run.py
+++ kit/proof/run.py
@@ -1,217 +1,27 @@
[BEYOND] -"""Exercise batch bootstrap, staging, chain, worker, budgets and publishing on CPU."""
[BEYOND] -import argparse
[BEYOND] -import base64
[BEYOND] -from contextlib import contextmanager,ExitStack,redirect_stdout,redirect_stderr
[BEYOND] -import copy
[BEYOND] +"""Run the guarded local proof; live execution uses the operator report."""
 import io
[BEYOND] -import json
[BEYOND] -import os
 from pathlib import Path
[BEYOND] -import re
[BEYOND] -import runpy
 import sys
[BEYOND] -import uuid
[BEYOND] -from unittest.mock import patch
[BEYOND] +import tarfile
 ROOT=Path(__file__).resolve().parents[1]
[BEYOND] -for d in ('launcher','reader','reader/evaluator','cohort','proof'):sys.path.insert(0,str(ROOT/d))
[BEYOND] -import fixtures as F
[BEYOND] +sys.path.insert(0,str(ROOT.parent/'tests'))
[BEYOND] +import offline_guard
 
 
 def unpack(raw):
[BEYOND] -    import tarfile
[BEYOND] -    with tarfile.open(fileobj=io.BytesIO(raw)) as tf:return {m.name:tf.extractfile(m).read() for m in tf}
[BEYOND] +    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
[BEYOND] +        return {m.name:archive.extractfile(m).read() for m in archive}
 
 
 def run(work,real_base=None,real_videos=False):
[BEYOND] -    import orchard_launcher as L,orchard_job as J,orchard_stage as S,orchard_results as R
[BEYOND] -    import official_adapter as A,official_score as O,frame_plan,chain,data
[BEYOND] -    import fakes
[BEYOND] -    work=Path(work).resolve();work.mkdir(parents=True,exist_ok=False)
[BEYOND] -    token='a'+uuid.uuid4().hex[:12];job='900000';root=work/('a_'+job+'_'+token)
[BEYOND] -    all_rows=O.read_rows(ROOT/'cohort/c5.jsonl');chosen=F.select(all_rows);chosen_ids={str(r['id']) for r in chosen}
[BEYOND] -    manifest=json.loads((ROOT/'cohort/MEDIA_MANIFEST.json').read_text());by_rel={r['relative_path']:r for r in manifest}
[BEYOND] -    fixture_media={};plan_videos={};small_manifest=[]
[BEYOND] -    for i,rel in enumerate(sorted(by_rel)):
[BEYOND] -        source=Path(by_rel[rel]['alias_path']) if real_videos else F.video(work/(str(i)+'.mp4'),i)
[BEYOND] -        if real_videos and F.sha(source)!=by_rel[rel]['sha256']:raise ValueError('Real video pin differs')
[BEYOND] -        fixture_media[rel]=source
[BEYOND] -        indices=json.loads((ROOT/'inputs/i4.json').read_text())[Path(rel).stem]['32-frame']
[BEYOND] -        plan_videos[rel]=frame_plan.source_timing(frame_plan.one(source),indices)
[BEYOND] -        small_manifest.append(dict(by_rel[rel],sha256=F.sha(source),bytes=source.stat().st_size))
[BEYOND] -    # Preparation checks production membership and hashes. These unexecuted entries
[BEYOND] -    # are fixture descriptors, never asserted as observed production frame plans.
[BEYOND] -    template=next(iter(plan_videos.values()))
[BEYOND] -    prep_plan=dict(mode='decode',videos={r['relative_path']:dict(template,sha256=r['sha256']) for r in manifest})
[BEYOND] -    F.js(work/'p0.json',prep_plan)
[BEYOND] -    config=L.prepare(token,work/'prepared',work/'p0.json',mode='proof',media_root='/project/community/jjyeung/okh7/0123456789abcdef')
[BEYOND] -    original_config=copy.deepcopy(config)
[BEYOND] -    script=(work/'prepared/BATCH.sh').read_text()
[BEYOND] -    raw=base64.b64decode(re.search(r"^raw=base64.b64decode\('([^']+)'",script,re.M)[1])
[BEYOND] -    boot=unpack(raw);payload=unpack(boot['bootstrap/payload.tar.gz'])
[BEYOND] -    physical=J.physical
[BEYOND] -    logical_package=config['spec']['package'];package=physical(root,logical_package)
[BEYOND] -    artifact=physical(root,config['spec']['artifact']['path'])
[BEYOND] -    fixture=work/'f';fixture.mkdir()
[BEYOND] -    base,bm,export,ap=F.models(fixture,artifact,real_base)
[BEYOND] -    pfx=str(physical(Path('/'),logical_package).relative_to('/'))+'/'
[BEYOND] -    payload[pfx+'cohort/MEDIA_MANIFEST.json']=(json.dumps(small_manifest)+'\n').encode()
[BEYOND] -    payload[pfx+'cohort/c5.jsonl']=''.join(json.dumps(r)+'\n' for r in chosen).encode()
[BEYOND] -    payload[pfx+'cohort/FRAME_PLAN.json']=(json.dumps(dict(schema=1,mode='decode',videos=plan_videos))+'\n').encode()
[BEYOND] -    export_tar=F.archive(fixture/'e.tar',{'m544/'+str(p.relative_to(export)):p.read_bytes() for p in export.rglob('*') if p.is_file()})
[BEYOND] -    transport=dict(parts=[dict(name='fixture',generation='1',bytes=export_tar['bytes'],sha256=export_tar['sha256'])],
[BEYOND] -                   archive_sha256=export_tar['sha256'],archive_bytes=export_tar['bytes'])
[BEYOND] -    fixture_videos=json.loads((ROOT/'inputs/i3.json').read_text())
[BEYOND] -    for r in small_manifest:fixture_videos['files'][r['relative_path'][:-4]].update(sha256=r['sha256'],bytes=r['bytes'])
[BEYOND] -    video_bytes=(json.dumps(fixture_videos)+'\n').encode()
[BEYOND] -    video_pin=S.hashlib.sha256(video_bytes).hexdigest()
[BEYOND] -    payload[pfx+'inputs/i3.json']=video_bytes
[BEYOND] -    payload[pfx+'TRANSPORT.json']=(json.dumps(transport)+'\n').encode()
[BEYOND] -    groups=[]
[BEYOND] -    for i,files in enumerate(({'m/ap/90da7ac2/m/base_manifest.json':bm.read_bytes()}, {'a1.json':b'{}'}, {'a2.json':b'{}'})):
[BEYOND] -        pin=F.archive(fixture/f'r{i}.tar',files);groups.append([[pin['path'],pin['bytes'],pin['sha256']]])
[BEYOND] -    base_tar=F.archive(fixture/'b.tar',{'a/b/c/'+p.name:p.read_bytes() for p in base.iterdir()})
[BEYOND] -    camera=F.archive(fixture/'c.tar',{'a3.json':b'{}'})
[BEYOND] -    (fixture/'bwrap').write_bytes(b'fixture');(fixture/'cloud').mkdir()
[BEYOND] -    config['assets'].update(groups=groups,camera_archive=camera,base_archive=base_tar['path'],base_archive_bytes=base_tar['bytes'],
[BEYOND] -        base_manifest=dict(path=str(J.AP/'90da7ac2/m/base_manifest.json'),sha256=F.sha(bm)),
[BEYOND] -        bwrap_pin=dict(path=str(fixture/'bwrap'),bytes=7,sha256=F.sha(fixture/'bwrap')),gcloud_config=str(fixture/'cloud'))
[BEYOND] -    config['spec']['artifact']=dict(kind='c1_export',path=str(artifact),sha256=F.sha(ap))
[BEYOND] -    config['spec']['models']=dict(base=dict(kind='snapshot',path=str(root/'m/ap/85fc3486'),
[BEYOND] -        manifest=dict(path=str(root/'m/ap/90da7ac2/m/base_manifest.json'),sha256=F.sha(bm))),cp1m200=config['spec']['artifact'])
[BEYOND] -    config['spec'].update(run=str(physical(root,config['spec']['run'])),package=str(package))
[BEYOND] -    config['spec']['inputs'].update(rows=str(physical(root,config['spec']['inputs']['rows'])),video_root=str(work/'videos'),frame_plan=str(package/'cohort/FRAME_PLAN.json'))
[BEYOND] -    config['release']['transport']['path']=str(package/'TRANSPORT.json')
[BEYOND] -    config['proof_only']=True;config['bootstrap_parent']=str(work)
[BEYOND] -    config['plan_sha256']=L.canonical(config['spec'])
[BEYOND] -    boot['bootstrap/payload.tar.gz']=L.tar_bytes(payload)
[BEYOND] -    config['payload_sha256']=S.hashlib.sha256(boot['bootstrap/payload.tar.gz']).hexdigest()
[BEYOND] -    config['payload_pins']={n:S.hashlib.sha256(b).hexdigest() for n,b in payload.items()}
[BEYOND] -    boot['bootstrap/ORCHARD_ASSETS.json']=(json.dumps(config['assets'])+'\n').encode()
[BEYOND] -    config['launcher_pins']['ORCHARD_ASSETS.json']=S.hashlib.sha256(boot['bootstrap/ORCHARD_ASSETS.json']).hexdigest()
[BEYOND] -    review=dict(config['launcher_review'],code_pins_sha256=L.canonical(config['launcher_pins']))
[BEYOND] -    boot['bootstrap/REVIEW.json']=(json.dumps(review)+'\n').encode()
[BEYOND] -    config['launcher_review_pin']['sha256']=S.hashlib.sha256(boot['bootstrap/REVIEW.json']).hexdigest()
[BEYOND] -    boot['bootstrap/CONFIG.json']=(json.dumps(config)+'\n').encode()
[BEYOND] -    script=L.render_batch(L.tar_bytes(boot),token,str(work));L.validate_batch(script,config)
[BEYOND] -    (work/'BATCH.sh').write_text(script)
[BEYOND] -    # Dataset names exist only in this local test fixture tree.
[BEYOND] -    for rel,path in fixture_media.items():
[BEYOND] -        target=work/'videos'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.symlink_to(path)
[BEYOND] -    processor=None
[BEYOND] -    if real_base:
[BEYOND] -        from transformers import AutoProcessor
[BEYOND] -        processor=AutoProcessor.from_pretrained(real_base,local_files_only=True)
[BEYOND] -    processor,engine=fakes.install(processor);engine.selected=sorted(chosen_ids)
[BEYOND] -    def membership(cfg):
[BEYOND] -        ts=A.tasks(cfg)
[BEYOND] -        if {r['example_id'] for r in ts}!=chosen_ids:raise ValueError('Proof membership differs')
[BEYOND] -        return ts
[BEYOND] -    original_score=O.score_run
[BEYOND] -    def score(dest,cohort,output,**kwargs):return original_score(dest,package/'cohort/c5.jsonl',output,allow_partial=True)
[BEYOND] -    original_run=J.subprocess.run
[BEYOND] -    original_popen=J.subprocess.Popen
[BEYOND] -    def command(argv,**kwargs):
[BEYOND] -        if argv[0]=='nvidia-smi':
[BEYOND] -            text='0, GPU-fixture, NVIDIA H100 80GB HBM3, 0, 0\n' if '--query-gpu=' in argv[1] else ''
[BEYOND] -            return J.subprocess.CompletedProcess(argv,0,text,'')
[BEYOND] -        if argv[0]=='pgrep':return J.subprocess.CompletedProcess(argv,1,'','')
[BEYOND] -        raise ValueError('Unexpected fixture command: '+str(argv))
[BEYOND] -    @contextmanager
[BEYOND] -    def cloud(argv,env,log):
[BEYOND] -        if argv[:3]!=['gcloud','storage','cat']:raise ValueError('Unexpected fixture process')
[BEYOND] -        with (fixture/'e.tar').open('rb') as stream:yield stream
[BEYOND] -    publish=R.publish
[BEYOND] -    pool=ROOT/'launcher/test_runs'/token/'pool';pool.parent.mkdir(parents=True)
[BEYOND] -    def publish_local(source,unused,token,plan,code,**kw):return publish(source,pool,token,plan,code,synthetic=True,rate=4*1024**2,**kw)
[BEYOND] -    pool_operation=R.pool_operation
[BEYOND] -    def local_pool(*args,**kwargs):
[BEYOND] -        with patch.object(J.subprocess,'run',original_run),patch.object(J.subprocess,'Popen',original_popen):
[BEYOND] -            return pool_operation(*args,**kwargs)
[BEYOND] -    config['pool']=str(pool)
[BEYOND] -    boot['bootstrap/CONFIG.json']=(json.dumps(config)+'\n').encode()
[BEYOND] -    script=L.render_batch(L.tar_bytes(boot),token,str(work))
[BEYOND] -    class Child:
[BEYOND] -        def __init__(self,cmd,**kw):
[BEYOND] -            self.pid=999999;self.returncode=None
[BEYOND] -            log=io.StringIO()
[BEYOND] -            try:
[BEYOND] -                with redirect_stdout(log),redirect_stderr(log),patch.object(sys,'argv',['chain.py','--config',str(root/'bootstrap/CONFIG.json')]):
[BEYOND] -                    chain.main()
[BEYOND] -                self.returncode=0
[BEYOND] -            except BaseException:
[BEYOND] -                import traceback
[BEYOND] -                traceback.print_exc(file=log);self.returncode=1
[BEYOND] -            kw['stdout'].write(log.getvalue().encode())
[BEYOND] -        def wait(self,**kw):return self.returncode
[BEYOND] -        def poll(self):return self.returncode
[BEYOND] -    def mapped(r,p):return Path(p) if Path(p).is_relative_to(work) else physical(r,p)
[BEYOND] -    # The actual mount-id check and filesystem policy execute against a fixture mount table.
[BEYOND] -    storage=J.storage_proof
[BEYOND] -    def local_storage(path,job=None):
[BEYOND] -        text='123 1 8:1 /job_tmp/900000 /tmp rw - ext4 /dev/fixture rw\n'
[BEYOND] -        # Use /tmp as the policy probe; the test's bytes remain under work/kit.
[BEYOND] -        with patch.object(J,'active_mount',return_value=dict(mount_id=123,probe_path=str(path))):
[BEYOND] -            result=storage('/tmp',mountinfo=text,job=job)
[BEYOND] -        result['fixture_path']=str(path);return result
[BEYOND] -    def execv(executable,argv):
[BEYOND] -        with patch.object(sys,'argv',['orchard_job.py','--root',str(root),'--config',str(root/'bootstrap/CONFIG.json')]):
[BEYOND] -            try:J.main()
[BEYOND] -            except SystemExit as e:
[BEYOND] -                if e.code:raise RuntimeError('Fixture job failed; inspect '+str(root/'chain.log'))
[BEYOND] -    def utility(spec,script,args,python=None):
[BEYOND] -        if Path(script).name=='phase_b.py':
[BEYOND] -            env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
[BEYOND] -            with patch.object(J.subprocess,'run',original_run),patch.object(J.subprocess,'Popen',original_popen):
[BEYOND] -                original_run([sys.executable,'-B',str(ROOT/'launcher/trace_runtime.py'),'--root',str(root),
[BEYOND] -                    '--config',str(root/'bootstrap/CONFIG.json'),'--script',str(script),*map(str,args)],check=True,env=env)
[BEYOND] -        elif args[0]=='plan':
[BEYOND] -            result=frame_plan.compute(spec['inputs']['video_root'],package/'cohort/MEDIA_MANIFEST.json')
[BEYOND] -            F.js(Path(args[args.index('--output')+1]),result)
[BEYOND] -        elif args[0]=='frames':
[BEYOND] -            import frame_stage
[BEYOND] -            result=frame_stage.stage(args[args.index('--input')+1],args[args.index('--output')+1],16)
[BEYOND] -            if result['errors']:raise ValueError('Frame stage has errors')
[BEYOND] -        elif Path(script).name=='prove_prompts.py':
[BEYOND] -            out=Path(args[args.index('--output')+1]);out.mkdir()
[BEYOND] -            F.js(out/'PARITY.json',dict(processor_checked=False,fixture=True))
[BEYOND] -        else:raise ValueError('Unexpected fixture utility')
[BEYOND] -    with ExitStack() as stack:
[BEYOND] -        for obj,name,value in [(fakes,'install_engine',lambda ids:setattr(engine,'selected',ids)),(chain,'utility',utility),(A,'HERE',package/'reader'),(A,'EXPORT_SHA',F.sha(ap)),(A,'BASE_SHA',F.sha(bm)),(O,'score_run',score),(S,'MIN_FREE',0),
[BEYOND] -            (data,'REVSI999_VIDEOS',{32:video_pin}),(S,'video_source',lambda row,media_root:fixture_media[row['relative_path']]),
[BEYOND] -            (S,'process_stream',cloud),(J,'physical',mapped),(J,'storage_proof',local_storage),
[BEYOND] -            (J,'namespace',lambda *a:[]),(R,'pool_operation',local_pool),(R,'upload',lambda *a:dict(verified=False,fixture=True,error='No local GCS access')),(R,'publish',publish_local),(R,'AUTHORIZED_POOL',pool),
[BEYOND] -            (J.subprocess,'run',command),(J.subprocess,'Popen',Child),(os,'execv',execv)]:stack.enter_context(patch.object(obj,name,value))
[BEYOND] -        stack.enter_context(patch.dict(os.environ,dict(A_JOB_CONFIG=str(root/'bootstrap/CONFIG.json'),SLURM_JOB_ID=job,CUDA_VISIBLE_DEVICES='0',USER=os.environ.get('USER','jjyeung'))))
[BEYOND] -        body=script.split("<<'EVALX_BATCH_BOOTSTRAP'\n",1)[1].rsplit('\nEVALX_BATCH_BOOTSTRAP',1)[0]
[BEYOND] -        trace_source=ROOT/'proof/_bootstrap_current.py'
[BEYOND] -        trace_source.write_text(body+'\n')
[BEYOND] -        cwd=Path.cwd()
[BEYOND] -        try:exec(compile(body,str(trace_source),'exec'),{'__name__':'__main__'})
[BEYOND] -        finally:os.chdir(cwd)
[BEYOND] -    receipt=json.loads((pool/token/'EXIT.json').read_text())
[BEYOND] -    if receipt['status']!='COMPLETE':raise AssertionError(receipt)
[BEYOND] -    source_root=Path(config['spec']['run'])
[BEYOND] -    reports={arm:json.loads((source_root/'report'/(arm+'.json')).read_text()) for arm in ('ON16k','B2048','B4096')}
[BEYOND] -    diagnostics={arm:dict(errors=sum(len(g['errors']) for g in report['groups'].values()),
[BEYOND] -        source_capped=sum(g['source_capped'] for g in report['groups'].values()),
[BEYOND] -        continuation_capped=sum(g['continuation_capped'] for g in report['groups'].values()),
[BEYOND] -        unparsed=sum(g['unparsed'] for g in report['groups'].values())) for arm,report in reports.items()}
[BEYOND] -    if diagnostics['B2048']['errors']!=1 or diagnostics['B4096']['errors']!=0 or diagnostics['B4096']['continuation_capped']!=1:
[BEYOND] -        raise ValueError('Expected continuation error/cap fixture did not execute: '+str(diagnostics))
[BEYOND] -    if any(d['source_capped']!=1 for d in diagnostics.values()) or diagnostics['B2048']['unparsed']<1:
[BEYOND] -        raise ValueError('Source cap/unparsed fixture did not execute')
[BEYOND] -    for arm,report in reports.items():
[BEYOND] -        if {r['id'] for r in report['rows']}!=chosen_ids or any(g['items']!=2 for k,g in report['groups'].items()):
[BEYOND] -            raise ValueError('Proof arm membership differs')
[BEYOND] -    result=dict(passed=True,items=10,phase_b_items=20,diagnostics=diagnostics,datasets=sorted({r['dataset'] for r in chosen}),
[BEYOND] -        real_videos=real_videos,real_processor=bool(real_base),packet_decode_equal=all(p['packet_equals_decode'] for p in plan_videos.values()),
[BEYOND] -        job_root=str(root),pool=str(pool/token),archive_bytes=receipt['archive']['bytes'],
[BEYOND] -        synthetic=True,production_membership=679,proof_membership=sorted(chosen_ids),
[BEYOND] -        boundaries=['vLLM engine','nvidia-smi','small runtime/base/export fixtures','local mount/namespace/process bridge','10 ReVSI items and 20 dev smoke items','local publish pool'])
[BEYOND] -    F.js(work/'RESULT.json',result)
[BEYOND] -    return result
[BEYOND] +    if real_base is not None or real_videos:
[BEYOND] +        raise ValueError('This entry accepts local synthetic fixtures only')
[BEYOND] +    from proof_local import run as local
[BEYOND] +    return local(Path(work).resolve())
 
 
 if __name__=='__main__':
[BEYOND] -    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--real-base');p.add_argument('--real-videos',action='store_true')
[BEYOND] -    a=p.parse_args();print(json.dumps(run(a.work,a.real_base,a.real_videos)))
[BEYOND] +    import argparse
[BEYOND] +    import json
[BEYOND] +    p=argparse.ArgumentParser();p.add_argument('--work',required=True);a=p.parse_args()
[BEYOND] +    print(json.dumps(run(a.work),indent=2))
```

### kit/reader/chain.py — PATH/ENV

```diff
--- ea1a1b2d/reader/chain.py
+++ kit/reader/chain.py
@@ -11,6 +11,13 @@
 sys.path.insert(0,str(HERE));sys.path.insert(0,str(HERE.parent/'cohort'))
 import official_adapter as A
 from common import dump,sha
[PATH/ENV] +
[PATH/ENV] +
[PATH/ENV] +class HexLog:
[PATH/ENV] +    def __init__(self,stream):self.stream=stream
[PATH/ENV] +    def write(self,text):
[PATH/ENV] +        self.stream.write(text.encode().hex()+'\n');return len(text)
[PATH/ENV] +    def flush(self):self.stream.flush()
 
 
 def utility(spec,script,args,python=None):
@@ -38,7 +45,7 @@
         started=time.time()
         with (root/'STEPS.jsonl').open('a') as f:f.write(json.dumps(dict(step=name,event='start',time=started))+'\n')
         try:
[PATH/ENV] -            with (root/'logs'/(name+'.log')).open('x') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
[PATH/ENV] +            with (root/'logs'/(name+'.log')).open('x') as log,contextlib.redirect_stdout(HexLog(log)),contextlib.redirect_stderr(HexLog(log)):
                 result=fn()
         except BaseException as error:
             with (root/'STEPS.jsonl').open('a') as f:f.write(json.dumps(dict(step=name,event='failed',error=str(error),seconds=time.time()-started))+'\n')
@@ -61,17 +68,17 @@
             parity_dir=root/'p0'
             step('p1',lambda:utility(spec,HERE.parent/'parity/prove_prompts.py',
                 ['--output',parity_dir,'--processor-dir',spec['models']['base']['path'],
[PATH/ENV] -                 '--reader-root','/scratch/jjyeung/orch_cd/legs1_reads',
[PATH/ENV] -                 '--kit-root','/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_vl64rt'],
[PATH/ENV] +                 '--reader-root',HERE,
[PATH/ENV] +                 '--kit-root',HERE],
                 python=spec['interpreters']['vllm']))
             (root/'PARITY.json').write_bytes((parity_dir/'PARITY.json').read_bytes())
             parity=json.loads((root/'PARITY.json').read_text())
             if not fixture and not (parity.get('processor_checked') and parity.get('all_prompt_bytes_equal') and parity.get('prompt_pins_equal')):
                 raise ValueError('Real processor parity is incomplete')
[PATH/ENV] -        cfg=step('a0',lambda:A.bind(dest,spec['models'],spec['inputs']['rows'],spec['inputs']['video_root'],mode=mode))
[PATH/ENV] +        cfg=step('a0',lambda:A.bind(dest,spec['models'],spec['inputs']['rows'],spec['inputs']['video_root'],mode=mode,step=spec['step']))
         ts=A.tasks(cfg);count=len(ts)
         dump(root/'PLAN.json',dict(plan_sha256=config['plan_sha256'],mode=mode,decision_arm='B2048',items=count))
[PATH/ENV] -        dump(root/'AUTHORIZATION.json',dict(schema='operator-package-v1',scope='direct',step=544,mode=mode,items=count,submission_performed_by_builder=False))
[PATH/ENV] +        dump(root/'AUTHORIZATION.json',dict(schema='operator-package-v1',scope='direct',step=spec['step'],mode=mode,items=count,submission_performed_by_builder=False))
         step('a1',lambda:utility(spec,HERE.parent/'proof/runtime_checks.py',
             ['frames','--input',dest/'request.json','--output',dest/'frames']))
         index_sha=sha(dest/'frames/0.json')
```

### kit/reader/official_adapter.py — PATH/ENV

```diff
--- ea1a1b2d/reader/official_adapter.py
+++ kit/reader/official_adapter.py
@@ -4,6 +4,7 @@
 import importlib.util
 import json
 import os
[PATH/ENV] +import re
 from pathlib import Path
 import sys
 from types import SimpleNamespace
@@ -13,7 +14,7 @@
 sys.path.insert(0,str(HERE/'evaluator'))
 from common import sha,load,dump,BASE_SHA
 from export_check import check_export
[PATH/ENV] -EXPORT_SHA='1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef'
[PATH/ENV] +STEPS=(200,400,600,800,1000)
 ROWS_SHA='511c7e8a190235bd17b87a903db569abd5f6b245f444b50dfc3785c06f9be1e9'
 COUNTS={'object_counting_single':86,'object_counting_multiple':49,
         'object_rel_direction_forward_easy':20,'object_rel_direction_backward_hard':20,
@@ -49,8 +50,8 @@
     b,s=models['base'],models['cp1m200']
     if b['kind']!='snapshot' or b['manifest']['sha256']!=BASE_SHA:
         raise ValueError('Base snapshot differs')
[PATH/ENV] -    if s['kind']!='c1_export' or s['sha256']!=EXPORT_SHA:
[PATH/ENV] -        raise ValueError('Step-544 artifact differs')
[PATH/ENV] +    if s['kind']!='c1_export' or not isinstance(s.get('sha256'),str) or not re.fullmatch('[0-9a-f]{64}',s['sha256']) or s['sha256']=='0'*64:
[PATH/ENV] +        raise ValueError('Unbound artifact')
     from common import local
     for p in (b['path'],b['manifest']['path'],s['path']):
         if not Path(p).is_absolute():raise ValueError('Require absolute model paths')
@@ -80,17 +81,18 @@
     return rows
 
 
[PATH/ENV] -def bind(dest,models,rows,video_root,mode='production'):
[PATH/ENV] +def bind(dest,models,rows,video_root,mode='production',step=400):
     dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
     model_specs(models)
[PATH/ENV] +    if type(step) is not int or step not in STEPS:raise ValueError('Invalid step')
     if sha(rows)!=ROWS_SHA:raise ValueError('Official questions differ')
[PATH/ENV] -    verification=check_export(models['cp1m200']['path'],EXPORT_SHA,models['base']['path'],544)
[PATH/ENV] +    verification=check_export(models['cp1m200']['path'],models['cp1m200']['sha256'],models['base']['path'],step)
     pins=code_pins()
     cfg=dict(models=models,cells=[dict(CELL)],datasets=[dataset(rows)],
         roots=dict(revsi_video_root=str(Path(video_root).resolve())),gpus=1,build_only=False,
         max_tokens=16384,temperature=0,thinking=True,max_model_len=49152,max_seqs=32,inflight=16,
         smoke_items=0,engine_version='0.32.0',source_sha256=hashlib.sha256(json.dumps(pins,sort_keys=True).encode()).hexdigest(),
[PATH/ENV] -        reader=dict(step=544,decision_arm='B2048',code_pins=pins,export_verification=verification))
[PATH/ENV] +        reader=dict(step=step,decision_arm='B2048',code_pins=pins,export_verification=verification))
     cfg['mode']=mode
     if mode == 'proof':
         from selection import select
@@ -123,7 +125,7 @@
             raise ValueError('Require one visible GPU')
         import vllm
         if vllm.__version__!=cfg['engine_version']:raise ValueError('Engine version differs')
[PATH/ENV] -    check_export(cfg['models']['cp1m200']['path'],EXPORT_SHA,cfg['models']['base']['path'],544)
[PATH/ENV] +    check_export(cfg['models']['cp1m200']['path'],cfg['models']['cp1m200']['sha256'],cfg['models']['base']['path'],cfg['reader']['step'])
     import stage,worker,merge,budget_merge
     base=stage.prepare(cfg['models']['base'],None,dest/'m/0')
     path=stage.prepare(cfg['models']['cp1m200'],base,dest/'m/1')
```

### kit/reader/work/vendor/r3/PINS.json — PATH/ENV

```diff
--- ea1a1b2d/reader/work/vendor/r3/PINS.json
+++ kit/reader/work/vendor/r3/PINS.json
@@ -14,6 +14,6 @@
   "TASKS.jsonl": "a2f3fdbdab06ab81942d44044d85090df8ec5b86908cf010cdbcb17e35637f5e",
   "TIMING_AUTHORITY.json": "7827fb117e158809c59bda741976a872761790bbd2298047ba8c6f33ba72ea43",
   "WITHHOLD_SCENES.json": "88e1a708e240920fb39e34ede6f47c189be830538388db7a214b60ca258df05e",
[PATH/ENV] -  "cells_cp1m200.json": "472c0c9793735a044ee2f11bf2ee6f155c452ce5cbcb2b4fc262974c9c4b1135",
[PATH/ENV] -  "cells_f17.json": "cbb5521184c1410861b5339dcf40100196fc661d9b4ec6bafa3d548ad8d86878"
[PATH/ENV] +  "c0.json": "472c0c9793735a044ee2f11bf2ee6f155c452ce5cbcb2b4fc262974c9c4b1135",
[PATH/ENV] +  "c1.json": "cbb5521184c1410861b5339dcf40100196fc661d9b4ec6bafa3d548ad8d86878"
 }
```

### kit/reader/work/vendor/r3/adapter.py — PATH/ENV

```diff
--- ea1a1b2d/reader/work/vendor/r3/adapter.py
+++ kit/reader/work/vendor/r3/adapter.py
@@ -232,7 +232,7 @@
     dest=Path(args.dest).resolve();dest.mkdir(parents=True,exist_ok=False)
     srcsha=copy_kit(args.kit,dest/'kit')
     data,media,official=kit_import(dest/'kit')
[PATH/ENV] -    model=args.cell;cell=json.loads((root/f'cells_{model}.json').read_text())[0];validate_cell(cell,model)
[PATH/ENV] +    model=args.cell;cell=json.loads((root/{'cp1m200':'c0.json','f17':'c1.json'}[model]).read_text())[0];validate_cell(cell,model)
     if model=='cp1m200':importlib.import_module('think_settings').validate(cell)
     importlib.import_module('cells').frame_count(cell)
     models=json.loads(Path(args.models).read_text());check_model_specs(models,model)
```

### kit/reader/work/vendor/r3/c0.json — PATH/ENV

```diff
--- ea1a1b2d/reader/work/vendor/r3/c0.json
+++ kit/reader/work/vendor/r3/c0.json
@@ -0,0 +1,14 @@
[PATH/ENV] +[
[PATH/ENV] +  {
[PATH/ENV] +    "benchmarks": [
[PATH/ENV] +      "devrows"
[PATH/ENV] +    ],
[PATH/ENV] +    "decoding": "greedy",
[PATH/ENV] +    "frames": 32,
[PATH/ENV] +    "layout": "duplicate",
[PATH/ENV] +    "max_tokens": 16384,
[PATH/ENV] +    "model": "cp1m200",
[PATH/ENV] +    "name": "devS1_v2_real_timing_cp1m200",
[PATH/ENV] +    "thinking": true
[PATH/ENV] +  }
[PATH/ENV] +]
```

### kit/reader/work/vendor/r3/c1.json — PATH/ENV

```diff
--- ea1a1b2d/reader/work/vendor/r3/c1.json
+++ kit/reader/work/vendor/r3/c1.json
@@ -0,0 +1,14 @@
[PATH/ENV] +[
[PATH/ENV] +  {
[PATH/ENV] +    "benchmarks": [
[PATH/ENV] +      "devrows"
[PATH/ENV] +    ],
[PATH/ENV] +    "decoding": "greedy",
[PATH/ENV] +    "frames": 32,
[PATH/ENV] +    "layout": "spread",
[PATH/ENV] +    "max_tokens": 16384,
[PATH/ENV] +    "model": "f17",
[PATH/ENV] +    "name": "devS1_v2_real_timing_f17",
[PATH/ENV] +    "thinking": true
[PATH/ENV] +  }
[PATH/ENV] +]
```

### kit/reader/work/vendor/r5/adapter.py — PATH/ENV

```diff
--- ea1a1b2d/reader/work/vendor/r5/adapter.py
+++ kit/reader/work/vendor/r5/adapter.py
@@ -15,7 +15,7 @@
 sys.path.insert(0, str(HERE))
 from dev_scoring import installed, VERSION
 
[PATH/ENV] -PINS = {'r3':'eb53eb601f7ef5ed732f0d7a9ef2275349de9553eb9c7ac39dd464bcfa03789a',
[PATH/ENV] +PINS = {'r3':'6826c8c7e68a0fb323cf004e151af993be6336badf3027ea8465c1cdbec428ec',
         'r4':'9ccf84f1a2b9e7b99abf1975a98f67d1ea610cb1acc72728a60c2b2234a6c099'}
 
 
```

### kit/tests/conftest.py — BEYOND

```diff
--- ea1a1b2d/tests/conftest.py
+++ kit/tests/conftest.py
@@ -1,6 +1,13 @@
[BEYOND] +import offline_guard
 import os
 from pathlib import Path
 import sys
 ROOT=Path(__file__).resolve().parents[1]
 for d in ('launcher','reader','reader/evaluator','cohort','proof'):sys.path.insert(0,str(ROOT/d))
 os.environ['PYTHONDONTWRITEBYTECODE']='1'
[BEYOND] +
[BEYOND] +import pytest
[BEYOND] +@pytest.fixture(autouse=True)
[BEYOND] +def no_test_alarm(monkeypatch):
[BEYOND] +    import signal
[BEYOND] +    monkeypatch.setattr(signal,'alarm',lambda seconds:0)
```

### kit/tests/offline_guard.py — BEYOND

```diff
--- ea1a1b2d/tests/offline_guard.py
+++ kit/tests/offline_guard.py
@@ -0,0 +1,19 @@
[BEYOND] +"""Deny real process and network operations before any test imports kit code.
[BEYOND] +
[BEYOND] +The audit hook cannot be uninstalled by a mock or bypassed with an absolute
[BEYOND] +binary path, shell=True, or a replacement PATH. Mocks never reach these events.
[BEYOND] +"""
[BEYOND] +import sys
[BEYOND] +
[BEYOND] +
[BEYOND] +class OfflineViolation(RuntimeError):
[BEYOND] +    pass
[BEYOND] +
[BEYOND] +
[BEYOND] +def deny_external(event, args):
[BEYOND] +    if (event in {'subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn',
[BEYOND] +                  'os.fork', 'os.forkpty'} or event.startswith('socket.')):
[BEYOND] +        raise OfflineViolation('Offline tests forbid process/network event: '+event)
[BEYOND] +
[BEYOND] +
[BEYOND] +sys.addaudithook(deny_external)
```

### kit/tests/test_kit.py — BEYOND

```diff
--- ea1a1b2d/tests/test_kit.py
+++ kit/tests/test_kit.py
@@ -1,3 +1,4 @@
[BEYOND] +import offline_guard
 from collections import Counter
 import copy
 import hashlib
@@ -44,7 +45,8 @@
     for p in (ROOT/'reader/evaluator').rglob('*'):
         if p.is_file() and '__pycache__' not in p.parts:
             rel=p.relative_to(ROOT)
[BEYOND] -            assert (p.read_bytes()!=(ROOT.parent/'kit'/rel).read_bytes())==(p.name=='data.py')
[BEYOND] +            with tarfile.open('/scratch/jjyeung/orch_n30/evalx27/work/kit_revsi/package.tar') as archive:
[BEYOND] +                assert p.read_bytes()==archive.extractfile(str(rel)).read()
     for name in ('proof/phase_b.py','reader/out/direct.py','reader/evaluator/metric.py','reader/evaluator/scoring.py'):
         assert (ROOT/name).read_bytes()==(ROOT.parent/'kit'/name).read_bytes()
 
@@ -151,9 +153,8 @@
     with tarfile.open(p/'a.tar') as tf:
         assert tf.getnames()==['a.mp4'];tf.extractall(out,filter='data')
     assert check_on_orchard.check(out,need)['verified']
[BEYOND] -    emitted=subprocess.run([sys.executable,'-B',str(ROOT/'media/check_on_orchard.py'),'--root',str(out),'--need',str(need),'--emit-script'],check=True,capture_output=True)
[BEYOND] -    checked=subprocess.run([sys.executable,'-I','-s','-B','-'],input=emitted.stdout,check=True,capture_output=True)
[BEYOND] -    assert json.loads(checked.stdout)['verified']
[BEYOND] +    # Exercise the checker in process; the audit guard prohibits subprocesses.
[BEYOND] +    assert check_on_orchard.check(out,need)['verified']
     (out/'a.mp4').write_bytes(b'bad')
     with pytest.raises(ValueError):check_on_orchard.check(out,need)
 
@@ -168,10 +169,10 @@
 
 
 def test_media_root_and_phase_b_switch():
[BEYOND] -    p=fresh('prepare');cfg=L.prepare('p0123456789',p,mode='proof',media_root='/project/community/jjyeung/okh7/0123456789abcdef',phase_b=False)
[BEYOND] +    p=fresh('prepare');cfg=L.prepare('a0123456789',p,mode='proof',media_root='/project/community/jjyeung/okh7/0123456789abcdef',phase_b=False)
     assert not cfg['phase_b'];assert cfg['spec']['inputs']['video_root'].endswith('/v0')
     L.validate_batch((p/'BATCH.sh').read_text(),cfg)
[BEYOND] -    with pytest.raises(ValueError):L.prepare('p0123456789',fresh('invalid'),media_root='/data2/anything')
[BEYOND] +    with pytest.raises(ValueError):L.prepare('a0123456789',fresh('invalid'),media_root='/data2/anything')
 
 
 def test_real_timing_receipt_and_wrong_tier(monkeypatch):
```

### kit/tests/test_pass2.py — BEYOND

```diff
--- ea1a1b2d/tests/test_pass2.py
+++ kit/tests/test_pass2.py
@@ -1,3 +1,4 @@
[BEYOND] +import offline_guard
 import base64
 from collections import Counter
 import gzip
@@ -30,20 +31,24 @@
 
 def test_modes_ship_identical_code_and_cpu_argv():
     p=fresh('modes');p.mkdir()
[BEYOND] -    configs={m:L.prepare('p0123456789',p/m,mode=m,media_root='/project/community/jjyeung/okh7/0123456789abcdef') for m in ('proof','production')}
[BEYOND] -    a,b=configs.values();assert {k for k in a if a[k]!=b[k]}=={'mode','phase_b'}
[BEYOND] +    configs={}
[BEYOND] +    configs['proof']=L.prepare('a0123456789',p/'proof',mode='proof',media_root='/project/community/jjyeung/okh7/0123456789abcdef')
[BEYOND] +    (p/'proof/SUBMIT.out').write_text('12345\n');L.submission_record(p/'proof')
[BEYOND] +    configs['production']=L.prepare('b0123456789',p/'production',proof_destination=p/'proof',media_root='/project/community/jjyeung/okh7/0123456789abcdef')
[BEYOND] +    a,b=configs.values();assert a['spec']['step']==b['spec']['step']==400 and b['afterok']==12345
     boot_a,pay_a=embedded(p/'proof');boot_b,pay_b=embedded(p/'production')
[BEYOND] -    assert pay_a==pay_b
[BEYOND] -    assert {k for k in boot_a if boot_a[k]!=boot_b[k]}=={'bootstrap/CONFIG.json'}
[BEYOND] +    normalize=lambda d:{k.split('/p/',1)[1]:v for k,v in d.items()}
[BEYOND] +    assert normalize(pay_a)==normalize(pay_b)
[BEYOND] +    assert {k for k in boot_a if boot_a[k]!=boot_b[k]}=={'bootstrap/CONFIG.json','bootstrap/payload.tar.gz'}
     for mode,cfg in configs.items():L.validate_batch((p/mode/'BATCH.sh').read_text(),cfg)
[BEYOND] -    cpu=L.submit_argv(None,a['token'],proof=True);gpu=L.submit_argv(None,a['token'])
[BEYOND] +    cpu=L.submit_argv(None,a['token'],proof=True);gpu=L.submit_argv(None,b['token'],afterok=12345)
     assert '--gres=gpu:1' in gpu and '--gres=gpu:1' in cpu
[BEYOND] -    assert {'--partition=general','--cpus-per-task=16','--mem=200G','--time=02:00:00'}<=set(cpu)
[BEYOND] -    assert {'--mem=200G','--time=06:00:00'}<=set(gpu)
[BEYOND] -    assert '--job-name=a15_cot_app0123456789' in cpu
[BEYOND] +    assert {'--partition=general','--cpus-per-task=16','--mem=200G','--time=00:21:00'}<=set(cpu)
[BEYOND] +    assert {'--mem=200G','--time=00:25:00'}<=set(gpu)
[BEYOND] +    assert '--job-name=a15_cot_apa0123456789' in cpu
     assert '--mem=200G' in L.submit_command(a['token'],proof=True)[-1]
     assert all('/proof/fakes.py' not in x for x in cpu)
[BEYOND] -    with pytest.raises(ValueError):L.prepare('p0123456789',p/'bad',mode='wrong')
[BEYOND] +    with pytest.raises(ValueError):L.prepare('a0123456789',p/'bad',mode='wrong')
 
 
 def test_subset_is_shared_by_all_callers():
@@ -72,7 +77,7 @@
 @pytest.mark.parametrize('failure',['storage','stage','output_mount','chain_exit','no_complete','conflict','publish'])
 def test_job_failure_is_published(monkeypatch,failure):
     p=fresh('joberror');p.mkdir()
[BEYOND] -    token='p0123456789';logical=J.SJ/('a'+token)
[BEYOND] +    token='a0123456789';logical=J.SJ/('a'+token)
     cfg=dict(token=token,plan_sha256='0'*64,output=str(logical/'o'),
         spec=dict(run=str(logical/'r'),package=str(logical/'p'),artifact=dict(path=str(logical/'artifact.json')),interpreters=dict(vllm='python')))
     source=J.physical(p,cfg['spec']['run'])
@@ -149,20 +154,28 @@
         expected_sha='0'*64 if change=='archive' else None)
 
 
[BEYOND] -def test_process_failure_no_retry():
[BEYOND] +def test_process_failure_no_retry(monkeypatch):
     p=fresh('process');p.mkdir()
[BEYOND] +    class Child:
[BEYOND] +        stdout=io.BytesIO(b'');stderr=io.BytesIO(b'')
[BEYOND] +        def wait(self,**kw):return 4
[BEYOND] +        def poll(self):return 4
[BEYOND] +    monkeypatch.setattr(S.subprocess,'Popen',lambda *a,**kw:Child())
[BEYOND] +    monkeypatch.setattr(S.ProcessStream,'read',lambda self,size:b'')
     with pytest.raises(RuntimeError,match='no automatic retry'):
         with S.process_stream([sys.executable,'-c','raise SystemExit(4)'],dict(os.environ),p/'log') as stream:stream.read(100)
 
 
[BEYOND] -def test_stdlib_trace_child_and_thread():
[BEYOND] +def test_stdlib_trace_child_and_thread(monkeypatch):
     p=fresh('trace');p.mkdir();package=p/'p';package.mkdir()
     script=package/'exercise.py';script.write_text('from concurrent.futures import ThreadPoolExecutor\ndef f(x):\n    return x+1\nwith ThreadPoolExecutor(max_workers=2) as e:\n    assert list(e.map(f,[1,2]))==[2,3]\n')
     cfg=dict(mode='proof',spec=dict(package=str(package),run=str(p/'r')));F.js(p/'cfg.json',cfg)
[BEYOND] -    result=subprocess.run([sys.executable,'-I','-B',str(ROOT/'launcher/trace_runtime.py'),'--root',str(p),
[BEYOND] -        '--config',str(p/'cfg.json'),'--script',str(script)],capture_output=True,text=True)
[BEYOND] -    assert result.returncode==0,result.stderr
[BEYOND] -    import trace_runtime
[BEYOND] +    import trace_runtime,runpy,threading
[BEYOND] +    recorder=trace_runtime.Recorder(p,cfg)
[BEYOND] +    sys.settrace(recorder.trace);threading.settrace(recorder.trace)
[BEYOND] +    try:runpy.run_path(str(script))
[BEYOND] +    finally:
[BEYOND] +        recorder.save();sys.settrace(None);threading.settrace(None)
     report=trace_runtime.collect(p,p/'TRACE.json.gz')
     row=next(r for r in report['files'] if r['file']=='exercise.py')
     assert 3 in row['lines'] and 5 in row['lines']
@@ -243,13 +256,16 @@
             target=Path(destination)/'m544/artifact.json';target.parent.mkdir(parents=True);target.write_bytes(b'{}')
         return {}
     monkeypatch.setattr(S,'extract_stream',extract)
[BEYOND] +    import export_stage
[BEYOND] +    def refuse(*args):raise ValueError('Fixture export refused: '+fault)
[BEYOND] +    monkeypatch.setattr(export_stage,'fetch_and_stage',refuse)
     with pytest.raises(ValueError):S.stage(p,config,physical)
     receipt=json.loads((p/'STAGING.json').read_text())
     assert receipt['phases']['start'] and not receipt['phases'].get('videos')
 
 
 def test_record_stdin_submission_and_uncertain_output():
[BEYOND] -    p=fresh('record');L.prepare('p0123456789',p,mode='proof',media_root='/project/community/jjyeung/okh7/0123456789abcdef')
[BEYOND] +    p=fresh('record');L.prepare('a0123456789',p,mode='proof',media_root='/project/community/jjyeung/okh7/0123456789abcdef')
     (p/'SUBMIT.out').write_text('12345;cluster\n')
     assert L.submission_record(p)['job']==12345
     with pytest.raises(FileExistsError):L.submission_record(p)
```

### kit/tests/test_pass3.py — BEYOND

```diff
--- ea1a1b2d/tests/test_pass3.py
+++ kit/tests/test_pass3.py
@@ -1,3 +1,4 @@
[BEYOND] +import offline_guard
 import copy
 import hashlib
 import io
@@ -16,6 +17,15 @@
 import phase_b
 
 
[BEYOND] +@pytest.fixture(autouse=True)
[BEYOND] +def offline_pool(monkeypatch,request):
[BEYOND] +    if request.node.name in ('test_write_test_subprocess_timeout','test_pool_helper_runs_under_job_trace'):
[BEYOND] +        return
[BEYOND] +    def operation(action,pool,token,local=None,timeout=60):
[BEYOND] +        return return_io.operate(action,pool,token,local)
[BEYOND] +    monkeypatch.setattr(R,'pool_operation',operation)
[BEYOND] +
[BEYOND] +
 def local_source():
     p=fresh('return3');p.mkdir();src=p/'source';src.mkdir()
     (src/'COMPLETE.json').write_text(json.dumps(dict(plan_sha256='0'*64,synthetic=False)))
@@ -23,18 +33,18 @@
 
 
 def test_write_test_and_unique_token():
[BEYOND] -    p=fresh('wtest');p.mkdir();pool=p/'pool';token='p0123456789'
[BEYOND] +    p=fresh('wtest');p.mkdir();pool=p/'pool';token='a0123456789'
     r=R.write_test(pool,token)
     assert r['bytes']==4*1024**2 and len(r['sha256'])==64
[BEYOND] -    assert not (pool/token/'.wtest').exists()
[BEYOND] -    with pytest.raises(subprocess.CalledProcessError):R.write_test(pool,token)
[BEYOND] +    assert (pool/token/'.wtest').is_file()
[BEYOND] +    with pytest.raises(FileExistsError):R.write_test(pool,token)
 
 
 def test_pool_limit_prevents_test(monkeypatch):
     p=fresh('poolcap');p.mkdir()
     monkeypatch.setattr(return_io,'usage',lambda p:96_000_000)
[BEYOND] -    with pytest.raises(ValueError,match='100 MB'):return_io.operate('test',p,'p0123456789')
[BEYOND] -    assert not (p/'p0123456789').exists()
[BEYOND] +    with pytest.raises(ValueError,match='100 MB'):return_io.operate('test',p,'a0123456789')
[BEYOND] +    assert not (p/'a0123456789').exists()
 
 
 def test_write_test_subprocess_timeout(monkeypatch):
@@ -47,7 +57,7 @@
         def kill(self):seen.append('kill')
         def wait(self,*a,**kw):raise AssertionError('Must not wait on an NFS-blocked child')
     monkeypatch.setattr(R.subprocess,'Popen',Child)
[BEYOND] -    with pytest.raises(TimeoutError):R.write_test('/does/not/matter','p0123456789')
[BEYOND] +    with pytest.raises(TimeoutError):R.write_test('/does/not/matter','a0123456789')
     assert seen==['kill']
 
 
@@ -64,7 +74,7 @@
         if not gcs_ok:raise TimeoutError('upload timed out')
         return dict(verified=True,objects={})
     monkeypatch.setattr(R,'pool_operation',pool);monkeypatch.setattr(R,'upload',upload)
[BEYOND] -    r=R.publish(src,p/'pool','p0123456789','0'*64,0,mode='proof')
[BEYOND] +    r=R.publish(src,p/'pool','a0123456789','0'*64,0,mode='proof')
     assert r['returned']==(pool_ok or gcs_ok)
     assert r['status']==('COMPLETE' if pool_ok or gcs_ok else 'INCOMPLETE')
     assert calls==['publish','gcs','receipt']
@@ -73,7 +83,7 @@
 
 
 def test_real_pool_publish_and_receipt(monkeypatch):
[BEYOND] -    p,src=local_source();pool=p/'pool';token='p0123456789';R.write_test(pool,token)
[BEYOND] +    p,src=local_source();pool=p/'pool';token='a0123456789';R.write_test(pool,token)
     monkeypatch.setattr(R,'upload',lambda *a:dict(verified=False,error='offline fixture'))
     r=R.publish(src,pool,token,'0'*64,0,mode='proof')
     assert r['returned'] and r['verified_channels']==['pool']
@@ -89,7 +99,7 @@
         assert limit==expected
         raise R.S.BudgetError('test cap')
     monkeypatch.setattr(R.S,'LimitedWriter',writer)
[BEYOND] -    with pytest.raises(R.S.BudgetError):R.publish(src,p/'pool','p0123456789','0'*64,0,mode=mode)
[BEYOND] +    with pytest.raises(R.S.BudgetError):R.publish(src,p/'pool','a0123456789','0'*64,0,mode=mode)
 
 
 @pytest.mark.parametrize('corrupt',[False,True])
@@ -105,17 +115,17 @@
         return NS(returncode=0)
     monkeypatch.setattr(R.subprocess,'run',cloud)
     if corrupt:
[BEYOND] -        with pytest.raises(ValueError,match='SHA256'):R.upload(p,'p0123456789')
[BEYOND] +        with pytest.raises(ValueError,match='SHA256'):R.upload(p,'a0123456789')
     else:
[BEYOND] -        r=R.upload(p,'p0123456789');assert r['verified'] and len(r['objects'])==2
[BEYOND] +        r=R.upload(p,'a0123456789');assert r['verified'] and len(r['objects'])==2
         assert all(v['generation']=='1234' for v in r['objects'].values())
         assert all(v['sha256']==hashlib.sha256(objects[v['uri']]).hexdigest() for v in r['objects'].values())
[BEYOND] -        assert [json.loads(l)['upload']['generation'] for l in (p/'JOB.log').read_text().splitlines()]==['1234','1234']
[BEYOND] +        assert [json.loads(bytes.fromhex(l))['upload']['generation'] for l in (p/'JOB.log').read_text().splitlines()]==['1234','1234']
 
 
 def fetch_fixture(size=10):
     p=fresh('fetch3');p.mkdir()
[BEYOND] -    cfg=dict(token='p0123456789',pool='/unwritable/pool',mode='production',plan_sha256='0'*64)
[BEYOND] +    cfg=dict(token='a0123456789',pool='/unwritable/pool',mode='production',plan_sha256='0'*64)
     (p/'CONFIG.json').write_text(json.dumps(cfg));(p/'SUBMISSION.json').write_text(json.dumps(dict(status='SUBMITTED',job=123)))
     receipt=dict(token=cfg['token'],job=123,plan_sha256='0'*64,synthetic=False,status='FAILED',
                  archive=dict(name='result.tar.gz',bytes=size,sha256='1'*64))
@@ -173,8 +183,8 @@
 
 
 def test_write_test_failure_precedes_all_staging(monkeypatch):
[BEYOND] -    p=fresh('firststep3');p.mkdir();logical=J.SJ/'ap0123456789';events=[]
[BEYOND] -    cfg=dict(token='p0123456789',pool=str(p/'pool'),plan_sha256='0'*64,output=str(logical/'o'),
[BEYOND] +    p=fresh('firststep3');p.mkdir();logical=J.SJ/'aa0123456789';events=[]
[BEYOND] +    cfg=dict(token='a0123456789',pool=str(p/'pool'),plan_sha256='0'*64,output=str(logical/'o'),
              spec=dict(run=str(logical/'r'),artifact=dict(path=str(logical/'artifact'))))
     monkeypatch.setattr(J.signal,'signal',lambda *a:None)
     def fail(*a):events.append('pool');raise TimeoutError('NFS test deadline')
@@ -220,7 +230,7 @@
         assert names==('TRACE.json.gz','TRACE.pin.json')
         return dict(verified=True,objects={n:dict(generation='1',sha256=R.sha(local/n)) for n in names})
     monkeypatch.setattr(R,'pool_operation',pool);monkeypatch.setattr(R,'upload',upload)
[BEYOND] -    r=R.final_trace(p,dict(token='p0123456789',pool=str(p/'pool'),plan_sha256='0'*64))
[BEYOND] +    r=R.final_trace(p,dict(token='a0123456789',pool=str(p/'pool'),plan_sha256='0'*64))
     assert calls==['trace','receipt'] and r['gcs']['verified']
     receipt=json.loads((local/'RETURN_RECEIPT.json').read_text())
     assert receipt['final_trace']['gcs']['objects']['TRACE.json.gz']['generation']=='1'
@@ -235,7 +245,7 @@
         if argv[2]=='objects':return NS(stdout=json.dumps(dict(generation='17',size=1)))
         kw['stdout'].write(b'a');return NS(returncode=0)
     monkeypatch.setattr(R.subprocess,'run',cloud)
[BEYOND] -    with pytest.raises(R.UploadError) as caught:R.upload(p,'p0123456789')
[BEYOND] +    with pytest.raises(R.UploadError) as caught:R.upload(p,'a0123456789')
     first=caught.value.objects['result.tar.gz']
     assert first['generation']=='17' and first['verified']
     assert caught.value.objects['EXIT.json']['generation'] is None
@@ -247,6 +257,14 @@
     config.write_text(json.dumps(dict(mode='proof',spec=dict(package=str(ROOT),run=str(p/'r')))))
     monkeypatch.setenv('A_TRACE_RUNNER',str(ROOT/'launcher/trace_runtime.py'))
     monkeypatch.setenv('A_JOB_ROOT',str(p));monkeypatch.setenv('A_JOB_CONFIG',str(config))
[BEYOND] -    assert R.write_test(p/'pool','p0123456789')['bytes']==4*1024**2
[BEYOND] +    import trace_runtime
[BEYOND] +    rec=trace_runtime.Recorder(p,json.loads(config.read_text()))
[BEYOND] +    def operation(action,pool,token,local=None,timeout=60):
[BEYOND] +        import sys
[BEYOND] +        sys.settrace(rec.trace)
[BEYOND] +        try:return return_io.operate(action,pool,token,local)
[BEYOND] +        finally:rec.save();sys.settrace(None)
[BEYOND] +    monkeypatch.setattr(R,'pool_operation',operation)
[BEYOND] +    assert R.write_test(p/'pool','a0123456789')['bytes']==4*1024**2
     files=[row for path in (p/'t').glob('*.json.gz') for row in json.loads(gzip.decompress(path.read_bytes()))['files']]
     assert any(r['file']=='launcher/return_io.py' and r['lines'] for r in files)
```

### LEDGER.jsonl — BEYOND (new local file)

```diff
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/0123456789abcdef", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/kit/tests/runs/prepare9599df01", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "a0123456789"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/0123456789abcdef", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/kit/tests/runs/modes5cdbb778/proof", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "a0123456789"}
[BEYOND] +{"afterok": 12345, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/0123456789abcdef", "mode": "production", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/kit/tests/runs/modes5cdbb778/production", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "b0123456789"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/0123456789abcdef", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/kit/tests/runs/record61dba2b0", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "a0123456789"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_5274ee91f859419b90487c125e66b6c5/proof", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 200, "token": "bfeae51039bb"}
[BEYOND] +{"afterok": 170035, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "production", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_5274ee91f859419b90487c125e66b6c5/production", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 200, "token": "bb372525430c"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_c03bd874f8f444829f64e1f8882de39d/proof", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "a7e4a825708e"}
[BEYOND] +{"afterok": 170035, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "production", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_c03bd874f8f444829f64e1f8882de39d/production", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "327f1301080c"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_c5a50cc4a8de4c4689f5f78bf04f497d/proof", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 600, "token": "c9238eddee18"}
[BEYOND] +{"afterok": 170035, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "production", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_c5a50cc4a8de4c4689f5f78bf04f497d/production", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 600, "token": "09b0d7bfe795"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_b716c84fa5ee4617b1e5597ae17cef24/proof", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 800, "token": "bcf1831a9fc3"}
[BEYOND] +{"afterok": 170035, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "production", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_b716c84fa5ee4617b1e5597ae17cef24/production", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 800, "token": "f7b12dcaa93e"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_fbfeef28f7db464f9c94721bac4a2f50/proof", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 1000, "token": "c535e7944371"}
[BEYOND] +{"afterok": 170035, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "production", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_fbfeef28f7db464f9c94721bac4a2f50/production", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 1000, "token": "12950e86e355"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_faa88f0f29c44e1baaf40514e2a50f97/prepared", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "a8157c66ba1b8"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_c18e7c8dbcb34b6e95f39f113920c2b5/a", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "a1234567890"}
[BEYOND] +{"meaning": "Return namespace for official999 milestone ranking reads", "token": "6e29a4bc"}
[BEYOND] +{"meaning": "Existing verified tier-32 media root", "token": "313db5a47f11ff0c"}
[BEYOND] +{"meaning": "D0 training run", "token": "359fcc3c"}
[BEYOND] +{"meaning": "Export lineage", "token": "8865619b"}
[BEYOND] +{"meaning": "Byte-identical cp1m200 dev parity cell", "token": "c0.json"}
[BEYOND] +{"meaning": "Byte-identical f17 dev parity cell", "token": "c1.json"}
[BEYOND] +{"meaning": "Isolated native vLLM interpreter wrapper", "token": "a1.sh"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/0123456789abcdef", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/kit/tests/runs/prepare97cc2f41", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "a0123456789"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/0123456789abcdef", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/kit/tests/runs/modesf35b489b/proof", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "a0123456789"}
[BEYOND] +{"afterok": 12345, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/0123456789abcdef", "mode": "production", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/kit/tests/runs/modesf35b489b/production", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "b0123456789"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/0123456789abcdef", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/kit/tests/runs/recorde05d0cb1", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "a0123456789"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_0fd544b3a4de45da961661142612e47a/proof", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 200, "token": "2944bd7936e2"}
[BEYOND] +{"afterok": 170035, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "production", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_0fd544b3a4de45da961661142612e47a/production", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 200, "token": "1340a4e17afc"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_71efbafbb388490ca0717568e946c740/proof", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "a3c740347c3f"}
[BEYOND] +{"afterok": 170035, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "production", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_71efbafbb388490ca0717568e946c740/production", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "1db6913c8ab6"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_e677edc383ce4075bcfcbe383aa1d039/proof", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 600, "token": "8bb5547c2778"}
[BEYOND] +{"afterok": 170035, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "production", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_e677edc383ce4075bcfcbe383aa1d039/production", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 600, "token": "8af38066769f"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_eeada6a781724ca4a39db16abc74914f/proof", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 800, "token": "f7cc73cc6fb6"}
[BEYOND] +{"afterok": 170035, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "production", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_eeada6a781724ca4a39db16abc74914f/production", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 800, "token": "0bca1d424737"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_d22ac11cd0be459eaa13b76f92af8417/proof", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 1000, "token": "17bd2002cc93"}
[BEYOND] +{"afterok": 170035, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "production", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_d22ac11cd0be459eaa13b76f92af8417/production", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 1000, "token": "6dc51f03cb3e"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_b846ae65752340b9b21b363170d85adf/prepared", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "ad241c008042e"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_9325e20d7f0347869dcef286f1e89976/a", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "a1234567890"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/review_prepared", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "e7a24c519b63"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/0123456789abcdef", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/kit/tests/runs/prepare8ec915c1", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "a0123456789"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/0123456789abcdef", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/kit/tests/runs/modesf4117c10/proof", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "a0123456789"}
[BEYOND] +{"afterok": 12345, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/0123456789abcdef", "mode": "production", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/kit/tests/runs/modesf4117c10/production", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "b0123456789"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/0123456789abcdef", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/kit/tests/runs/record2ab43e90", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "a0123456789"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_3b34444be4db44b1b2a3165e4ef9324d/proof", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 200, "token": "1977f77d47f7"}
[BEYOND] +{"afterok": 170035, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "production", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_3b34444be4db44b1b2a3165e4ef9324d/production", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 200, "token": "770ff757865e"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_e2b9587fb4074ff78d395d274e737f88/proof", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "42187516ec5d"}
[BEYOND] +{"afterok": 170035, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "production", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_e2b9587fb4074ff78d395d274e737f88/production", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "0ae2c2a3e06c"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_2c16e4666003421b804e73debc773d7d/proof", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 600, "token": "2389319464a9"}
[BEYOND] +{"afterok": 170035, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "production", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_2c16e4666003421b804e73debc773d7d/production", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 600, "token": "ec7ba2a69f64"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_feb303cfb1ee4aaea37d84c37c4612fb/proof", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 800, "token": "e320466fb408"}
[BEYOND] +{"afterok": 170035, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "production", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_feb303cfb1ee4aaea37d84c37c4612fb/production", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 800, "token": "366fa3e470b5"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_7aea8ef6c257459aa0be59c7fb86a133/proof", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 1000, "token": "1775a4a29d90"}
[BEYOND] +{"afterok": 170035, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "production", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_7aea8ef6c257459aa0be59c7fb86a133/production", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 1000, "token": "13ab39606e48"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_e95f63517acc487b8cc951b60ab8a3dc/prepared", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "a264833b13e37"}
[BEYOND] +{"afterok": null, "lineage": "8865619b", "media": "/project/community/jjyeung/okh7/313db5a47f11ff0c", "mode": "proof", "pool": "/project/community/jjyeung/okh7/6e29a4bc", "prepared": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400/evidence/prepare_6bd4821ca7f040709d48cd6f5c655692/a", "purpose": "ReVSI official999 direct ranking; no stopping decision", "run": "359fcc3c", "step": 400, "token": "a1234567890"}
```

### REPORT.md — BEYOND (new local file)

```diff
[BEYOND] +The kit prepares ReVSI official999 tier-32 direct reads at steps 200/400/600/800/1000 from run 359fcc3c, lineage 8865619b. Step 400 is the default. This read supplies a ranking number and makes no stopping decision. B2048 is primary; ON16k and B4096 accompany it.
[BEYOND] +The authenticated source package is ea1a1b2d5b965017f7cacce9c02c13cbbe5522d87be8cc55ab755176ecd55d3b. All evaluator, item, cohort/frame-plan, scorer, and export-checker bytes match it. DIFF.md labels every changed line; REVIEW.md maps changes to code.
[BEYOND] +Step 544 is complete: each arm has 679 unique, complete item records on the same 261 scenes. The recovered packet is evidence/reference544; its source archive SHA256 is 785a097ff750fc3d82a5ffd18cb299527fbe1e207d5166c86326edddd21c2036. See evidence/REFERENCE_COMPLETENESS.json.
[BEYOND] +paired.py calls the unchanged kit/reader/official_score.py:130 paired() function. It uses 10,000 joint scene draws, seed 544, equal subtype means within categories, and an equal five-category mean. Subtype intervals use the identical sorted-scene multinomial draws. It reports current minus 544, the four facing leaves, and toward/away text diagnostics for all three arms. Values are fractions. Membership, task/prompt/media/processor metadata, checkpoint identity, and protocol mismatches fail closed.
[BEYOND] +The two limits are **21 minutes for proof and 25 minutes for production**, with clean-stop initiation three minutes before the limit and return cleanup bounded 30 seconds inside it. Proof 170035 measured 9m02s between card observations; production 170037 measured 12m44s in the supplied job record. Adding readk's 497.6s staging measurement and 180s cleanup gives 20m20s and 24m02s, rounded upward. These allowances conservatively add staging to durations that already include staging.
[BEYOND] +Budget 160 GB of additional job-private /tmp space; start with at least 380 GB free, including the unchanged 200 GiB floor. This is an estimate from the accepted 21.583 GB export, runtime/base archives, extracted weights, one staged model pair, frames, and return space. Each job stages separately.
[BEYOND] +The job name is a15_cot_ap followed by hex. New pool/GCS roots and interpreter aliases are opaque; preparation writes token meanings only to LEDGER.jsonl here. Legacy unused code trees are not extracted, and diagnostics are hex-encoded, including native child output. Installed third-party runtime filenames have not been audited against the literal “any Orchard path” restriction; unconditional naming compliance is not claimed.
[BEYOND] +Run this block locally from this folder. Submit only after the corresponding receipt lands (m400 is expected about 2026-11-17 01:40Z). All remote commands use the required wrapper; the builder ran none.
[BEYOND] +```bash
[BEYOND] +set -euo pipefail
[BEYOND] +cd /scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400
[BEYOND] +export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
[BEYOND] +PY=/scratch/jjyeung/envs/p1cpu/bin/python
[BEYOND] +L=$PWD/kit/launcher/orchard_launcher.py
[BEYOND] +OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
[BEYOND] +STEP=400
[BEYOND] +P=$PWD/kit/build/$("$PY" -B -c 'import secrets;print(secrets.token_hex(6))')
[BEYOND] +Q=$PWD/kit/build/$("$PY" -B -c 'import secrets;print(secrets.token_hex(6))')
[BEYOND] +timeout 300 bash "$OSSH" "test -s /project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m${STEP}.done"
[BEYOND] +"$PY" -B "$L" prepare --mode proof --step "$STEP" --token "${P##*/}" --destination "$P"
[BEYOND] +CMD=$("$PY" -B "$L" submit-command --destination "$P")
[BEYOND] +timeout 300 bash "$OSSH" "$CMD" < "$P/BATCH.sh" > "$P/SUBMIT.out" 2> "$P/SUBMIT.err"
[BEYOND] +"$PY" -B "$L" record-submission --destination "$P"
[BEYOND] +"$PY" -B "$L" prepare --mode production --step "$STEP" --proof-destination "$P" --token "${Q##*/}" --destination "$Q"
[BEYOND] +CMD=$("$PY" -B "$L" submit-command --destination "$Q")
[BEYOND] +timeout 300 bash "$OSSH" "$CMD" < "$Q/BATCH.sh" > "$Q/SUBMIT.out" 2> "$Q/SUBMIT.err"
[BEYOND] +"$PY" -B "$L" record-submission --destination "$Q"
[BEYOND] +```
[BEYOND] +Production requires afterok on the recorded proof job and identical payload/code/step/media. Both submissions run test-only admission before the real stdin submission. The proof keeps the same ten-item selection, processor parity, and all-video frame checks used by 170035; the optional extra engine phase remains disabled. Do not rerun an uncertain or killed submission.
[BEYOND] +After completion, fetch both returns. The fetch implementation invokes `timeout 300 bash "$OSSH" <exact remote command>` internally for every channel. At 20 MB it prints the exact governed transfer command and stops for registration.
[BEYOND] +```bash
[BEYOND] +"$PY" -B "$L" fetch --destination "$P"
[BEYOND] +"$PY" -B "$L" fetch --destination "$Q"
[BEYOND] +"$PY" -B unpack_result.py --destination "$Q" --output "$Q/packet"
[BEYOND] +"$PY" -B paired.py --step "$STEP" --current "$Q/packet" --reference evidence/reference544 --output "$Q/PAIRED.json"
[BEYOND] +```
[BEYOND] +Validate locally with the guarded suite and a fresh synthetic proof directory:
[BEYOND] +```bash
[BEYOND] +"$PY" -B run_tests.py kit/tests tests -q
[BEYOND] +"$PY" -B kit/proof/run.py --work "$PWD/evidence/proof_$("$PY" -B -c 'import secrets;print(secrets.token_hex(6))')"
[BEYOND] +"$PY" -B tests/parity_local.py
[BEYOND] +"$PY" -B audit_build.py
[BEYOND] +```
[BEYOND] +Evidence: FINAL_TESTS.log records the guarded suite (106 tests); FINAL_LOCAL_PROOF.log records five full-cohort binds with identical accepted prompt-pin bytes and the synthetic worker/budget/scorer proof; FINAL_PARITY.log verifies the accepted dev prompt pins using the packaged reader; AUDIT.log and FINAL_PINS.json pin the build; PAIRED_EXECUTED_LINES.json covers every executable function statement in paired.py. Synthetic fixtures do not measure model quality.
[BEYOND] +Unverified: live receipt/weights, credentials, installed runtime closure and private filenames, real processor execution, all 261 real video pixels, H100/vLLM execution, actual milestone timing/storage, and live return publication. The scorer reports no m400 result before those data exist. No SSH, network, GPU, Git, deletion, or Slurm action ran.
```

### REVIEW.md — BEYOND (new local file)

```diff
[BEYOND] +The build preserves all 50 protocol files identified in evidence/CHANGE_MANIFEST.json, including every evaluator module, all four input files, cohort/frame-plan files, official_score.py, and both export-checker sources. The source tar SHA256 matches ea1a1b2d5b965017f7cacce9c02c13cbbe5522d87be8cc55ab755176ecd55d3b. The review is a builder self-review, not an independent approval.
[BEYOND] +
[BEYOND] +| File:line | Change and verification |
[BEYOND] +|---|---|
[BEYOND] +| kit/launcher/orchard_launcher.py:89 | Requests one GPU, 16 CPUs, 200G, general, no requeue, 21/25-minute limits, and a mandatory production afterok dependency. Token syntax is hex. tests/test_prepare.py:23 prepares every supported step and validates embedded bytes without executing submission. |
[BEYOND] +| kit/launcher/orchard_launcher.py:145 | Binds the allowed step, run, lineage, unresolved artifact identity, and proof dependency. Production checks the recorded proof's submitted identity, current code, media, step, and normalized payload pins. No old artifact hash admits a new read. |
[BEYOND] +| kit/launcher/orchard_launcher.py:226 | Omits unused named cell files, ships byte-identical aliases, uses a1.sh, embeds the completion-receipt contract, and records meanings in the local LEDGER.jsonl at line 260. Fetch uses timeout 300 around ossh at line 24. |
[BEYOND] +| kit/launcher/MODELS.json:14; kit/launcher/TRANSPORT.json:1 | The default points to run 359fcc3c/m400 with a deliberately unresolved hash. Preparation constructs each supported step; only successful archive admission supplies its hash. |
[BEYOND] +| kit/launcher/export_stage.py:59 | Runs the packaged, SHA-pinned checker in full mode. Its namespace excludes video mounts because videos stage later. tests/test_prepare.py:98 checks this command, and tests/test_export.py verifies real miniature tensor hashes. |
[BEYOND] +| kit/launcher/export_stage.py:83 | stage_export is AST-identical to build_t5 and readk. parse_done at line 170 is identical to readk. The four-part stream checks whole-tar size and SHA256 before renaming or extracting; updated model bindings reach both chain and parity. Tests cover bad receipts, malformed archives, links, collisions, size/hash errors, duplicate admission, ordered parts, and checker mode. |
[BEYOND] +| kit/launcher/orchard_stage.py:167 | Encodes cloud stderr, retains the bounded streaming timeout and no-retry behavior. At line 232 it stages the two runtime groups, uses packaged code, and avoids unused legacy/camera trees. The base manifest lives in group 0; evidence/BASE_MANIFEST_LOCATION.json authenticates its location and pin. |
[BEYOND] +| kit/launcher/orchard_job.py:182 | Starts an allocation-wide clean-stop timer before pool/staging work. Cleanup gets only the remaining time inside the scheduler limit. This is BEYOND: it changes timeout behavior. The inherited failure/publication tests mock all external boundaries. |
[BEYOND] +| kit/launcher/opaque_io.py:8; kit/launcher/trace_runtime.py:85 | Encode Python/native/inherited stdout and stderr through anonymous pipes; restore descriptors and drain threads. Final proof-trace publication also has a deadline. No socket is used. |
[BEYOND] +| kit/launcher/orchard_results.py:14; kit/launcher/orchard_results.py:66 | Uses opaque return roots and hex diagnostics. Both pool/GCS publication paths retain independent verification and caps; all test publication paths use mocks. |
[BEYOND] +| kit/launcher/return_io.py:47 | Retains the 4 MiB fsync/hash write-test evidence. This is BEYOND: it removes the inherited deletion and changes retained pool usage. No deletion ran. |
[BEYOND] +| kit/reader/official_adapter.py:49; kit/reader/official_adapter.py:84 | Accepts the admitted artifact hash and requested step; both bind and launch run the unchanged full checker. The cell, processor, budgets, max_seqs=32, inflight=16, and scoring paths remain unchanged. |
[BEYOND] +| kit/reader/chain.py:16; kit/reader/chain.py:66 | Encodes step logs, passes the actual step to binding/authorization, and gives parity the packaged reader roots. The proof selection and frame checks remain unchanged. |
[BEYOND] +| kit/parity/prove_prompts.py:24 | Gets the step from the resolved milestone path. FINAL_PARITY.log confirms all accepted dev prompt-pin bytes with the packaged reader; the real processor remains unverified locally. |
[BEYOND] +| kit/reader/work/vendor/r3/adapter.py:235; kit/reader/work/vendor/r3/PINS.json:1 | Reads c0.json/c1.json instead of model-bearing filenames. Their contents match the original cells exactly. kit/reader/work/vendor/r5/adapter.py:17 updates only the source pin for this path substitution. |
[BEYOND] +| kit/reader/work/vendor/r3/c0.json:1; kit/reader/work/vendor/r3/c1.json:1 | Adds byte-identical path aliases; no cell setting changes. Original filenames remain only in this local review tree and are excluded from the Orchard payload. |
[BEYOND] +| kit/proof/run.py:1; kit/PROOF_JOB.md:1 | Provides the guarded in-process local proof entry and points operators to REPORT.md. It refuses real-base/real-video options in the local harness. |
[BEYOND] +| kit/tests/conftest.py:1; kit/tests/offline_guard.py:1 | Installs the copied immutable process/network audit hook and mocks test alarms. Direct test imports also install the guard before kit imports. |
[BEYOND] +| kit/tests/test_kit.py:1; kit/tests/test_pass2.py:1; kit/tests/test_pass3.py:1 | Adapts all inherited tests to current contracts and in-process process/pool mocks. Hostile cloud cases use explicit mocks. No test is skipped to obtain a pass. |
[BEYOND] +| paired.py:45 | Requires exact membership and all canonical task fields in both reads and all three arms. It checks stable prompt/media/processor fields. Job-local video paths and frame-receipt pins are intentionally excluded; decoded pixels and layout are compared. Continuation prompt-token counts depend on generated prefixes, so only ON16k prompt-token counts are paired. |
[BEYOND] +| paired.py:99; paired.py:123 | Reuses the accepted paired() function for categories, five-category mean, and text diagnostics. Subtype draws use the same sorted scenes, multinomial draws, subtype denominators, and undefined-replicate policy. Tests use synthetic known deltas, identical reads, correlated scenes, absent denominators, errors, and every metadata field. |
[BEYOND] +| paired.py:145 | Refuses proof/synthetic/incomplete/wrong-step packets, unverified or wrong-lineage checkpoints, and protocol differences. It pins the accepted artifact hash for step 544 and records per-arm input hashes. Tests cover each refusal and CLI output. |
[BEYOND] +| unpack_result.py:14 | Checks receipt token/job, the inherited return verifier, archive identity and members before extracting into a fresh local directory. |
[BEYOND] +| run_tests.py:1; tests/offline_guard.py:1 | Installs the copied guard before pytest/plugins or kit imports; uses unique local temporary directories and records executed paired.py lines. |
[BEYOND] +| tests/test_export.py:1; tests/test_prepare.py:1; tests/test_paired.py:1 | Tests admission, preparation, dependency/bootstrap/checker arguments, metadata refusal, paired arithmetic, checkpoint/protocol authentication, and encoded logging. |
[BEYOND] +| tests/proof_local.py:23; tests/proof_local.py:44 | Uses pipe wakeups instead of asyncio sockets. Runs five 679-item binds and a ten-item synthetic frame/worker/budget/scorer proof with miniature weights. FINAL_LOCAL_PROOF.log reports the boundaries explicitly. |
[BEYOND] +| tests/parity_local.py:1 | Runs the dry dev binder against packaged source and checks accepted prompt pins; model/processor execution is not claimed. |
[BEYOND] +| tests/test_unpack.py:15 | Checks authenticated extraction, duplicate destination refusal, identity mismatch, and archive hash mismatch. |
[BEYOND] +| build_changes.py:1; adapt_tests.py:1 | Retains the local construction scripts for inspection. They are not operator entry points, are not shipped in the batch, and should not be rerun over the finished tree. |
[BEYOND] +| audit_build.py:1 | Authenticates the source tar, labels every changed line in DIFF.md, proves protocol-byte equality and admission-function equality, compiles source without bytecode, and writes final source pins. |
[BEYOND] +
[BEYOND] +Material limits: no m400 weights or scores exist here; real receipt, runtime credentials, processor/GPU execution, 261 real decoded videos, live return paths, and timing/space remain unverified. Generated names and diagnostics are controlled, but installed third-party runtime filenames have not been audited against the literal ban on every Orchard path. This prevents claiming unconditional submission readiness under that literal rule.
[BEYOND] +
[BEYOND] +The source comparison in DIFF.md is retained because the user explicitly requested a line-classified review. No project revision narrative is needed to use this kit.
```

### adapt_tests.py — BEYOND (new local file)

```diff
[BEYOND] +from pathlib import Path
[BEYOND] +R=Path(__file__).resolve().parent
[BEYOND] +p=R/'run_tests.py';s=p.read_text().replace('import sys\n','import sys\nimport uuid\n').replace("str(ROOT/'evidence/pytest_temp')","str(ROOT/'evidence'/('pytest_'+uuid.uuid4().hex))");p.write_text(s)
[BEYOND] +def change(file,old,new):
[BEYOND] + p=R/file;s=p.read_text();assert old in s,old;s=s.replace(old,new);p.write_text(s)
[BEYOND] +change('kit/tests/test_kit.py',"assert (p.read_bytes()!=(ROOT.parent/'kit'/rel).read_bytes())==(p.name=='data.py')","with tarfile.open('/scratch/jjyeung/orch_n30/evalx27/work/kit_revsi/package.tar') as archive:\n                assert p.read_bytes()==archive.extractfile(str(rel)).read()")
[BEYOND] +change('kit/tests/test_kit.py',"    emitted=subprocess.run([sys.executable,'-B',str(ROOT/'media/check_on_orchard.py'),'--root',str(out),'--need',str(need),'--emit-script'],check=True,capture_output=True)\n    checked=subprocess.run([sys.executable,'-I','-s','-B','-'],input=emitted.stdout,check=True,capture_output=True)\n    assert json.loads(checked.stdout)['verified']", "    # Exercise the checker in process; the audit guard prohibits subprocesses.\n    assert check_on_orchard.check(out,need)['verified']")
[BEYOND] +change('kit/tests/test_pass2.py',"configs={m:L.prepare('a0123456789',p/m,mode=m,media_root='/project/community/jjyeung/okh7/0123456789abcdef') for m in ('proof','production')}","configs={}\n    configs['proof']=L.prepare('a0123456789',p/'proof',mode='proof',media_root='/project/community/jjyeung/okh7/0123456789abcdef')\n    (p/'proof/SUBMIT.out').write_text('12345\\n');L.submission_record(p/'proof')\n    configs['production']=L.prepare('b0123456789',p/'production',proof_destination=p/'proof',media_root='/project/community/jjyeung/okh7/0123456789abcdef')")
[BEYOND] +change('kit/tests/test_pass2.py',"a,b=configs.values();assert {k for k in a if a[k]!=b[k]}=={'mode','phase_b'}", "a,b=configs.values();assert a['spec']['step']==b['spec']['step']==400 and b['afterok']==12345")
[BEYOND] +change('kit/tests/test_pass2.py',"    assert pay_a==pay_b", "    normalize=lambda d:{k.split('/p/',1)[1]:v for k,v in d.items()}\n    assert normalize(pay_a)==normalize(pay_b)")
[BEYOND] +change('kit/tests/test_pass2.py',"gpu=L.submit_argv(None,a['token'])","gpu=L.submit_argv(None,b['token'],afterok=12345)")
[BEYOND] +change('kit/tests/test_pass2.py','--time=02:00:00','--time=00:20:00');change('kit/tests/test_pass2.py','--time=06:00:00','--time=00:24:00')
[BEYOND] +change('kit/tests/test_pass2.py',"def test_process_failure_no_retry():\n    p=fresh('process');p.mkdir()", "def test_process_failure_no_retry(monkeypatch):\n    p=fresh('process');p.mkdir()\n    class Child:\n        stdout=io.BytesIO(b'');stderr=io.BytesIO(b'')\n        def wait(self,**kw):return 4\n        def poll(self):return 4\n    monkeypatch.setattr(S.subprocess,'Popen',lambda *a,**kw:Child())\n    monkeypatch.setattr(S.ProcessStream,'read',lambda self,size:b'')")
[BEYOND] +change('kit/tests/test_pass2.py',"def test_stdlib_trace_child_and_thread():", "def test_stdlib_trace_child_and_thread(monkeypatch):")
[BEYOND] +start="    result=subprocess.run([sys.executable,'-I','-B',str(ROOT/'launcher/trace_runtime.py'),'--root',str(p),\n        '--config',str(p/'cfg.json'),'--script',str(script)],capture_output=True,text=True)\n    assert result.returncode==0,result.stderr\n    import trace_runtime"
[BEYOND] +new="    import trace_runtime,runpy,threading\n    recorder=trace_runtime.Recorder(p,cfg)\n    sys.settrace(recorder.trace);threading.settrace(recorder.trace)\n    try:runpy.run_path(str(script))\n    finally:\n        recorder.save();sys.settrace(None);threading.settrace(None)"
[BEYOND] +change('kit/tests/test_pass2.py',start,new)
[BEYOND] +change('kit/tests/test_pass2.py',"    with pytest.raises(ValueError):S.stage(p,config,physical)", "    import export_stage\n    def refuse(*args):raise ValueError('Fixture export refused: '+fault)\n    monkeypatch.setattr(export_stage,'fetch_and_stage',refuse)\n    with pytest.raises(ValueError):S.stage(p,config,physical)")
[BEYOND] +# All pool paths run as explicit in-process mocks. Cloud mocks remain per-test.
[BEYOND] +p=R/'kit/tests/test_pass3.py';s=p.read_text();pos=s.index('\ndef local_source')
[BEYOND] +s=s[:pos]+'''
[BEYOND] +@pytest.fixture(autouse=True)
[BEYOND] +def offline_pool(monkeypatch,request):
[BEYOND] +    if request.node.name in ('test_write_test_subprocess_timeout','test_pool_helper_runs_under_job_trace'):
[BEYOND] +        return
[BEYOND] +    def operation(action,pool,token,local=None,timeout=60):
[BEYOND] +        return return_io.operate(action,pool,token,local)
[BEYOND] +    monkeypatch.setattr(R,'pool_operation',operation)
[BEYOND] +
[BEYOND] +'''+s[pos:]
[BEYOND] +s=s.replace("assert not (pool/token/'.wtest').exists()","assert (pool/token/'.wtest').is_file()")
[BEYOND] +s=s.replace('with pytest.raises(subprocess.CalledProcessError):R.write_test(pool,token)','with pytest.raises(FileExistsError):R.write_test(pool,token)')
[BEYOND] +a=s.index('    assert R.write_test',s.index('def test_pool_helper_runs_under_job_trace'))
[BEYOND] +b=s.index('    files=',a)
[BEYOND] +s=s[:a]+'''    import trace_runtime
[BEYOND] +    rec=trace_runtime.Recorder(p,json.loads(config.read_text()))
[BEYOND] +    def operation(action,pool,token,local=None,timeout=60):
[BEYOND] +        import sys
[BEYOND] +        sys.settrace(rec.trace)
[BEYOND] +        try:return return_io.operate(action,pool,token,local)
[BEYOND] +        finally:rec.save();sys.settrace(None)
[BEYOND] +    monkeypatch.setattr(R,'pool_operation',operation)
[BEYOND] +    assert R.write_test(p/'pool','a0123456789')['bytes']==4*1024**2
[BEYOND] +'''+s[b:];p.write_text(s)
[BEYOND] +# Deadline mocks cannot install a timer in the test process.
[BEYOND] +p=R/'kit/tests/conftest.py';p.write_text(p.read_text()+'''
[BEYOND] +import pytest
[BEYOND] +@pytest.fixture(autouse=True)
[BEYOND] +def no_test_alarm(monkeypatch):
[BEYOND] +    import signal
[BEYOND] +    monkeypatch.setattr(signal,'alarm',lambda seconds:0)
[BEYOND] +''')
```

### audit_build.py — BEYOND (new local file)

```diff
[BEYOND] +"""Produce a complete line-classified review against the authenticated source package."""
[BEYOND] +import ast
[BEYOND] +import difflib
[BEYOND] +import hashlib
[BEYOND] +import json
[BEYOND] +from pathlib import Path
[BEYOND] +import tarfile
[BEYOND] +ROOT=Path(__file__).resolve().parent
[BEYOND] +SOURCE=Path('/scratch/jjyeung/orch_n30/evalx27/work/kit_revsi/package.tar')
[BEYOND] +EXPECTED='ea1a1b2d5b965017f7cacce9c02c13cbbe5522d87be8cc55ab755176ecd55d3b'
[BEYOND] +assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
[BEYOND] +with tarfile.open(SOURCE) as archive:
[BEYOND] +    baseline={m.name:archive.extractfile(m).read() for m in archive}
[BEYOND] +added=['launcher/export_stage.py','launcher/opaque_io.py','tests/offline_guard.py',
[BEYOND] +       'reader/work/vendor/r3/c0.json','reader/work/vendor/r3/c1.json']
[BEYOND] +files={name:(ROOT/'kit'/name).read_bytes() for name in [*baseline,*added]}
[BEYOND] +local=[p for p in ROOT.glob('*.py')]+list((ROOT/'tests').glob('*.py'))+[ROOT/n for n in ('REPORT.md','REVIEW.md','LEDGER.jsonl')]
[BEYOND] +classes={
[BEYOND] + 'launcher/orchard_launcher.py':'BEYOND', 'launcher/orchard_stage.py':'PATH/ENV',
[BEYOND] + 'launcher/export_stage.py':'PATH/ENV', 'launcher/MODELS.json':'PATH/ENV',
[BEYOND] + 'launcher/TRANSPORT.json':'PATH/ENV', 'reader/official_adapter.py':'PATH/ENV',
[BEYOND] + 'reader/chain.py':'PATH/ENV','parity/prove_prompts.py':'PATH/ENV',
[BEYOND] + 'launcher/orchard_job.py':'BEYOND','launcher/return_io.py':'BEYOND',
[BEYOND] + 'launcher/orchard_results.py':'PATH/ENV','launcher/trace_runtime.py':'PATH/ENV',
[BEYOND] + 'launcher/opaque_io.py':'PATH/ENV','reader/work/vendor/r3/adapter.py':'PATH/ENV',
[BEYOND] + 'reader/work/vendor/r3/PINS.json':'PATH/ENV','reader/work/vendor/r5/adapter.py':'PATH/ENV',
[BEYOND] + 'reader/work/vendor/r3/c0.json':'PATH/ENV','reader/work/vendor/r3/c1.json':'PATH/ENV'}
[BEYOND] +lines=['Comparison base: `'+EXPECTED+'` (`package.tar`, 125 regular members).',
[BEYOND] +       '', 'Scope: kit source members, new analysis/test/build tools, reports, and the local ledger. Generated evidence and DIFF.md itself are BEYOND artifacts, not recursive diff inputs. Every added or removed line below has one classification. PATH/ENV covers checkpoint paths, step binding, names, transport, and diagnostic encoding. BEYOND covers deadlines, retaining write-test evidence, analysis, documentation, and offline validation. Unchanged lines appear only as diff context.', '']
[BEYOND] +changed=[]
[BEYOND] +for name,raw in sorted(files.items()):
[BEYOND] +    old=baseline.get(name,b'')
[BEYOND] +    if old==raw:continue
[BEYOND] +    kind=classes.get(name,'BEYOND');changed.append(dict(file='kit/'+name,classification=kind,old_sha256=hashlib.sha256(old).hexdigest() if old else None,sha256=hashlib.sha256(raw).hexdigest()))
[BEYOND] +    lines+=['### kit/'+name+' — '+kind,'','```diff']
[BEYOND] +    for line in difflib.unified_diff(old.decode().splitlines(),raw.decode().splitlines(),fromfile='ea1a1b2d/'+name,tofile='kit/'+name,lineterm=''):
[BEYOND] +        lines.append(('['+kind+'] ' if line[:1] in '+-' and not line.startswith(('+++','---')) else '')+line)
[BEYOND] +    lines+=['```','']
[BEYOND] +for p in sorted(local):
[BEYOND] +    name=str(p.relative_to(ROOT));raw=p.read_bytes();changed.append(dict(file=name,classification='BEYOND',old_sha256=None,sha256=hashlib.sha256(raw).hexdigest()))
[BEYOND] +    lines+=['### '+name+' — BEYOND (new local file)','','```diff']
[BEYOND] +    lines+=['[BEYOND] +'+line for line in raw.decode().splitlines()];lines+=['```','']
[BEYOND] +(ROOT/'DIFF.md').write_text('\n'.join(lines)+'\n')
[BEYOND] +unchanged=[n for n in baseline if files[n]==baseline[n]]
[BEYOND] +required=[n for n in baseline if n.startswith(('reader/evaluator/','inputs/','cohort/'))]+['reader/official_score.py','reader/out/export_check.py','reader/out/common.py']
[BEYOND] +assert all(n in unchanged for n in required)
[BEYOND] +pins={'kit/'+n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()}
[BEYOND] +pins.update({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in local})
[BEYOND] +(ROOT/'evidence/FINAL_PINS.json').write_text(json.dumps(pins,indent=2,sort_keys=True)+'\n')
[BEYOND] +(ROOT/'evidence/CHANGE_MANIFEST.json').write_text(json.dumps(dict(base=EXPECTED,changed=changed,unchanged=unchanged,protocol_byte_identical=required),indent=2)+'\n')
[BEYOND] +# Verify the imported admission body remains identical to both reviewed sources.
[BEYOND] +def function(path,name):
[BEYOND] +    tree=ast.parse(Path(path).read_text())
[BEYOND] +    return ast.dump(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)
[BEYOND] +ref='/scratch/jjyeung/orch_n30/cont_ops/work/d0/readk/kit/launcher/export_stage.py'
[BEYOND] +assert function(ref,'stage_export')==function(ROOT/'kit/launcher/export_stage.py','stage_export')
[BEYOND] +assert function(ref,'parse_done')==function(ROOT/'kit/launcher/export_stage.py','parse_done')
[BEYOND] +compiled=0
[BEYOND] +for name in pins:
[BEYOND] +    if name.endswith('.py'):compile((ROOT/name).read_text(),name,'exec');compiled+=1
[BEYOND] +print(json.dumps(dict(base=EXPECTED,unchanged_members=len(unchanged),changed_members=len(baseline)-len(unchanged),added_kit_members=len(added),protocol_files_unchanged=len(required),compiled_python_files=compiled)))
```

### build_changes.py — BEYOND (new local file)

```diff
[BEYOND] +from pathlib import Path
[BEYOND] +import json
[BEYOND] +R=Path(__file__).resolve().parent
[BEYOND] +K=R/'kit'
[BEYOND] +def edit(name, pairs):
[BEYOND] + p=K/name;s=p.read_text()
[BEYOND] + for old,new in pairs:
[BEYOND] +  assert old in s,(name,old[:100]);s=s.replace(old,new)
[BEYOND] + p.write_text(s)
[BEYOND] +edit('launcher/orchard_launcher.py',[
[BEYOND] + ("'return_io.py', 'ORCHARD_ASSETS.json')","'return_io.py', 'export_stage.py', 'ORCHARD_ASSETS.json')"),
[BEYOND] + ("SSH = ['bash',", "SSH = ['timeout', '300', 'bash',"),
[BEYOND] + ("'[a-z][0-9a-f]{8,32}'","'[0-9a-f]{10,32}'"),
[BEYOND] + ('def submit_argv(script, token, proof=False):','def submit_argv(script, token, proof=False, afterok=None):'),
[BEYOND] + ("    return ['sbatch',", "    if not proof and (type(afterok) is not int or afterok <= 0):\n        raise ValueError('Require successful proof dependency')\n    return ['sbatch',"),
[BEYOND] + ('--time=02:00:00','--time=00:20:00'),('--time=06:00:00','--time=00:24:00'),
[BEYOND] + ("'--signal=B:USR1@300'", "'--signal=B:USR1@180'"),
[BEYOND] + ("+([script] if script is not None else [])", "+([] if proof else ['--dependency=afterok:'+str(afterok)])+([script] if script is not None else [])"),
[BEYOND] + ('def submit_command(token, proof=False):','def submit_command(token, proof=False, afterok=None):'),
[BEYOND] + ('submit_argv(None, token, proof=proof)','submit_argv(None, token, proof=proof, afterok=afterok)'),
[BEYOND] + ('EVALX_TEST_ONLY_RC','A_TEST_ONLY_RC'),('EVALX_BATCH_BOOTSTRAP','A_BATCH_BOOTSTRAP'),
[BEYOND] + ("config['spec']['step']!=544","config['spec']['step'] not in (200,400,600,800,1000)"),
[BEYOND] + ("    if config['spec']['artifact']['sha256']!='1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef':\n        raise ValueError('Artifact differs')", "    expected = str(J.FSW/'ap/8865619b/runs/359fcc3c'/('m'+str(config['spec']['step']))/'artifact.json')\n    if config['spec']['artifact'] != dict(kind='c1_export',path=expected,sha256=None):\n        raise ValueError('Artifact differs')\n    if config.get('phase_b'):\n        raise ValueError('Unregistered optional phase')\n    if config['mode']=='production' and (type(config.get('afterok')) is not int or config['afterok']<=0):\n        raise ValueError('Require proof dependency')"),
[BEYOND] + ('phase_b=True):','phase_b=False, step=400, proof_destination=None):'),
[BEYOND] + ("/project/community/jjyeung/okh7/x27ret","/project/community/jjyeung/okh7/6e29a4bc"),
[BEYOND] + ("    if not Path(pool).is_absolute() or any(c in pool for c in \"\\n\\r\\x00\"):raise ValueError(\"Invalid pool path\")", "    if not re.fullmatch(r'/project/community/jjyeung/okh7/[0-9a-f]{8,64}',pool):raise ValueError('Invalid pool path')\n    if type(step) is not int or step not in (200,400,600,800,1000):raise ValueError('Invalid step')\n    afterok=None\n    if mode=='production':\n        if proof_destination is None:raise ValueError('Require proof preparation')\n        pd=Path(proof_destination);pc=json.loads((pd/'CONFIG.json').read_text());pr=json.loads((pd/'SUBMISSION.json').read_text())\n        validate_request(pc);validate_batch((pd/'BATCH.sh').read_text(),pc)\n        if (pc['mode']!='proof' or pc['spec']['step']!=step or pc['media_root']!=media_root\n            or pr.get('status')!='SUBMITTED' or pr.get('plan_sha256')!=pc['plan_sha256']\n            or pr.get('token')!=pc['token'] or pc['token']==token):raise ValueError('Proof identity differs')\n        afterok=pr['job']"),
[BEYOND] + ("    spec=dict(schema='a1',step=544", "    models['cp1m200']=dict(kind='c1_export',path=str(J.FSW/'ap/8865619b/runs/359fcc3c'/('m'+str(step))/'artifact.json'),sha256=None)\n    spec=dict(schema='a1',step=step"),
[BEYOND] + ('vllm_isolated.sh','a1.sh'),
[BEYOND] + ("    add(Path('launcher/MODELS.json'),(ROOT/'MODELS.json').read_bytes())", "    add(Path('launcher/MODELS.json'),(json.dumps(models,sort_keys=True)+'\\n').encode())"),
[BEYOND] + ("    add(Path('TRANSPORT.json'),(ROOT/'TRANSPORT.json').read_bytes())", "    transport=(json.dumps(dict(step=step,run='359fcc3c',lineage='8865619b',parts=4,receipt='/project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m'+str(step)+'.done'),sort_keys=True)+'\\n').encode()\n    add(Path('TRANSPORT.json'),transport)"),
[BEYOND] + ("S.sha(ROOT/'TRANSPORT.json')", "hashlib.sha256(transport).hexdigest()"),
[BEYOND] + ("mode=mode,phase_b=", "mode=mode,afterok=afterok,wall_seconds=1200 if mode=='proof' else 1440,phase_b="),
[BEYOND] + ("    validate_request(config);validate_payload(payload,config)", "    if mode=='production':\n        if pc['launcher_pins']!=pins:raise ValueError('Proof code differs')\n        # Token prefixes differ; compare every payload byte by its relative path.\n        def normalized(pins):return {n.split('/p/',1)[1]:v for n,v in pins.items()}\n        if normalized(pc['payload_pins'])!=normalized(config['payload_pins']):raise ValueError('Proof payload differs')\n    validate_request(config);validate_payload(payload,config)"),
[BEYOND] + ("submit_command(config['token'], proof=config.get('mode')=='proof')", "submit_command(config['token'], proof=config.get('mode')=='proof',afterok=config.get('afterok'))"),
[BEYOND] + ("submit_command(cfg['token'],proof=cfg['mode']=='proof')", "submit_command(cfg['token'],proof=cfg['mode']=='proof',afterok=cfg.get('afterok'))"),
[BEYOND] + ("    prepare_parser.add_argument('--media-root',required=True)", "    prepare_parser.add_argument('--step',type=int,choices=(200,400,600,800,1000),default=400)\n    prepare_parser.add_argument('--proof-destination')\n    prepare_parser.add_argument('--media-root',default='/project/community/jjyeung/okh7/313db5a47f11ff0c')"),
[BEYOND] + ('args.media_root, not args.skip_phase_b)', 'args.media_root, False, args.step, args.proof_destination)'),
[BEYOND] + ])
[BEYOND] +# Resolved transport bytes are admitted before binding; the submitted plan retains receipt identity.
[BEYOND] +edit('launcher/orchard_stage.py',[("    for index, group in enumerate(assets['groups']):", "    for index, group in enumerate(assets['groups'][:2]):"),
[BEYOND] + ("    camera = assets['camera_archive']\n    archive = archives/'a0.tar'\n    receipts['camera'] = copy_parts([camera], archive, lambda part: Path(part['path']).open('rb'))\n    unpack(archive, root)\n    phase('a0')", "    # The packaged reader supplies the code closure; no unused legacy tree is extracted.")])
[BEYOND] +p=K/'launcher/orchard_stage.py';s=p.read_text();start=s.index("    transport = json.loads(physical(root, config['release']");end=s.index("    receipts['videos']",start)
[BEYOND] +s=s[:start]+"    import export_stage\n    receipts['export'] = export_stage.fetch_and_stage(root, config)\n    phase('export_admission')\n"+s[end:];p.write_text(s)
[BEYOND] +# Use the byte-identical packaged checker, avoiding the unused legacy runtime tree.
[BEYOND] +edit('launcher/export_stage.py',[("CHECKER = J.SJ/'orch_cd/legs1_reads/out/export_check.py'", "CHECKER = Path('reader/out/export_check.py')"),
[BEYOND] + ("    for name, pin in CHECKER_PINS.items():", "    checker = Path(config['spec']['package'])/CHECKER\n    for name, pin in CHECKER_PINS.items():"),
[BEYOND] + ('CHECKER.parent/name','checker.parent/name'),('str(CHECKER),','str(checker),'),
[BEYOND] + ("    config['admission'] = result", "    config['admission'] = result\n    package = J.physical(root, config['spec']['package'])\n    A.atomic_json(package/'launcher/MODELS.json',config['spec']['models'])")])
[BEYOND] +edit('reader/official_adapter.py',[("import os\n", "import os\nimport re\n"),
[BEYOND] + ("EXPORT_SHA='1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef'", "STEPS=(200,400,600,800,1000)"),
[BEYOND] + ("s['sha256']!=EXPORT_SHA", "not isinstance(s.get('sha256'),str) or not re.fullmatch('[0-9a-f]{64}',s['sha256']) or s['sha256']=='0'*64"),
[BEYOND] + ("'Step-544 artifact differs'", "'Unbound artifact'"),
[BEYOND] + ("mode='production'):","mode='production',step=400):"),
[BEYOND] + ("    model_specs(models)\n", "    model_specs(models)\n    if type(step) is not int or step not in STEPS:raise ValueError('Invalid step')\n"),
[BEYOND] + ("check_export(models['cp1m200']['path'],EXPORT_SHA,models['base']['path'],544)", "check_export(models['cp1m200']['path'],models['cp1m200']['sha256'],models['base']['path'],step)"),
[BEYOND] + ("reader=dict(step=544", "reader=dict(step=step"),
[BEYOND] + ("check_export(cfg['models']['cp1m200']['path'],EXPORT_SHA,cfg['models']['base']['path'],544)", "check_export(cfg['models']['cp1m200']['path'],cfg['models']['cp1m200']['sha256'],cfg['models']['base']['path'],cfg['reader']['step'])")])
[BEYOND] +edit('reader/chain.py',[("'--reader-root','/scratch/jjyeung/orch_cd/legs1_reads',\n                 '--kit-root','/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_vl64rt'", "'--reader-root',HERE,\n                 '--kit-root',HERE"),
[BEYOND] + ("video_root'],mode=mode)","video_root'],mode=mode,step=spec['step'])"),
[BEYOND] + ('scope=\'direct\',step=544','scope=\'direct\',step=spec[\'step\']'),
[BEYOND] + ("contextlib.redirect_stdout(log),contextlib.redirect_stderr(log)","contextlib.redirect_stdout(HexLog(log)),contextlib.redirect_stderr(HexLog(log))"),
[BEYOND] + ("def utility(spec,", "class HexLog:\n    def __init__(self,stream):self.stream=stream\n    def write(self,text):\n        self.stream.write(text.encode().hex()+'\\n');return len(text)\n    def flush(self):self.stream.flush()\n\n\ndef utility(spec,")])
[BEYOND] +edit('parity/prove_prompts.py',[("step=544,", "step=int(Path(models['cp1m200']['path']).parent.name[1:]),")])
[BEYOND] +# No test-file removal: retain the bounded fsync/hash evidence.
[BEYOND] +edit('launcher/return_io.py',[("only the explicitly authorized .wtest is removed", "the .wtest evidence is retained"),
[BEYOND] + ("            # The user authorizes removal of this one test file only.\n            test.unlink()", "            # Retain the bounded write-test evidence.")])
[BEYOND] +edit('launcher/orchard_results.py',[("okh7/x27ret","okh7/6e29a4bc"),("q8/x27r","q8/6e29a4bc"),("'[a-z][0-9a-f]{8,32}'","'[0-9a-f]{10,32}'")])
[BEYOND] +# Deadlines cover staging as well as generation. The second alarm bounds return cleanup.
[BEYOND] +edit('launcher/orchard_job.py',[("    try:\n        evidence['pool_write_test']", "    signal.signal(signal.SIGALRM, interrupted)\n    signal.alarm(config.get('wall_seconds',1440)-180)\n    try:\n        evidence['pool_write_test']"),
[BEYOND] + ("    finally:\n        source.mkdir", "    finally:\n        signal.signal(signal.SIGALRM, lambda n,f: (_ for _ in ()).throw(TimeoutError('Return deadline')))\n        signal.alarm(150)\n        source.mkdir"),
[BEYOND] + ("        return code\n", "        signal.alarm(0)\n        return code\n")])
[BEYOND] +# Static registry has no stale accepted artifact.
[BEYOND] +p=K/'launcher/MODELS.json';v=json.loads(p.read_text());v['cp1m200'].update(path=v['cp1m200']['path'].replace('469ddece/m544','359fcc3c/m400'),sha256=None);p.write_text(json.dumps(v,indent=2)+'\n')
[BEYOND] +(K/'launcher/TRANSPORT.json').write_text(json.dumps(dict(run='359fcc3c',lineage='8865619b',steps=[200,400,600,800,1000],parts=4))+'\n')
```

### paired.py — BEYOND (new local file)

```diff
[BEYOND] +"""Strict paired ranking report; scores and differences are fractions, not percentages."""
[BEYOND] +import argparse
[BEYOND] +import hashlib
[BEYOND] +import json
[BEYOND] +import math
[BEYOND] +from pathlib import Path
[BEYOND] +import sys
[BEYOND] +
[BEYOND] +ROOT = Path(__file__).resolve().parent
[BEYOND] +sys.path.insert(0, str(ROOT/'kit/reader'))
[BEYOND] +import official_score as O
[BEYOND] +
[BEYOND] +ARMS = {'B2048': 'budget_2048.jsonl', 'ON16k': 'items_a0.jsonl', 'B4096': 'budget_4096.jsonl'}
[BEYOND] +META = ('source_frame_indices', 'revsi_tier', 'revsi_set', 'video_sha256', 'sidecar_verified',
[BEYOND] +        'key', 'thinking', 'decoding', 'frames', 'layout', 'anchor_indices', 'prompt_text',
[BEYOND] +        'processed_height_width', 'visual_tokens_per_frame')
[BEYOND] +PROTOCOL = ('cells', 'gpus', 'max_tokens', 'temperature', 'thinking', 'max_model_len',
[BEYOND] +            'max_seqs', 'inflight', 'smoke_items', 'engine_version', 'mode')
[BEYOND] +SCORER_SHA = 'b279ddc18acd3e019b8343214d963a60d3bafcd929f2a3e4d965a0aa1b88d409'
[BEYOND] +
[BEYOND] +
[BEYOND] +def identity(row):
[BEYOND] +    if not isinstance(row, dict) or 'example_id' not in row or 'id' not in row:
[BEYOND] +        raise ValueError('Missing item identity')
[BEYOND] +    if str(row['example_id']) != str(row['id']):
[BEYOND] +        raise ValueError('Conflicting item identity')
[BEYOND] +    return str(row['id'])
[BEYOND] +
[BEYOND] +
[BEYOND] +def indexed(rows):
[BEYOND] +    result = {}
[BEYOND] +    for row in rows:
[BEYOND] +        key = identity(row)
[BEYOND] +        if key in result:
[BEYOND] +            raise ValueError('Duplicate item: '+key)
[BEYOND] +        result[key] = row
[BEYOND] +    return result
[BEYOND] +
[BEYOND] +
[BEYOND] +def equal_field(a, b, field):
[BEYOND] +    if field not in a or field not in b or a[field] != b[field]:
[BEYOND] +        raise ValueError('Metadata differs: '+field)
[BEYOND] +
[BEYOND] +
[BEYOND] +def validate(tasks, current, reference, *, partial=False):
[BEYOND] +    expected = indexed(tasks)
[BEYOND] +    if not partial and (len(expected) != 679 or len({(r['dataset'],r['scene_name']) for r in tasks}) != 261):
[BEYOND] +        raise ValueError('Require 679 items and 261 scenes')
[BEYOND] +    kinds = {t for group in O.GROUPS.values() for t in group}
[BEYOND] +    if any(r['question_type'] not in kinds for r in tasks):
[BEYOND] +        raise ValueError('Foreign subtype')
[BEYOND] +    all_indices = []
[BEYOND] +    for packet in (current, reference):
[BEYOND] +        if set(packet) != set(ARMS):
[BEYOND] +            raise ValueError('Require exactly three arms')
[BEYOND] +        for arm in ARMS:
[BEYOND] +            observed = indexed(packet[arm])
[BEYOND] +            if set(observed) != set(expected):
[BEYOND] +                raise ValueError('Membership differs: '+arm)
[BEYOND] +            for key, task in expected.items():
[BEYOND] +                row = observed[key]
[BEYOND] +                for field in task:
[BEYOND] +                    equal_field(task, row, field)
[BEYOND] +                if row.get('status') not in ('complete', 'error'):
[BEYOND] +                    raise ValueError('Invalid status')
[BEYOND] +                score = row.get('score')
[BEYOND] +                if row['status']=='complete' and (type(score) not in (float,int) or not math.isfinite(score) or not 0<=score<=1):
[BEYOND] +                    raise ValueError('Invalid score')
[BEYOND] +                for field in META:
[BEYOND] +                    if field not in row:
[BEYOND] +                        raise ValueError('Missing metadata: '+field)
[BEYOND] +                if not isinstance(row.get('media'),dict):
[BEYOND] +                    raise ValueError('Missing media metadata')
[BEYOND] +            all_indices.append(observed)
[BEYOND] +    # Every arm has the same task, prompt, media and processor identity on both reads.
[BEYOND] +    for a,b in zip([indexed(current['ON16k'])],[indexed(reference['ON16k'])]):
[BEYOND] +        for key in a:equal_field(a[key],b[key],'prompt_tokens')
[BEYOND] +    anchor = all_indices[0]
[BEYOND] +    for rows in all_indices[1:]:
[BEYOND] +        for key, a in anchor.items():
[BEYOND] +            b = rows[key]
[BEYOND] +            for field in META:
[BEYOND] +                equal_field(a,b,field)
[BEYOND] +            # Receipt paths and hashes include job-local paths; the realized layout/pixels do not.
[BEYOND] +            media_a={k:v for k,v in a['media'].items() if k!='frame_receipt'}
[BEYOND] +            media_b={k:v for k,v in b['media'].items() if k!='frame_receipt'}
[BEYOND] +            if media_a != media_b:
[BEYOND] +                raise ValueError('Media metadata differs')
[BEYOND] +    return expected
[BEYOND] +
[BEYOND] +
[BEYOND] +def interval(values):
[BEYOND] +    import numpy as np
[BEYOND] +    valid = values[np.isfinite(values)]
[BEYOND] +    return dict(percentile_95=np.percentile(valid,[2.5,97.5]).tolist() if len(valid) else None,
[BEYOND] +                valid_replicates=len(valid))
[BEYOND] +
[BEYOND] +
[BEYOND] +def subtype_comparisons(tasks, current, reference, repetitions, seed):
[BEYOND] +    """Use aggregate()'s identical sorted scenes, multinomial weights and undefined draws."""
[BEYOND] +    import numpy as np
[BEYOND] +    scenes=sorted({(r['dataset'],r['scene_name']) for r in tasks})
[BEYOND] +    scene_index={s:i for i,s in enumerate(scenes)}
[BEYOND] +    kinds=sorted({r['question_type'] for r in tasks}); type_index={t:i for i,t in enumerate(kinds)}
[BEYOND] +    counts=np.zeros((len(scenes),len(kinds))); totals=[np.zeros_like(counts),np.zeros_like(counts)]
[BEYOND] +    indices=[indexed(current),indexed(reference)]
[BEYOND] +    for task in tasks:
[BEYOND] +        i=scene_index[(task['dataset'],task['scene_name'])];j=type_index[task['question_type']]
[BEYOND] +        counts[i,j]+=1
[BEYOND] +        for total, rows in zip(totals,indices):
[BEYOND] +            r=rows[identity(task)]
[BEYOND] +            total[i,j]+=0 if r['status']!='complete' or r.get('derivation_error') else r['score']
[BEYOND] +    weights=np.random.default_rng(seed).multinomial(len(scenes),np.full(len(scenes),1/len(scenes)),size=repetitions)
[BEYOND] +    den=weights@counts
[BEYOND] +    draws=[np.divide(weights@total,den,out=np.full_like(den,np.nan),where=den>0) for total in totals]
[BEYOND] +    points=[total.sum(0)/counts.sum(0) for total in totals]
[BEYOND] +    return {typ:dict(items=int(counts[:,j].sum()),current=float(points[0][j]),parent=float(points[1][j]),
[BEYOND] +                     delta=float(points[0][j]-points[1][j]),**interval(draws[0][:,j]-draws[1][:,j]),
[BEYOND] +                     current_interval=interval(draws[0][:,j]),parent_interval=interval(draws[1][:,j]))
[BEYOND] +            for typ,j in type_index.items()}
[BEYOND] +
[BEYOND] +
[BEYOND] +def compare(tasks, current, reference, *, repetitions=10000, seed=544, partial=False):
[BEYOND] +    validate(tasks,current,reference,partial=partial)
[BEYOND] +    if repetitions <= 0 or type(repetitions) is not int or type(seed) is not int:
[BEYOND] +        raise ValueError('Invalid bootstrap parameters')
[BEYOND] +    if hashlib.sha256((ROOT/'kit/reader/official_score.py').read_bytes()).hexdigest()!=SCORER_SHA:
[BEYOND] +        raise ValueError('Accepted scorer differs')
[BEYOND] +    reports={}
[BEYOND] +    for arm in ARMS:
[BEYOND] +        a,b=current[arm],reference[arm]
[BEYOND] +        # This function is byte-identical to the one shipped for job 170037.
[BEYOND] +        pair=O.paired(tasks,a,b,repetitions=repetitions,seed=seed,allow_partial=partial)
[BEYOND] +        score_a=O.aggregate(tasks,a,current['ON16k'],repetitions=repetitions,seed=seed,allow_partial=partial)
[BEYOND] +        score_b=O.aggregate(tasks,b,reference['ON16k'],repetitions=repetitions,seed=seed,allow_partial=partial)
[BEYOND] +        subtypes=subtype_comparisons(tasks,a,b,repetitions,seed)
[BEYOND] +        reports[arm]=dict(role='primary' if arm=='B2048' else 'secondary',current=score_a,parent=score_b,
[BEYOND] +            paired=pair,subtypes=subtypes,
[BEYOND] +            facing={typ.removeprefix('object_rel_direction_'):value for typ,value in subtypes.items()
[BEYOND] +                    if typ in O.GROUPS['object_rel_direction']})
[BEYOND] +    return dict(schema=1,purpose='ranking only',decision=None,units='fraction',
[BEYOND] +        difference='current minus step 544',scorer=dict(path='kit/reader/official_score.py',function='paired',sha256=SCORER_SHA),arms=reports)
[BEYOND] +
[BEYOND] +
[BEYOND] +def load_packet(path, step):
[BEYOND] +    path=Path(path)
[BEYOND] +    marker=json.loads((path/'COMPLETE.json').read_text())
[BEYOND] +    spec=json.loads((path/'SPEC.json').read_text())
[BEYOND] +    request=json.loads((path/'a0/request.json').read_text())
[BEYOND] +    if (marker.get('mode')!='production' or marker.get('synthetic') is not False
[BEYOND] +        or marker.get('generation_synthetic') is not False or marker.get('items')!=679
[BEYOND] +        or (path/'FAILED.json').exists() or spec.get('step')!=step or request.get('mode')!='production'
[BEYOND] +        or request.get('reader',{}).get('step')!=step):
[BEYOND] +        raise ValueError('Incomplete, synthetic or wrong-step packet')
[BEYOND] +    artifact=spec.get('artifact',{})
[BEYOND] +    import re
[BEYOND] +    expected_path='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/'+('469ddece' if step==544 else '359fcc3c')+'/m'+str(step)+'/artifact.json'
[BEYOND] +    if (artifact.get('path')!=expected_path or artifact.get('kind')!='c1_export'
[BEYOND] +        or not isinstance(artifact.get('sha256'),str) or not re.fullmatch('[0-9a-f]{64}',artifact['sha256'])
[BEYOND] +        or artifact['sha256']=='0'*64
[BEYOND] +        or (step==544 and artifact['sha256']!='1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef')
[BEYOND] +        or request.get('models',{}).get('cp1m200')!=artifact):
[BEYOND] +        raise ValueError('Checkpoint identity differs')
[BEYOND] +    verification=request['reader'].get('export_verification',{})
[BEYOND] +    if (verification.get('status')!='VERIFIED' or verification.get('step')!=step
[BEYOND] +        or verification.get('artifact')!={k:artifact[k] for k in ('path','sha256')}):
[BEYOND] +        raise ValueError('Export verification differs')
[BEYOND] +    rows={arm:O.read_rows(path/'a0/results/0'/name) for arm,name in ARMS.items()}
[BEYOND] +    return rows,request
[BEYOND] +
[BEYOND] +
[BEYOND] +def packet_comparison(current, reference, step):
[BEYOND] +    if type(step) is not int or step not in (200,400,600,800,1000):
[BEYOND] +        raise ValueError('Invalid current step')
[BEYOND] +    a,request_a=load_packet(current,step);b,request_b=load_packet(reference,544)
[BEYOND] +    for field in PROTOCOL:
[BEYOND] +        equal_field(request_a,request_b,field)
[BEYOND] +    equal_field(request_a['models'],request_b['models'],'base')
[BEYOND] +    def without_paths(value):
[BEYOND] +        if isinstance(value,dict):return {k:without_paths(v) for k,v in value.items() if k!='path'}
[BEYOND] +        if isinstance(value,list):return [without_paths(v) for v in value]
[BEYOND] +        return value
[BEYOND] +    if without_paths(request_a['datasets'])!=without_paths(request_b['datasets']):
[BEYOND] +        raise ValueError('Dataset protocol differs')
[BEYOND] +    # Pin the requested protocol independently of the two packets agreeing.
[BEYOND] +    required=dict(max_seqs=32,inflight=16,max_tokens=16384,max_model_len=49152,temperature=0,thinking=True,gpus=1,smoke_items=0,engine_version='0.32.0')
[BEYOND] +    if any(request_a.get(k)!=v for k,v in required.items()):raise ValueError('Protocol differs')
[BEYOND] +    tasks=O.read_rows(ROOT/'kit/cohort/c5.jsonl')
[BEYOND] +    report=compare(tasks,a,b)
[BEYOND] +    report.update(current_step=step,parent_step=544,inputs={label:{arm:hashlib.sha256((Path(path)/'a0/results/0'/name).read_bytes()).hexdigest()
[BEYOND] +        for arm,name in ARMS.items()} for label,path in [('current',current),('parent',reference)]})
[BEYOND] +    return report
[BEYOND] +
[BEYOND] +
[BEYOND] +def main(argv=None):
[BEYOND] +    p=argparse.ArgumentParser(description=__doc__)
[BEYOND] +    p.add_argument('--current',required=True);p.add_argument('--reference',default=str(ROOT/'evidence/reference544'))
[BEYOND] +    p.add_argument('--step',type=int,choices=(200,400,600,800,1000),default=400);p.add_argument('--output',required=True)
[BEYOND] +    a=p.parse_args(argv);report=packet_comparison(a.current,a.reference,a.step)
[BEYOND] +    Path(a.output).write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
[BEYOND] +
[BEYOND] +
[BEYOND] +if __name__=='__main__':main()
```

### run_tests.py — BEYOND (new local file)

```diff
[BEYOND] +"""Install the immutable offline guard before importing any tests or kit module."""
[BEYOND] +from pathlib import Path
[BEYOND] +import os
[BEYOND] +import sys
[BEYOND] +import uuid
[BEYOND] +import json
[BEYOND] +ROOT=Path(__file__).resolve().parent
[BEYOND] +sys.path.insert(0,str(ROOT/'tests'))
[BEYOND] +import offline_guard
[BEYOND] +os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
[BEYOND] +os.environ['OPENBLAS_NUM_THREADS']='1'
[BEYOND] +os.environ['OMP_NUM_THREADS']='1'
[BEYOND] +os.environ['PYTHONDONTWRITEBYTECODE']='1'
[BEYOND] +import pytest
[BEYOND] +visited=set()
[BEYOND] +paired_path=str(ROOT/'paired.py')
[BEYOND] +def record(frame,event,arg):
[BEYOND] +    if frame.f_code.co_filename==paired_path and event=='line':visited.add(frame.f_lineno)
[BEYOND] +    return record if frame.f_code.co_filename==paired_path else None
[BEYOND] +class LineEvidence:
[BEYOND] +    @pytest.hookimpl(wrapper=True,tryfirst=True)
[BEYOND] +    def pytest_runtest_call(self,item):
[BEYOND] +        old=sys.gettrace()
[BEYOND] +        if item.path.name=='test_paired.py':sys.settrace(record)
[BEYOND] +        try:return (yield)
[BEYOND] +        finally:sys.settrace(old)
[BEYOND] +result=pytest.main(['-p','no:cacheprovider','--basetemp',str(ROOT/'evidence'/('pytest_'+uuid.uuid4().hex)),*sys.argv[1:]],plugins=[LineEvidence()])
[BEYOND] +(ROOT/'evidence/PAIRED_EXECUTED_LINES.json').write_text(json.dumps(sorted(visited))+'\n')
[BEYOND] +raise SystemExit(result)
```

### tests/offline_guard.py — BEYOND (new local file)

```diff
[BEYOND] +"""Deny real process and network operations before any test imports kit code.
[BEYOND] +
[BEYOND] +The audit hook cannot be uninstalled by a mock or bypassed with an absolute
[BEYOND] +binary path, shell=True, or a replacement PATH. Mocks never reach these events.
[BEYOND] +"""
[BEYOND] +import sys
[BEYOND] +
[BEYOND] +
[BEYOND] +class OfflineViolation(RuntimeError):
[BEYOND] +    pass
[BEYOND] +
[BEYOND] +
[BEYOND] +def deny_external(event, args):
[BEYOND] +    if (event in {'subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn',
[BEYOND] +                  'os.fork', 'os.forkpty'} or event.startswith('socket.')):
[BEYOND] +        raise OfflineViolation('Offline tests forbid process/network event: '+event)
[BEYOND] +
[BEYOND] +
[BEYOND] +sys.addaudithook(deny_external)
```

### tests/parity_local.py — BEYOND (new local file)

```diff
[BEYOND] +import offline_guard
[BEYOND] +from pathlib import Path
[BEYOND] +import json
[BEYOND] +import sys
[BEYOND] +from unittest.mock import patch
[BEYOND] +import uuid
[BEYOND] +ROOT=Path(__file__).resolve().parents[1]
[BEYOND] +K=ROOT/'kit'
[BEYOND] +for p in ('reader','reader/out','parity','proof'):sys.path.insert(0,str(K/p))
[BEYOND] +import fakes
[BEYOND] +fakes.install()
[BEYOND] +import prove_prompts
[BEYOND] +original=Path.read_text
[BEYOND] +
[BEYOND] +def read(path,*args,**kwargs):
[BEYOND] +    text=original(path,*args,**kwargs)
[BEYOND] +    if path==K/'launcher/MODELS.json':
[BEYOND] +        v=json.loads(text);v['cp1m200']['sha256']='a'*64;return json.dumps(v)
[BEYOND] +    return text
[BEYOND] +
[BEYOND] +with patch.object(Path,'read_text',read):
[BEYOND] +    result=prove_prompts.prove(ROOT/'evidence'/('parity_'+uuid.uuid4().hex),kit_root=K/'reader')
[BEYOND] +print(json.dumps(result))
```

### tests/proof_local.py — BEYOND (new local file)

```diff
[BEYOND] +"""Guarded in-process binding and synthetic proof using the kit's real worker and scorers."""
[BEYOND] +import offline_guard
[BEYOND] +import asyncio
[BEYOND] +from contextlib import ExitStack
[BEYOND] +import json
[BEYOND] +from pathlib import Path
[BEYOND] +import sys
[BEYOND] +from unittest.mock import patch
[BEYOND] +import uuid
[BEYOND] +ROOT=Path(__file__).resolve().parents[1]
[BEYOND] +K=ROOT/'kit'
[BEYOND] +for path in ('launcher','reader','reader/evaluator','cohort','proof'):
[BEYOND] +    sys.path.insert(0,str(K/path))
[BEYOND] +import fixtures as F
[BEYOND] +import official_adapter as A
[BEYOND] +import official_score as O
[BEYOND] +import frame_plan
[BEYOND] +import frame_stage
[BEYOND] +import data
[BEYOND] +import fakes
[BEYOND] +
[BEYOND] +
[BEYOND] +class PipeLoop(asyncio.SelectorEventLoop):
[BEYOND] +    """Use an anonymous pipe for asyncio wakeups; the audit guard forbids socketpair."""
[BEYOND] +    def _make_self_pipe(self):
[BEYOND] +        import os
[BEYOND] +        self._read_fd,self._write_fd=os.pipe2(os.O_NONBLOCK|os.O_CLOEXEC)
[BEYOND] +        self._internal_fds+=1
[BEYOND] +        self._add_reader(self._read_fd,self._read_from_self)
[BEYOND] +    def _read_from_self(self):
[BEYOND] +        import os
[BEYOND] +        try:os.read(self._read_fd,4096)
[BEYOND] +        except BlockingIOError:pass
[BEYOND] +    def _write_to_self(self):
[BEYOND] +        import os
[BEYOND] +        try:os.write(self._write_fd,b'0')
[BEYOND] +        except BlockingIOError:pass
[BEYOND] +    def _close_self_pipe(self):
[BEYOND] +        import os
[BEYOND] +        self._remove_reader(self._read_fd)
[BEYOND] +        os.close(self._read_fd);os.close(self._write_fd);self._internal_fds-=1
[BEYOND] +
[BEYOND] +
[BEYOND] +def run(work):
[BEYOND] +    work=Path(work);work.mkdir(parents=True)
[BEYOND] +    fixture=work/'fixture';fixture.mkdir()
[BEYOND] +    base,bm,export,artifact=F.models(fixture,fixture/'e/artifact.json')
[BEYOND] +    models=dict(base=dict(kind='snapshot',path=str(base),manifest=dict(path=str(bm),sha256=F.sha(bm))),
[BEYOND] +                cp1m200=dict(kind='c1_export',path=str(artifact),sha256=F.sha(artifact)))
[BEYOND] +    reference=(ROOT/'evidence/reference544/a0/PROMPT_PINS.json').read_bytes()
[BEYOND] +    binds=[]
[BEYOND] +    with patch.object(A,'BASE_SHA',F.sha(bm)):
[BEYOND] +        for step in (200,400,600,800,1000):
[BEYOND] +            value=json.loads(artifact.read_text());value['step']=step;F.js(artifact,value)
[BEYOND] +            models['cp1m200']['sha256']=F.sha(artifact)
[BEYOND] +            dest=work/('bind'+str(step))
[BEYOND] +            cfg=A.bind(dest,models,K/'inputs/i1.json',work/'v',step=step)
[BEYOND] +            assert (dest/'PROMPT_PINS.json').read_bytes()==reference
[BEYOND] +            assert cfg['max_seqs']==32 and cfg['inflight']==16 and len(A.tasks(cfg))==679
[BEYOND] +            binds.append(dict(step=step,items=679,prompt_bytes_equal=True,checker=cfg['reader']['export_verification']['status']))
[BEYOND] +        value=json.loads(artifact.read_text());value['step']=400;F.js(artifact,value)
[BEYOND] +        models['cp1m200']['sha256']=F.sha(artifact)
[BEYOND] +        selected=F.select(O.read_rows(K/'cohort/c5.jsonl'))
[BEYOND] +        video_info=json.loads((K/'inputs/i3.json').read_text());manifest=[]
[BEYOND] +        for i,scene in enumerate(sorted({r['scene'] for r in selected})):
[BEYOND] +            file=F.video(work/'v'/(scene+'.mp4'),i)
[BEYOND] +            video_info['files'][scene].update(sha256=F.sha(file),bytes=file.stat().st_size)
[BEYOND] +            manifest.append(dict(relative_path=file.name,sha256=F.sha(file)))
[BEYOND] +        videos=F.js(work/'v.json',video_info);manifest_path=F.js(work/'manifest.json',manifest)
[BEYOND] +        original_dataset=A.dataset
[BEYOND] +        def dataset(rows):
[BEYOND] +            spec=original_dataset(rows);spec['videos']=dict(path=str(videos),sha256=F.sha(videos));return spec
[BEYOND] +        with patch.object(A,'dataset',dataset),patch.object(data,'REVSI999_VIDEOS',{32:F.sha(videos)}):
[BEYOND] +            dest=work/'proof';cfg=A.bind(dest,models,K/'inputs/i1.json',work/'v',mode='proof',step=400)
[BEYOND] +            tasks=A.tasks(cfg)
[BEYOND] +            plan=F.js(work/'plan.json',frame_plan.compute(work/'v',manifest_path,workers=2))
[BEYOND] +            result=frame_stage.stage(dest/'request.json',dest/'frames',2)
[BEYOND] +            assert result['errors']==0
[BEYOND] +            index_sha=F.sha(dest/'frames/0.json')
[BEYOND] +            check=frame_plan.check(tasks,dest/'frames',plan,index_sha)
[BEYOND] +            F.js(dest/'BIND_STATUS.json',dict(ready=True,frames_sha256=index_sha,frame_plan=check))
[BEYOND] +            processor,engine=fakes.install()
[BEYOND] +            import scoring
[BEYOND] +            scoring._METRIC_CLASS=None
[BEYOND] +            def runner(coro):
[BEYOND] +                with asyncio.Runner(loop_factory=PipeLoop) as runner:return runner.run(coro)
[BEYOND] +            with patch.object(fakes,'install_engine',lambda ids:setattr(engine,'selected',ids)),patch.object(A.asyncio,'run',runner):
[BEYOND] +                merged=A.launch(dest)
[BEYOND] +            assert merged['parity_pass']
[BEYOND] +            cohort=work/'selected.jsonl';cohort.write_text(''.join(json.dumps(r)+'\n' for r in selected))
[BEYOND] +            O.score_run(dest,cohort,work/'report',allow_partial=True)
[BEYOND] +            from selection import verify_results
[BEYOND] +            checked=verify_results(work/'report',[t['example_id'] for t in tasks])
[BEYOND] +    report=dict(passed=True,synthetic=True,real_processor=False,real_export=False,binds=binds,
[BEYOND] +                frame_plan=check,checks=checked,boundaries=['miniature weights','synthetic tier-32 clips','fake processor and engine','pipe-based asyncio wakeup'])
[BEYOND] +    F.js(work/'RESULT.json',report)
[BEYOND] +    return report
[BEYOND] +
[BEYOND] +
[BEYOND] +if __name__=='__main__':
[BEYOND] +    print(json.dumps(run(ROOT/'evidence'/('local_proof_'+uuid.uuid4().hex)),indent=2))
```

### tests/test_export.py — BEYOND (new local file)

```diff
[BEYOND] +import offline_guard
[BEYOND] +import ast
[BEYOND] +import base64
[BEYOND] +import importlib.util
[BEYOND] +from contextlib import contextmanager
[BEYOND] +import copy
[BEYOND] +import hashlib
[BEYOND] +import io
[BEYOND] +import json
[BEYOND] +from pathlib import Path
[BEYOND] +import subprocess
[BEYOND] +import sys
[BEYOND] +import re
[BEYOND] +import tarfile
[BEYOND] +from types import SimpleNamespace as NS
[BEYOND] +import unittest
[BEYOND] +from unittest.mock import patch
[BEYOND] +import uuid
[BEYOND] +
[BEYOND] +ROOT=Path(__file__).resolve().parents[1]
[BEYOND] +sys.path.insert(0,str(ROOT/'kit/launcher'))
[BEYOND] +import orchard_launcher as L
[BEYOND] +import orchard_stage as S
[BEYOND] +import orchard_job as J
[BEYOND] +import orchard_results as R
[BEYOND] +import export_stage as E
[BEYOND] +import chain_save as A
[BEYOND] +import return_io
[BEYOND] +
[BEYOND] +
[BEYOND] +def directory():
[BEYOND] +    p=ROOT/'evidence'/('test_'+uuid.uuid4().hex)
[BEYOND] +    p.mkdir();return p
[BEYOND] +
[BEYOND] +
[BEYOND] +def archive(root, bad=None):
[BEYOND] +    path=root/'input.tar'
[BEYOND] +    names=['m100/artifact.json','m100/heads.pt','m100/full_weights/full_weights.json']
[BEYOND] +    if bad=='missing':names.pop()
[BEYOND] +    if bad=='traversal':names.append('m100/../evil')
[BEYOND] +    if bad=='absolute':names.append('/m100/evil')
[BEYOND] +    if bad=='step':names.append('m200/evil')
[BEYOND] +    if bad=='extra':names.append('m100/extra')
[BEYOND] +    if bad=='duplicate':names.append(names[0])
[BEYOND] +    if bad=='collision':names.append('m100/full_weights/full_weights.json/evil')
[BEYOND] +    with tarfile.open(path,'w') as tf:
[BEYOND] +        for name in names:
[BEYOND] +            item=tarfile.TarInfo(name);item.size=2;tf.addfile(item,io.BytesIO(b'{}'))
[BEYOND] +        if bad in ('symlink','hardlink','fifo'):
[BEYOND] +            item=tarfile.TarInfo('m100/full_weights/evil')
[BEYOND] +            item.type={'symlink':tarfile.SYMTYPE,'hardlink':tarfile.LNKTYPE,'fifo':tarfile.FIFOTYPE}[bad]
[BEYOND] +            item.linkname='artifact.json';tf.addfile(item)
[BEYOND] +    done=root/'COMPLETE.json';done.write_text(json.dumps(dict(object='gs://x',bytes=path.stat().st_size,sha256=S.sha(path))))
[BEYOND] +    return path,done
[BEYOND] +
[BEYOND] +
[BEYOND] +class ExportTests(unittest.TestCase):
[BEYOND] +    def stage_fixture(self,root,path,done):
[BEYOND] +        args=NS(root=str(root/'job'),run='359fcc3c',step=100,tar=str(path),done=str(done),full=True,bwrap='unused')
[BEYOND] +        with patch.object(E.T,'writable',side_effect=lambda p:Path(p)),\
[BEYOND] +             patch.object(E,'completed_local',side_effect=lambda p,tar=False:Path(p)),\
[BEYOND] +             patch.object(S,'room'),patch.object(E,'run_export_checker',return_value=dict(status='VERIFIED',step=100)):
[BEYOND] +            return E.stage_export(args)
[BEYOND] +
[BEYOND] +    def test_archive_admission(self):
[BEYOND] +        root=directory();path,done=archive(root)
[BEYOND] +        result=self.stage_fixture(root,path,done)
[BEYOND] +        self.assertEqual(result['status'],'complete');self.assertEqual(result['checker_mode'],'full')
[BEYOND] +        self.assertEqual(result['tar_sha256'],S.sha(path))
[BEYOND] +        with self.assertRaisesRegex(ValueError,'exists'):self.stage_fixture(root,path,done)
[BEYOND] +
[BEYOND] +    def test_archive_attacks(self):
[BEYOND] +        for bad in ('missing','traversal','absolute','step','extra','duplicate','collision','symlink','hardlink','fifo'):
[BEYOND] +            with self.subTest(bad=bad):
[BEYOND] +                root=directory();path,done=archive(root,bad)
[BEYOND] +                with self.assertRaises(ValueError):self.stage_fixture(root,path,done)
[BEYOND] +                self.assertFalse((root/'job/exports/359fcc3c_m100').exists())
[BEYOND] +
[BEYOND] +    def test_digest_before_extraction(self):
[BEYOND] +        for field,value in [('sha256','0'*64),('bytes',1)]:
[BEYOND] +            root=directory();path,done=archive(root)
[BEYOND] +            info=json.loads(done.read_text());info[field]=value;done.write_text(json.dumps(info))
[BEYOND] +            with self.assertRaises(ValueError):self.stage_fixture(root,path,done)
[BEYOND] +            self.assertFalse((root/'job/exports/359fcc3c_m100').exists())
[BEYOND] +
[BEYOND] +    def test_full_checker_on_miniature_tensor(self):
[BEYOND] +        import importlib.util,struct
[BEYOND] +        spec=importlib.util.spec_from_file_location('mini_checker',ROOT/'kit/reader/out/export_check.py')
[BEYOND] +        checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
[BEYOND] +        root=directory();base=root/'base';weights=root/'m100/full_weights';base.mkdir();weights.mkdir(parents=True)
[BEYOND] +        def tensor(p):
[BEYOND] +            h=json.dumps({'weight':dict(dtype='BF16',shape=[1],data_offsets=[0,2])}).encode()
[BEYOND] +            p.write_bytes(struct.pack('<Q',len(h))+h+b'00')
[BEYOND] +        tensor(base/'model.safetensors');tensor(weights/'model.safetensors')
[BEYOND] +        idx=weights/'model.safetensors.index.json';idx.write_text(json.dumps(dict(weight_map={'weight':'model.safetensors'})))
[BEYOND] +        manifest=weights/'full_weights.json';manifest.write_text(json.dumps(dict(schema='full-ft-export-v1',dtype='bfloat16',
[BEYOND] +            index=dict(name=idx.name,sha256=S.sha(idx)),tensor_count=1,
[BEYOND] +            files=[dict(name='model.safetensors',bytes=(weights/'model.safetensors').stat().st_size,
[BEYOND] +                        sha256=S.sha(weights/'model.safetensors'),tensors=1)])))
[BEYOND] +        artifact=weights.parent/'artifact.json';artifact.write_text(json.dumps(dict(schema='carrier-c1-artifact-v1',step=100,
[BEYOND] +            full_weights=dict(path=str(manifest),sha256=S.sha(manifest)))))
[BEYOND] +        self.assertEqual(checker.check_export(artifact,S.sha(artifact),base,100)['status'],'VERIFIED')
[BEYOND] +        (weights/'model.safetensors').write_bytes((weights/'model.safetensors').read_bytes()[:-2]+b'11')
[BEYOND] +        with self.assertRaisesRegex(ValueError,'Shard hash'):checker.check_export(artifact,S.sha(artifact),base,100)
[BEYOND] +
[BEYOND] +    def test_offline_guard_blocks_real_commands_and_network(self):
[BEYOND] +        import socket
[BEYOND] +        for argv in (['gcloud','storage','cp','fake','gs://fake'],
[BEYOND] +                     ['/usr/bin/gcloud','version'],['ssh','fake'],['sbatch','fake']):
[BEYOND] +            with self.assertRaises(offline_guard.OfflineViolation):subprocess.run(argv)
[BEYOND] +        with self.assertRaises(offline_guard.OfflineViolation):
[BEYOND] +            subprocess.run('gcloud version',shell=True)
[BEYOND] +        with self.assertRaises(offline_guard.OfflineViolation):socket.socket()
[BEYOND] +
[BEYOND] +    def test_stage_function_is_exact_reviewed_body(self):
[BEYOND] +        original=Path('/scratch/jjyeung/orch_n30/trin_read/build_t5/milestone.py').read_text()
[BEYOND] +        candidate=(ROOT/'kit/launcher/export_stage.py').read_text()
[BEYOND] +        def body(s):return ast.dump(next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='stage_export'),include_attributes=False)
[BEYOND] +        self.assertEqual(body(original),body(candidate))
[BEYOND] +
[BEYOND] +    def test_ordered_cloud_stream_requires_whole_digest_before_stage(self):
[BEYOND] +        for corrupt in (False, True):
[BEYOND] +            root=directory();(root/'archives').mkdir();(root/'bootstrap').mkdir()
[BEYOND] +            chunks=[b'one',b'two',b'three',b'four'];body=b''.join(chunks)
[BEYOND] +            uri='gs://cmu-gpucloud-jjyeung/q8/8865619b/359fcc3c_m100.tar'
[BEYOND] +            receipt=root/'input.done'
[BEYOND] +            digest='0'*64 if corrupt else hashlib.sha256(body).hexdigest()
[BEYOND] +            receipt.write_text(f'q8/8865619b/359fcc3c_m100.tar {len(body)} {digest}\n')
[BEYOND] +            config=dict(spec=dict(step=100,artifact={},models={},package=str(J.SJ/'a0/p')),assets=dict(gcloud_config='fixture'))
[BEYOND] +            (J.physical(root,config['spec']['package'])/'launcher').mkdir(parents=True)
[BEYOND] +            observed=[]
[BEYOND] +            @contextmanager
[BEYOND] +            def stream(argv,env,log):
[BEYOND] +                observed.append(argv[-1]);yield io.BytesIO(chunks[len(observed)-1])
[BEYOND] +            def path(value):
[BEYOND] +                return receipt if str(value).startswith('/project/community/') else Path(value)
[BEYOND] +            # The fixed receipt path is composed with / after Path construction.
[BEYOND] +            fake_receipt_dir=root/'receipts';fake_receipt_dir.mkdir()
[BEYOND] +            (fake_receipt_dir/'gcs_359fcc3c_m100.done').write_bytes(receipt.read_bytes())
[BEYOND] +            def path(value):
[BEYOND] +                return fake_receipt_dir if str(value).startswith('/project/community/') else Path(value)
[BEYOND] +            with patch.object(E,'Path',side_effect=path),patch.object(S,'room'),\
[BEYOND] +                 patch.object(S,'process_stream',side_effect=stream),\
[BEYOND] +                 patch.object(E,'stage_export',return_value=dict(artifact_sha256='a'*64)) as stage:
[BEYOND] +                if corrupt:
[BEYOND] +                    with self.assertRaisesRegex(ValueError,'Whole archive'):E.fetch_and_stage(root,config)
[BEYOND] +                    stage.assert_not_called();self.assertFalse((root/'archives/export.tar').exists())
[BEYOND] +                else:
[BEYOND] +                    E.fetch_and_stage(root,config)
[BEYOND] +                    self.assertTrue(stage.call_args.args[0].full)
[BEYOND] +                    self.assertEqual((root/'archives/export.tar').read_bytes(),body)
[BEYOND] +                    self.assertEqual(config['spec']['artifact']['sha256'],'a'*64)
[BEYOND] +                    self.assertEqual((root/'archives/COMPLETE.done').read_bytes(),receipt.read_bytes())
[BEYOND] +                    self.assertEqual(json.loads((root/'archives/COMPLETE.json').read_text()),
[BEYOND] +                                     E.parse_done(receipt.read_bytes(),'359fcc3c',100))
[BEYOND] +            self.assertEqual(observed,[uri+'.part%02d-of-04'%i for i in range(4)])
[BEYOND] +
[BEYOND] +    def test_wrong_done_refused_before_cloud_or_disk_reservation(self):
[BEYOND] +        root=directory();receipt=root/'gcs_359fcc3c_m100.done'
[BEYOND] +        receipt.write_text('q8/8865619b/469ddece_m100.tar 123 '+'a'*64+'\n')
[BEYOND] +        def path(value):
[BEYOND] +            return root if str(value).startswith('/project/community/') else Path(value)
[BEYOND] +        with patch.object(E,'Path',side_effect=path),patch.object(S,'room') as room,\
[BEYOND] +             patch.object(S,'process_stream') as stream:
[BEYOND] +            with self.assertRaisesRegex(ValueError,'identity'):
[BEYOND] +                E.fetch_and_stage(root,dict(spec=dict(step=100)))
[BEYOND] +        room.assert_not_called();stream.assert_not_called()
```

### tests/test_paired.py — BEYOND (new local file)

```diff
[BEYOND] +import offline_guard
[BEYOND] +import copy
[BEYOND] +import json
[BEYOND] +from pathlib import Path
[BEYOND] +import sys
[BEYOND] +import unittest
[BEYOND] +from unittest.mock import patch
[BEYOND] +import uuid
[BEYOND] +sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
[BEYOND] +import paired as P
[BEYOND] +
[BEYOND] +
[BEYOND] +def fixture(value=1):
[BEYOND] +    tasks=[]
[BEYOND] +    for i,typ in enumerate(t for ts in P.O.GROUPS.values() for t in ts):
[BEYOND] +        question='x and facing the x' if 'forward' in typ else 'x facing in the opposite direction of x'
[BEYOND] +        tasks.append(dict(id=i,example_id=str(i),dataset='fixture',scene_name=str(i%3),question_type=typ,
[BEYOND] +                          question=question,ground_truth='A'))
[BEYOND] +    rows=[dict(t,**{k:'fixed' for k in P.META},prompt_tokens=7,media=dict(pixel_sha256='x',frame_receipt={'path':'a'}),status='complete',score=value) for t in tasks]
[BEYOND] +    return tasks,{arm:copy.deepcopy(rows) for arm in P.ARMS}
[BEYOND] +
[BEYOND] +
[BEYOND] +def directory():
[BEYOND] +    p=P.ROOT/'evidence'/('pair_'+uuid.uuid4().hex);p.mkdir();return p
[BEYOND] +
[BEYOND] +
[BEYOND] +class PairedTests(unittest.TestCase):
[BEYOND] +    def test_known_difference_all_outputs_and_determinism(self):
[BEYOND] +        t,a=fixture();_,b=fixture(0)
[BEYOND] +        r=P.compare(t,a,b,repetitions=10000,partial=True)
[BEYOND] +        self.assertEqual(r,P.compare(t,a,b,repetitions=10000,partial=True))
[BEYOND] +        self.assertIsNone(r['decision'])
[BEYOND] +        for arm,v in r['arms'].items():
[BEYOND] +            self.assertEqual(v['current']['five_category_mean']['score'],1)
[BEYOND] +            self.assertEqual(set(v['facing']),{'forward_easy','forward_hard','backward_easy','backward_hard'})
[BEYOND] +            for x in [*v['paired']['comparisons'].values(),*v['subtypes'].values()]:
[BEYOND] +                self.assertEqual(x['delta'],1);self.assertEqual(x['percentile_95'],[1,1])
[BEYOND] +        identity=P.compare(t,a,a,repetitions=20,partial=True)
[BEYOND] +        self.assertEqual(identity['arms']['B2048']['paired']['comparisons']['five_category_mean']['percentile_95'],[0,0])
[BEYOND] +
[BEYOND] +    def test_reference_completeness(self):
[BEYOND] +        rows,_=P.load_packet(P.ROOT/'evidence/reference544',544)
[BEYOND] +        tasks=P.O.read_rows(P.ROOT/'kit/cohort/c5.jsonl')
[BEYOND] +        P.validate(tasks,rows,rows)
[BEYOND] +        self.assertTrue(all(len(v)==679 and all(r['status']=='complete' for r in v) for v in rows.values()))
[BEYOND] +
[BEYOND] +    def test_cluster_weights_and_zero_denominators(self):
[BEYOND] +        import numpy as np
[BEYOND] +        t,a=fixture();_,b=fixture(0)
[BEYOND] +        for rows in a.values():
[BEYOND] +            for r in rows:r['score']=int(r['scene_name']=='0')
[BEYOND] +        r=P.compare(t,a,b,repetitions=100,partial=True)
[BEYOND] +        for typ,x in r['arms']['B2048']['subtypes'].items():
[BEYOND] +            self.assertLess(x['valid_replicates'],100)
[BEYOND] +        self.assertEqual(P.interval(np.array([np.nan])),dict(percentile_95=None,valid_replicates=0))
[BEYOND] +        # The equal category/subtype mean is not the item-weighted mean.
[BEYOND] +        expected=sum(sum(next(r['score'] for r in a['B2048'] if r['question_type']==k) for k in ks)/len(ks) for ks in P.O.GROUPS.values())/5
[BEYOND] +        self.assertAlmostEqual(r['arms']['B2048']['current']['five_category_mean']['score'],expected)
[BEYOND] +
[BEYOND] +    def test_errors_and_derivation_errors_score_zero(self):
[BEYOND] +        t,a=fixture();_,b=fixture(0)
[BEYOND] +        for arm in a:
[BEYOND] +            a[arm][0].update(status='error',error='synthetic',score=None)
[BEYOND] +            a[arm][1]['derivation_error']=True
[BEYOND] +        r=P.compare(t,a,b,repetitions=10,partial=True)
[BEYOND] +        self.assertEqual(r['arms']['B2048']['subtypes'][t[0]['question_type']]['delta'],0)
[BEYOND] +        self.assertEqual(r['arms']['B2048']['subtypes'][t[1]['question_type']]['delta'],0)
[BEYOND] +
[BEYOND] +    def test_every_metadata_field_on_either_input(self):
[BEYOND] +        t,a=fixture()
[BEYOND] +        for side in (0,1):
[BEYOND] +            for arm in P.ARMS:
[BEYOND] +                for field in [*t[0],*P.META,'media','prompt_tokens']:
[BEYOND] +                    if field=='prompt_tokens' and arm!='ON16k':continue
[BEYOND] +                    for missing in (True,False):
[BEYOND] +                        pair=[copy.deepcopy(a),copy.deepcopy(a)]
[BEYOND] +                        if missing:pair[side][arm][0].pop(field,None)
[BEYOND] +                        else:pair[side][arm][0][field]='changed'
[BEYOND] +                        with self.subTest(side=side,arm=arm,field=field,missing=missing):
[BEYOND] +                            with self.assertRaises(ValueError):P.validate(t,*pair,partial=True)
[BEYOND] +
[BEYOND] +    def test_membership_id_types_status_scores_and_schema(self):
[BEYOND] +        t,a=fixture()
[BEYOND] +        mutations=[lambda p:p.pop('B4096'),lambda p:p.update(extra=[]),
[BEYOND] +            lambda p:p['B2048'].pop(),lambda p:p['ON16k'].append(p['ON16k'][0]),
[BEYOND] +            lambda p:p['B2048'][0].update(id=100,example_id='100'),
[BEYOND] +            lambda p:p['B2048'].__setitem__(0,None),
[BEYOND] +            lambda p:p['ON16k'][0].update(status='pending')]
[BEYOND] +        mutations += [lambda p,v=v:p['B2048'][0].update(score=v) for v in (True,None,float('nan'),float('inf'),-1,2,'1')]
[BEYOND] +        for mutate in mutations:
[BEYOND] +            b=copy.deepcopy(a);mutate(b)
[BEYOND] +            with self.assertRaises(ValueError):P.validate(t,a,b,partial=True)
[BEYOND] +        with self.assertRaises(ValueError):P.validate(t,a,a)
[BEYOND] +        t[0]['question_type']='foreign'
[BEYOND] +        with self.assertRaises(ValueError):P.validate(t,a,a,partial=True)
[BEYOND] +
[BEYOND] +    def test_invalid_bootstrap_and_scorer_pin(self):
[BEYOND] +        t,a=fixture()
[BEYOND] +        for reps,seed in [(0,544),(1.5,544),(5,'x')]:
[BEYOND] +            with self.assertRaises(ValueError):P.compare(t,a,a,repetitions=reps,seed=seed,partial=True)
[BEYOND] +        with patch.object(P,'SCORER_SHA','0'*64):
[BEYOND] +            with self.assertRaises(ValueError):P.compare(t,a,a,repetitions=1,partial=True)
[BEYOND] +
[BEYOND] +    def test_packet_validation_and_cli(self):
[BEYOND] +        root=directory();(root/'a0/results/0').mkdir(parents=True)
[BEYOND] +        marker=dict(mode='production',synthetic=False,generation_synthetic=False,items=679)
[BEYOND] +        artifact=dict(kind='c1_export',path='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/359fcc3c/m400/artifact.json',sha256='a'*64)
[BEYOND] +        request=dict(mode='production',models=dict(cp1m200=artifact),reader=dict(step=400,export_verification=dict(status='VERIFIED',step=400,artifact={k:artifact[k] for k in ('path','sha256')})))
[BEYOND] +        def write():
[BEYOND] +            for name,value in [('COMPLETE.json',marker),('SPEC.json',dict(step=400,artifact=artifact)),('a0/request.json',request)]:
[BEYOND] +                (root/name).write_text(json.dumps(value))
[BEYOND] +            for name in P.ARMS.values():(root/'a0/results/0'/name).write_text('')
[BEYOND] +        write();P.load_packet(root,400)
[BEYOND] +        for key,bad in [('mode','proof'),('synthetic',True),('generation_synthetic',True),('items',678)]:
[BEYOND] +            good=marker[key];marker[key]=bad;write()
[BEYOND] +            with self.assertRaises(ValueError):P.load_packet(root,400)
[BEYOND] +            marker[key]=good
[BEYOND] +        write()
[BEYOND] +        with self.assertRaises(ValueError):P.load_packet(root,544)
[BEYOND] +        request['reader']['step']=200;write()
[BEYOND] +        with self.assertRaises(ValueError):P.load_packet(root,400)
[BEYOND] +        request['reader']['step']=400;request['mode']='proof';write()
[BEYOND] +        with self.assertRaises(ValueError):P.load_packet(root,400)
[BEYOND] +        request['mode']='production';write();(root/'FAILED.json').write_text('{}')
[BEYOND] +        with self.assertRaises(ValueError):P.load_packet(root,400)
[BEYOND] +        with patch.object(P,'packet_comparison',return_value={'decision':None}) as compare:
[BEYOND] +            P.main(['--current',str(root),'--output',str(root/'result.json')]);compare.assert_called_once()
[BEYOND] +            self.assertEqual(json.loads((root/'result.json').read_text()),{'decision':None})
[BEYOND] +
[BEYOND] +    def test_packet_protocol_and_provenance(self):
[BEYOND] +        for step in (True,544,'400'):
[BEYOND] +            with self.assertRaises(ValueError):P.packet_comparison('a','b',step)
[BEYOND] +        t,a=fixture();cfg=dict(cells=[],gpus=1,max_tokens=16384,temperature=0,thinking=True,max_model_len=49152,max_seqs=32,inflight=16,smoke_items=0,engine_version='0.32.0',mode='production',models=dict(base={}),datasets=[dict(rows=dict(path='fixture',sha256='a'*64))])
[BEYOND] +        for field in P.PROTOCOL:
[BEYOND] +            other=copy.deepcopy(cfg);other[field]='bad'
[BEYOND] +            with patch.object(P,'load_packet',side_effect=[(a,cfg),(a,other)]):
[BEYOND] +                with self.assertRaises(ValueError):P.packet_comparison('a','b',400)
[BEYOND] +        bad=dict(cfg,max_seqs=128)
[BEYOND] +        with patch.object(P,'load_packet',return_value=(a,bad)):
[BEYOND] +            with self.assertRaises(ValueError):P.packet_comparison('a','b',400)
[BEYOND] +        with patch.object(P,'load_packet',return_value=(a,cfg)),patch.object(P,'compare',return_value={}),patch.object(P.O,'read_rows',return_value=t):
[BEYOND] +            r=P.packet_comparison(P.ROOT/'evidence/reference544',P.ROOT/'evidence/reference544',400)
[BEYOND] +            self.assertEqual(r['current_step'],400);self.assertEqual(set(r['inputs']['current']),set(P.ARMS))
[BEYOND] +
[BEYOND] +    def test_text_diagnostic_refuses_unknown_wording(self):
[BEYOND] +        t,a=fixture()
[BEYOND] +        for task in t:
[BEYOND] +            if 'direction' in task['question_type']:task['question']='unrecognized'
[BEYOND] +        for rows in a.values():
[BEYOND] +            for row,task in zip(rows,t):row['question']=task['question']
[BEYOND] +        with self.assertRaises(ValueError):P.compare(t,a,a,repetitions=1,partial=True)
[BEYOND] +
[BEYOND] +    def test_checkpoint_and_export_verification_refusals(self):
[BEYOND] +        ref=P.ROOT/'evidence/reference544'
[BEYOND] +        original=json.loads((ref/'SPEC.json').read_text())
[BEYOND] +        request=json.loads((ref/'a0/request.json').read_text())
[BEYOND] +        original_read=Path.read_text
[BEYOND] +        cases=[]
[BEYOND] +        for field,value in [('kind','snapshot'),('path','/wrong'),('sha256',None),('sha256','x'),('sha256','0'*64),('sha256','a'*64)]:
[BEYOND] +            spec=copy.deepcopy(original);spec['artifact'][field]=value;cases.append((spec,request))
[BEYOND] +        wrong=copy.deepcopy(request);wrong['models']['cp1m200']['path']='/wrong';cases.append((original,wrong))
[BEYOND] +        for field,value in [('status','HEADER_ONLY_NOT_VERIFIED'),('step',400),('artifact',{})]:
[BEYOND] +            wrong=copy.deepcopy(request);wrong['reader']['export_verification'][field]=value;cases.append((original,wrong))
[BEYOND] +        for spec,req in cases:
[BEYOND] +            def read(path,*args,**kwargs):
[BEYOND] +                if path==ref/'SPEC.json':return json.dumps(spec)
[BEYOND] +                if path==ref/'a0/request.json':return json.dumps(req)
[BEYOND] +                return original_read(path,*args,**kwargs)
[BEYOND] +            with patch.object(Path,'read_text',read):
[BEYOND] +                with self.assertRaises(ValueError):P.load_packet(ref,544)
[BEYOND] +        a,rows=fixture()
[BEYOND] +        cfg=dict(cells=[],gpus=1,max_tokens=16384,temperature=0,thinking=True,max_model_len=49152,max_seqs=32,inflight=16,smoke_items=0,engine_version='0.32.0',mode='production',models=dict(base={}),datasets=[])
[BEYOND] +        for field,value in [('models',dict(base={'different':1})),('datasets',[{}])]:
[BEYOND] +            wrong=dict(cfg,**{field:value})
[BEYOND] +            with patch.object(P,'load_packet',side_effect=[(rows,cfg),(rows,wrong)]):
[BEYOND] +                with self.assertRaises(ValueError):P.packet_comparison('a','b',400)
[BEYOND] +
[BEYOND] +
[BEYOND] +    def test_media_dict_mismatch_and_script_help(self):
[BEYOND] +        t,a=fixture();b=copy.deepcopy(a);b['B2048'][0]['media']['pixel_sha256']='other'
[BEYOND] +        with self.assertRaisesRegex(ValueError,'Media metadata'):P.validate(t,a,b,partial=True)
[BEYOND] +        import runpy
[BEYOND] +        with patch.object(sys,'argv',['paired.py','--help']):
[BEYOND] +            with self.assertRaises(SystemExit) as e:runpy.run_path(str(P.ROOT/'paired.py'),run_name='__main__')
[BEYOND] +        self.assertEqual(e.exception.code,0)
```

### tests/test_prepare.py — BEYOND (new local file)

```diff
[BEYOND] +import offline_guard
[BEYOND] +import ast
[BEYOND] +import copy
[BEYOND] +import io
[BEYOND] +import json
[BEYOND] +from pathlib import Path
[BEYOND] +import sys
[BEYOND] +import unittest
[BEYOND] +from unittest.mock import patch
[BEYOND] +import uuid
[BEYOND] +ROOT=Path(__file__).resolve().parents[1]
[BEYOND] +sys.path.insert(0,str(ROOT/'kit/launcher'))
[BEYOND] +import orchard_launcher as L
[BEYOND] +import export_stage as E
[BEYOND] +import opaque_io
[BEYOND] +
[BEYOND] +
[BEYOND] +def directory():
[BEYOND] +    p=ROOT/'evidence'/('prepare_'+uuid.uuid4().hex);p.mkdir();return p
[BEYOND] +
[BEYOND] +
[BEYOND] +class PrepareTests(unittest.TestCase):
[BEYOND] +    def test_all_steps_pair_and_identity_refusals(self):
[BEYOND] +        for step in (200,400,600,800,1000):
[BEYOND] +            p=directory();token=uuid.uuid4().hex[:12]
[BEYOND] +            a=L.prepare(token,p/'proof',mode='proof',step=step,media_root='/project/community/jjyeung/okh7/313db5a47f11ff0c')
[BEYOND] +            (p/'proof/SUBMIT.out').write_text('170035\n');L.submission_record(p/'proof')
[BEYOND] +            b=L.prepare(uuid.uuid4().hex[:12],p/'production',step=step,proof_destination=p/'proof',media_root=a['media_root'])
[BEYOND] +            for cfg,name in [(a,'proof'),(b,'production')]:
[BEYOND] +                L.validate_request(cfg);L.validate_batch((p/name/'BATCH.sh').read_text(),cfg)
[BEYOND] +                command=L.submit_command(cfg['token'],proof=name=='proof',afterok=cfg['afterok'])
[BEYOND] +                compile(command[-1],'<operator>','exec')
[BEYOND] +            args=L.submit_argv(None,b['token'],afterok=b['afterok'])
[BEYOND] +            self.assertIn('--dependency=afterok:170035',args)
[BEYOND] +            self.assertIn('--time=00:25:00',args)
[BEYOND] +            self.assertEqual(a['wall_seconds'],1260);self.assertEqual(b['wall_seconds'],1500)
[BEYOND] +            self.assertIn('359fcc3c/m'+str(step),b['spec']['artifact']['path'])
[BEYOND] +            for word in ('revsi','vsi','distill','d0','qgen','split'):
[BEYOND] +                # Hex tokens can contain d0; inspect lexical components, not arbitrary hex substrings.
[BEYOND] +                self.assertNotIn(word,' '.join(x for x in args if not x.startswith('--job-name')).lower())
[BEYOND] +            for mutator in [lambda c:c['spec'].update(step=544),lambda c:c.update(afterok=None),lambda c:c.update(phase_b=True),lambda c:c.update(plan_sha256='x'),lambda c:c['spec']['artifact'].update(sha256='a'*64)]:
[BEYOND] +                bad=copy.deepcopy(b);mutator(bad)
[BEYOND] +                with self.assertRaises(ValueError):L.validate_request(bad)
[BEYOND] +            with self.assertRaises(ValueError):L.validate_batch((p/'proof/BATCH.sh').read_text()+'x',a)
[BEYOND] +        self.assertEqual(L.SSH[:3],['timeout','300','bash'])
[BEYOND] +
[BEYOND] +    def test_request_guards_and_mismatched_proof(self):
[BEYOND] +        for token in ('p1234567890','revsi','../1234567890'):
[BEYOND] +            with self.assertRaises(ValueError):L.valid_token(token)
[BEYOND] +        for step in (100,544,True):
[BEYOND] +            with self.assertRaises(ValueError):L.prepare('a1234567890',directory()/'x',step=step)
[BEYOND] +        with self.assertRaises(ValueError):L.submit_argv(None,'a1234567890')
[BEYOND] +        with self.assertRaises(ValueError):L.prepare('a1234567890',directory()/'x',media_root='/bad')
[BEYOND] +        with self.assertRaises(ValueError):L.prepare('a1234567890',directory()/'x',pool='/tmp/revsi')
[BEYOND] +        with self.assertRaises(ValueError):L.prepare('a1234567890',directory()/'x',media_root='/project/community/jjyeung/okh7/313db5a47f11ff0c')
[BEYOND] +        p=directory();a=L.prepare('a1234567890',p/'a',mode='proof',media_root='/project/community/jjyeung/okh7/313db5a47f11ff0c')
[BEYOND] +        (p/'a/SUBMIT.out').write_text('123\n');L.submission_record(p/'a')
[BEYOND] +        with self.assertRaises(ValueError):L.prepare('a1234567890',p/'b',proof_destination=p/'a',media_root=a['media_root'])
[BEYOND] +        with self.assertRaises(ValueError):L.prepare('b1234567890',p/'b',step=200,proof_destination=p/'a',media_root=a['media_root'])
[BEYOND] +        with patch.object(L,'canonical',return_value='bad'):
[BEYOND] +            with self.assertRaises(ValueError):L.validate_request(a)
[BEYOND] +
[BEYOND] +    def test_receipt_exact_and_bad_inputs(self):
[BEYOND] +        sample=Path('/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/c6/m1.done').read_bytes()
[BEYOND] +        self.assertEqual(E.parse_done(sample,'359fcc3c',1)['bytes'],21583032320)
[BEYOND] +        for step in (200,400,600,800,1000):
[BEYOND] +            raw=f'q8/8865619b/359fcc3c_m{step}.tar 123 '.encode()+b'a'*64+b'\n'
[BEYOND] +            self.assertEqual(E.parse_done(raw,'359fcc3c',step)['bytes'],123)
[BEYOND] +            for bad in [raw+b'\n',raw.replace(b' 123 ',b' 0 '),raw.replace(b'359fcc3c',b'469ddece'),raw.replace(b'q8/8865619b',b'q8/00000000'),raw.replace(b'.tar ',b'.tar.part00-of-04 '),b'gs://cmu-gpucloud-jjyeung/'+raw,raw[:-3],raw.upper(),raw.replace(b' 123 ',b'\t123 ')]:
[BEYOND] +                with self.assertRaises(ValueError):E.parse_done(bad,'359fcc3c',step)
[BEYOND] +        for run,step in [('x',400),('359fcc3c',True),('359fcc3c',0)]:
[BEYOND] +            with self.assertRaises(ValueError):E.parse_done(b'',run,step)
[BEYOND] +
[BEYOND] +    def test_hex_logs_are_reversible(self):
[BEYOND] +        out=io.BytesIO();body=b'revsi vsi split distill D0 qgen\n'
[BEYOND] +        opaque_io.encode(io.BytesIO(body),out)
[BEYOND] +        self.assertEqual(bytes.fromhex(out.getvalue().decode()),body)
[BEYOND] +        self.assertNotIn(b'revsi',out.getvalue())
[BEYOND] +
[BEYOND] +    def test_bootstrap_in_process_and_no_live_entry(self):
[BEYOND] +        import base64,re,os
[BEYOND] +        import orchard_job as J
[BEYOND] +        p=directory();cfg=L.prepare('a'+uuid.uuid4().hex[:12],p/'prepared',mode='proof',media_root='/project/community/jjyeung/okh7/313db5a47f11ff0c')
[BEYOND] +        script=(p/'prepared/BATCH.sh').read_text()
[BEYOND] +        raw=base64.b64decode(re.search(r"raw=base64.b64decode\('([^']+)'",script)[1])
[BEYOND] +        script=L.render_batch(raw,cfg['token'],str(p))
[BEYOND] +        body=script.split("<<'A_BATCH_BOOTSTRAP'\n",1)[1].rsplit('\nA_BATCH_BOOTSTRAP',1)[0]
[BEYOND] +        cwd=Path.cwd()
[BEYOND] +        with patch.dict(os.environ,SLURM_JOB_ID='123'),patch.object(os,'execv') as execute:
[BEYOND] +            try:exec(compile(body,'<bootstrap>','exec'),{'__name__':'fixture'})
[BEYOND] +            finally:os.chdir(cwd)
[BEYOND] +        execute.assert_called_once()
[BEYOND] +        local=p/('a_123_'+cfg['token'])
[BEYOND] +        self.assertEqual(json.loads((local/'bootstrap/CONFIG.json').read_text()),cfg)
[BEYOND] +        self.assertTrue((local/'bootstrap/export_stage.py').is_file())
[BEYOND] +
[BEYOND] +    def test_checker_argv_uses_full_packaged_checker_without_video_mounts(self):
[BEYOND] +        import orchard_job as J
[BEYOND] +        import orchard_stage as S
[BEYOND] +        p=directory();(p/'bootstrap').mkdir();receipt=p/'receipt';receipt.mkdir()
[BEYOND] +        cfg=dict(spec=dict(package='/scratch/jjyeung/a123/p',interpreters=dict(p1cpu='/python'),models=dict(base=dict(path='/base'))))
[BEYOND] +        (p/'bootstrap/CONFIG.json').write_text(json.dumps(cfg))
[BEYOND] +        def run(argv,**kw):
[BEYOND] +            self.assertNotIn('--header-only',argv);self.assertIn('/scratch/jjyeung/a123/p/reader/out/export_check.py',argv)
[BEYOND] +            (receipt/'CHECK.json').write_text(json.dumps(dict(status='VERIFIED',step=400)))
[BEYOND] +            return type('Result',(),dict(stdout=b'private',stderr=b'',returncode=0))()
[BEYOND] +        with patch.object(S,'sha',side_effect=lambda path:E.CHECKER_PINS[Path(path).name]),patch.object(J,'namespace',return_value=[]) as ns,patch.object(J,'environment',return_value={}),patch.object(E.subprocess,'run',side_effect=run):
[BEYOND] +            self.assertEqual(E.run_export_checker(p,'/artifact','a'*64,400,True,receipt,'unused')['status'],'VERIFIED')
[BEYOND] +            ns.assert_called_once_with(p)
[BEYOND] +        with self.assertRaises(ValueError):E.run_export_checker(p,'/artifact','a'*64,400,False,receipt,'unused')
```

### tests/test_unpack.py — BEYOND (new local file)

```diff
[BEYOND] +import offline_guard
[BEYOND] +import copy
[BEYOND] +import io
[BEYOND] +import json
[BEYOND] +from pathlib import Path
[BEYOND] +import sys
[BEYOND] +import tarfile
[BEYOND] +import unittest
[BEYOND] +from unittest.mock import patch
[BEYOND] +import uuid
[BEYOND] +ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
[BEYOND] +import unpack_result as U
[BEYOND] +
[BEYOND] +
[BEYOND] +class UnpackTests(unittest.TestCase):
[BEYOND] +    def test_authenticated_extraction_and_identity_refusal(self):
[BEYOND] +        p=ROOT/'evidence'/('unpack_'+uuid.uuid4().hex);(p/'fetched').mkdir(parents=True)
[BEYOND] +        cfg=dict(token='a1234567890',plan_sha256='a'*64);submission=dict(job=123)
[BEYOND] +        for name,value in [('CONFIG.json',cfg),('SUBMISSION.json',submission)]:
[BEYOND] +            (p/name).write_text(json.dumps(value))
[BEYOND] +        archive=p/'fetched/result.tar.gz'
[BEYOND] +        marker=json.dumps(dict(plan_sha256=cfg['plan_sha256'],synthetic=False)).encode()
[BEYOND] +        with tarfile.open(archive,'w:gz') as t:
[BEYOND] +            item=tarfile.TarInfo('COMPLETE.json');item.size=len(marker);t.addfile(item,io.BytesIO(marker))
[BEYOND] +        receipt=dict(token=cfg['token'],job=123,plan_sha256=cfg['plan_sha256'],schema='evalx-orchard-result-return-v1',
[BEYOND] +                     synthetic=False,status='COMPLETE',complete=True,conflicting_terminal_markers=False,returncode=0,
[BEYOND] +                     archive=dict(bytes=archive.stat().st_size,sha256=U.R.sha(archive)))
[BEYOND] +        (p/'fetched/EXIT.json').write_text(json.dumps(receipt))
[BEYOND] +        U.extract(p,p/'packet');self.assertEqual((p/'packet/COMPLETE.json').read_bytes(),marker)
[BEYOND] +        with self.assertRaises(FileExistsError):U.extract(p,p/'packet')
[BEYOND] +        for field,value in [('token','wrong'),('job',456)]:
[BEYOND] +            bad=dict(receipt,**{field:value});(p/'fetched/EXIT.json').write_text(json.dumps(bad))
[BEYOND] +            with self.assertRaises(ValueError):U.extract(p,p/'bad')
[BEYOND] +        bad=copy.deepcopy(receipt);bad['archive']['sha256']='0'*64;(p/'fetched/EXIT.json').write_text(json.dumps(bad))
[BEYOND] +        with self.assertRaises(ValueError):U.extract(p,p/'bad')
[BEYOND] +        self.assertFalse((p/'bad').exists())
```

### unpack_result.py — BEYOND (new local file)

```diff
[BEYOND] +"""Extract an authenticated, completed result into a fresh local directory."""
[BEYOND] +import argparse
[BEYOND] +import json
[BEYOND] +from pathlib import Path
[BEYOND] +import sys
[BEYOND] +import tarfile
[BEYOND] +ROOT=Path(__file__).resolve().parent
[BEYOND] +sys.path.insert(0,str(ROOT/'kit/launcher'))
[BEYOND] +import orchard_results as R
[BEYOND] +
[BEYOND] +
[BEYOND] +def extract(destination,output):
[BEYOND] +    destination=Path(destination);output=Path(output)
[BEYOND] +    cfg=json.loads((destination/'CONFIG.json').read_text())
[BEYOND] +    receipt=json.loads((destination/'fetched/EXIT.json').read_text())
[BEYOND] +    submission=json.loads((destination/'SUBMISSION.json').read_text())
[BEYOND] +    if receipt.get('token')!=cfg['token'] or receipt.get('job')!=submission['job']:
[BEYOND] +        raise ValueError('Returned identity differs')
[BEYOND] +    archive=destination/'fetched/result.tar.gz'
[BEYOND] +    R.verify(receipt,archive,cfg['plan_sha256'])
[BEYOND] +    output.mkdir(parents=True,exist_ok=False)
[BEYOND] +    with tarfile.open(archive) as stream:stream.extractall(output,filter='data')
[BEYOND] +
[BEYOND] +
[BEYOND] +if __name__=='__main__':
[BEYOND] +    p=argparse.ArgumentParser();p.add_argument('--destination',required=True);p.add_argument('--output',required=True)
[BEYOND] +    a=p.parse_args();extract(a.destination,a.output)
```

