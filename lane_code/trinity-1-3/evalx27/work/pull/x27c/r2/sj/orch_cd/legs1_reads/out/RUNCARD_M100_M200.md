Direct dev-S1 reads are prepared for a LEG-S1 full export. Full boundary clearance is not prepared: f17 dev-S1 and dev-858 comparisons are missing, routed controls are unqualified, and the native scripted API covers only 600 of 1,525 items. The current training prelaunch card says HOLD. This run card does not authorize training or allocate a GPU.

Run the following on the operator's assigned compute host. This CPU lane executed only binds, merges, reports and tests. `PY` is the CPU interpreter; `CARD_PY` must name the operator's reviewed GPU environment, with vLLM 0.32.0 for direct reads and the frozen trainer dependencies for native reads. Retain every failed output and choose a fresh destination for a corrected request. Never overwrite a request after launch. Do not automatically restart a killed job.

Before either milestone, stage the package, reviewed kits, base snapshot, tokenizer, exact PNGs and native runtime dependencies on local disk. Preserve the absolute paths in already-bound receipts. Bind afresh after relocating code. The dry-cell catalog is `CELLS.json`; its requests are metadata templates, not launchable requests.

```bash
L=/scratch/jjyeung/orch_cd/legs1_reads
PY=/scratch/jjyeung/envs/p1cpu/bin/python
KIT=/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_vl64rt
F17KIT=/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_eval_gaps
export OMP_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
# Set these to the assigned host's actual local inputs, never shared NFS.
: "${RUNROOT:?}" "${FRAMES:?}" "${BASE:?}" "${MODELS:?}"
: "${TOKENIZER:?}" "${TOKENIZER_MANIFEST:?}" "${CARD_PY:?}" "${CARD:?}"
export HF_HOME="$RUNROOT/hf" XDG_CACHE_HOME="$RUNROOT/cache"
```

`MODELS` has the structure of `work/vendor/r3/MODELS.reference.json`, with locally resolvable base/manifest and f17 paths. `direct.py` replaces only its CP1 export entry and retains the CP1 protocol slot. Use the parent merge at `work/parent_main_merge` as the baseline; it pins the real parent journals. This lane's source-path references must remain readable when reporting elsewhere.

Before m100, obtain f17's three development reads. Its reviewed protocol is its trained 32-frame spread layout, greedy, thinking ON16k; do not replace it with duplicate frames or B2048. Bind/launch main with the r3 adapter and the controls with r4, then merge with r5:

```bash
"$PY" -I -s "$L/work/vendor/r3/adapter.py" bind --cell f17 \
  --kit "$F17KIT" --models "$MODELS" --frames-root "$FRAMES" --dest "$RUNROOT/f17_main"
"$PY" -I -s "$L/work/vendor/r4/adapter.py" bind --cell f17 \
  --payload "$L/work/vendor/r4/DEV_BACKDIR" --kit "$F17KIT" --models "$MODELS" \
  --frames-root "$FRAMES" --dest "$RUNROOT/f17_away"
"$PY" -I -s "$L/work/vendor/r4/adapter.py" bind --cell f17 \
  --payload "$L/work/vendor/r4/DEV_FORWARD_TWINS" --kit "$F17KIT" --models "$MODELS" \
  --frames-root "$FRAMES" --dest "$RUNROOT/f17_forward"
for FAMILY in main away forward; do
  CUDA_VISIBLE_DEVICES="$CARD" "$CARD_PY" -I -s "$L/work/vendor/r5/adapter.py" launch \
    --dest "$RUNROOT/f17_$FAMILY" --attempt "f17_${FAMILY}_a1"
  CUDA_VISIBLE_DEVICES='' "$PY" -I -s "$L/work/vendor/r5/adapter.py" merge \
    --source "$RUNROOT/f17_$FAMILY" --dest "$RUNROOT/f17_${FAMILY}_merge" \
    --kit "$F17KIT" --attempt "f17_${FAMILY}_a1"
done
```

At m100 set `STEP=100`; at m200 use `STEP=200` and fresh directories. Obtain the export URL, archive SHA256, artifact SHA256 and published path from the training producer. These values do not exist yet. The pull command below is an operator template and was not run in this lane. Keep archive transfers serialized and within the operator's cluster allowance. For transfers over 30 GB through Trinity's shared paths, the cluster's planning rule still applies.

```bash
STEP=100
RUN="$RUNROOT/m$STEP"
mkdir -p "$RUN"
: "${EXPORT_URL:?}" "${ARCHIVE_SHA:?}" "${ARTIFACT_SHA:?}" "${PUBLISHED_ROOT:?}" "${ARTIFACT:?}"
curl --fail --location --limit-rate 8M "$EXPORT_URL" --output "$RUN/export.tar"
"$PY" -I -s "$L/out/receive.py" --archive "$RUN/export.tar" \
  --sha256 "$ARCHIVE_SHA" --dest "$PUBLISHED_ROOT"
"$PY" -I -s "$L/out/export_check.py" --export "$ARTIFACT" --sha256 "$ARTIFACT_SHA" \
  --step "$STEP" --base "$BASE" --output "$RUN/EXPORT_CHECK.json"
```

The archive must unpack beneath `PUBLISHED_ROOT` to the paths embedded in `artifact.json`. The receiver rejects links, traversal, duplicate members and existing destinations. It does not rewrite paths. If the producer ships a different archive layout, expose it at the published paths before verification. Never infer the artifact hash from a directory name.

Run the direct cells on one assigned card, sequentially. The main cell is first because it decides m100 reversal. The launch stages the export using the reviewed stager, generates ON16k and derives both B2048 and B4096. The decision report selects B2048. Do not change max generation tokens to 2,048.

```bash
for FAMILY in main away forward; do
  "$PY" -I -s "$L/out/direct.py" bind --family "$FAMILY" --step "$STEP" \
    --export "$ARTIFACT" --sha256 "$ARTIFACT_SHA" --models "$MODELS" --kit "$KIT" \
    --frames-root "$FRAMES" --dest "$RUN/$FAMILY"
  CUDA_VISIBLE_DEVICES="$CARD" "$CARD_PY" -I -s "$L/out/direct.py" launch \
    --dest "$RUN/$FAMILY" --attempt "legs1_m${STEP}_${FAMILY}_a1"
  CUDA_VISIBLE_DEVICES='' "$PY" -I -s "$L/out/direct.py" merge \
    --source "$RUN/$FAMILY" --dest "$RUN/${FAMILY}_merge" --kit "$KIT" \
    --attempt "legs1_m${STEP}_${FAMILY}_a1" \
    --tokenizer-dir "$TOKENIZER" --tokenizer-manifest "$TOKENIZER_MANIFEST"
done
"$PY" -I -s "$L/out/decision.py" --step "$STEP" \
  --leg "$RUN/main_merge" --parent "$L/work/parent_main_merge" \
  --f17 "$RUNROOT/f17_main_merge" --away "$RUN/away_merge" --forward "$RUN/forward_merge" \
  --output "$RUN/DECISION_DIRECT.json"
```

Use `set -euo pipefail` in an operator wrapper so a failed launch cannot fall through into a merge. Each cell stages its own model by default. The operator may share one staged-model directory across the three cells of one artifact using the reviewed staging receipts; never reuse the CP1 staging directory or m100 weights as m200.

Conditional native preparation, after source/control qualification and receipt admission:

```bash
# Skip tower generation only when an existing raw cache passes all native pins.
CUDA_VISIBLE_DEVICES="$CARD" "$CARD_PY" -I -s "$L/out/geometry.py" tower \
  --dense-manifest "$DENSE_FRAMES" --weights "$G3T_WEIGHTS" --config "$G3T_CONFIG" \
  --device cuda:0 --dest "$RUNROOT/raw_g3t"
CUDA_VISIBLE_DEVICES="$CARD" "$CARD_PY" -I -s "$L/out/geometry.py" prepare \
  --raw-tower "$RUNROOT/raw_g3t/RAW_G3T.json" --config "$TRAIN_CONFIG" \
  --export "$ARTIFACT" --sha256 "$ARTIFACT_SHA" --step "$STEP" \
  --frames-root "$FRAMES" --device cuda:0 --dest "$RUN/geometry"
GEOMETRY="$RUN/geometry/GEOMETRY_MANIFEST.json"
for ARM in forced_route scripted forced_direct unflagged; do
  "$PY" -I -s "$L/out/routed.py" bind --step "$STEP" --arm "$ARM" --scope supported600 \
    --export "$ARTIFACT" --sha256 "$ARTIFACT_SHA" --config "$TRAIN_CONFIG" \
    --geometry "$GEOMETRY" --frames-root "$FRAMES" --dest "$RUN/$ARM"
  CUDA_VISIBLE_DEVICES="$CARD" "$CARD_PY" -I -s "$L/out/routed.py" run \
    --dest "$RUN/$ARM" --device cuda:0
done
"$PY" -I -s "$L/out/routed.py" merge --forced-route "$RUN/forced_route" \
  --scripted "$RUN/scripted" --forced-direct "$RUN/forced_direct" --unflagged "$RUN/unflagged" \
  --output "$RUN/ROUTED.json"
```

For a first-item rehearsal, bind to a separate `probe` destination and add `--first-minute` to `routed.py run`. That output cannot merge as a completed cell. The commands above are development diagnostics until trained flags match; full-table R1 still needs the missing scripted APIs. The current report will not certify them. Free-generation `--scope main1525` cells are available, but there is deliberately no scripted-main command.

The complete report command accepts additional admitted comparisons:

```bash
"$PY" -I -s "$L/out/decision.py" --step "$STEP" \
  --leg "$RUN/main_merge" --parent "$L/work/parent_main_merge" \
  --f17 "$RUNROOT/f17_main_merge" --away "$RUN/away_merge" --forward "$RUN/forward_merge" \
  --dev858 "$DEV858_PIN" --routed "$RUN/ROUTED.json.pin.json" \
  --output "$RUN/DECISION.json"
# At m200 add: --history "$M100_HISTORY" --official "$OFFICIAL_PIN"
```

`M100_HISTORY` is a retained JSON object with `rows_raised_at_m100`, a list of actual question types changed at that boundary. Do not infer changes from R1 failures. `DEV858_PIN` and `OFFICIAL_PIN` each pin an externally merged `legs1-auxiliary-comparison-v1` object: `items` (858 or 5130), `leg_artifact_sha256`, `f17_artifact_sha256`, `synthetic:false`, `parity_pass:true`, `sources:{leg:[pins],f17:[pins]}`, and paired normalized `leg`/`f17` rows. Each row requires `key`, physical `room`, `question_type`, `stratum`, `scores:{released_answer,answer}` and `capped`; official term checks also need `dataset`. `auxiliary.py` verifies these pins and identities; it does not generate or rescore these external journals. A source scorer must establish their normalized scores. This package has no completed dev-858/official generation-to-bundle adapter, so global R3 and the official ledger remain open. Never replace dev-858 with the older 741-item subset.

| Cell | Parent timing basis | Planning time on a comparable card |
|---|---|---:|
| Main, 1,525 | 06:59:03–07:41:46, including generation and budget arms | 42m43s; 0.712 GPU-h |
| Forward, 150 | 10:29:40–10:34:32 | 4m52s; 0.081 GPU-h |
| Away, 150 | Forward-size proxy, not a measured away duration | about 5m; 0.081 GPU-h |
| All three direct | Sum of measured main/forward and away proxy | about 53m; 0.875 GPU-h |
| Each 600-item native arm | No comparable native measurement | Unknown; time the first item and then a small sample |
| Each 1,525-item native arm | No comparable native measurement | Unknown |
| G3T/own-head geometry | No measurement for this export/driver | Unknown |
| f17 / dev-858 / official | Different protocol/runtime | No measured estimate from this lane |

At the parent's main rate, 858 direct items would take roughly 24 minutes and 5,130 roughly 144 minutes before extra staging; these are arithmetic proxies, not measured job estimates. Native autoregressive tool execution must not inherit vLLM throughput. The plan's 25–35 GPU-hour combined read budget is also an estimate.

| Verdict | Operator action |
|---|---|
| m100 reversal: any direct type or route CI wholly below zero vs f17 | Stop at m100 and reopen the lineage. |
| R1 fails | Give the failed form more rows at the next boundary; retain the exact changed-type history. |
| R1b fails | Revisit path-choice training; do not silently change the frozen table. |
| R2 CI above zero / below zero / spans zero | Keep routing / move that type to direct next boundary / retain table and log the cell. |
| R3 fails | Raise direct share or shorten thinking at the next boundary. |
| m200 R1 still fails after rows raised at m100 | Stop at m200. |
| Official macro CI wholly below −2.5 or above +2.4 pp | Reject the ledger; do not select policy on official items. |
| Missing, unqualified, failed-parity or incomplete comparison | No clearance from that check. Complete its missing evidence before making the boundary decision. |

The report uses the empirical B2048 parent route score, 33.3333%, and also discloses the card's ON16k reference, 29.3333%. Do not compare a LEG B2048 route result with the parent's ON16k reference. Facing-away controls remain diagnostics; no new stopping threshold is attached to them. Every policy/config change needs a fresh binding and the training owner's normal admission.
