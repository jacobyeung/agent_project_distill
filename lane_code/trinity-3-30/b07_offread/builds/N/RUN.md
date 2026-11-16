This build supports ReVSI CPU fixtures, question-only inventories, binding checks, local return verification, and reports. It is not ready to submit a native official read. `submit-command` and `record-submission` deliberately refuse because no production bootstrap has passed rehearsal. Nothing was submitted or uploaded.

Run the fixtures on `trinity-3-30` from this directory. Use a new destination for every run; the worker refuses to overwrite a journal.

```bash
cd /scratch/jjyeung/orch_n30/b07_offread/builds/N
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=/scratch/jjyeung/envs/p1cpu/bin/python
"$PY" -B -m offnative.rehearse work/revsi_harness_new harness
"$PY" -B -m offnative.rehearse work/revsi_e2e_new e2e
"$PY" -B -m pytest -p no:cacheprovider kit/tests --basetemp=work/pytest_new -q
```

The fixture runs use two generated videos, two synthetic items per ReVSI subtype, a tiny random Qwen3 model, forced sampled tokens, synthetic tower arrays, and b04's actual audited generation function. Reports identify the export as a fixture. These reports are not benchmark results.

Prepare a binding after the owner supplies the frozen reader record. This writes an admission record with the unresolved production blockers; it does not create a runnable batch.

```bash
"$PY" -B native_read.py prepare --benchmark revsi999t32 --export step544 \
  --reader "harness:$FREEZE_SHA256" --freeze-file "$FREEZE_FILE" \
  --frames 32 --frame-layout duplicate --mode production \
  --destination work/prepared_read
```

For an end-to-end binding, use `--reader e2e:<manifest-sha256> --e2e-manifest <path> --eat1-report <path>`. Production binding requires EAT-1 PASS. For D0, use `--export done:<path> --init-selection <path> --export-layout <path>`. The layout record must contain `export_sha256` and `frames: {count, layout}`. The existing three-field `.done` format contains no layout, so the separately pinned record is required unless an explicit override reason is supplied. The shared frame guard refuses 64 spread on step 544 without `--override-reason`. A successful frame binding alone does not validate the 64-frame production backend.

`BINDING.json` and `COHORT.json` stay on Trinity. The proposed pool is `/project/community/jjyeung/okh7/4f6a2c8d19e073b5/`. Proposed returns use `gs://cmu-gpucloud-jjyeung/q8/4f6a2c8d19e073b5/<opaque-token>/`. Job names use `a15_cot_ap` followed by 16 hexadecimal characters. Token meanings are recorded in `work/ORCHARD_LEDGER.jsonl`. The prepared CONFIG contains opaque identities and frame parameters; no input packet is authorized by this build.

The completed bootstrap must reuse build R's reviewed runtime/base/export staging and D0 `export_stage` admission. It must stage `root/bwrap`, reject input hard links, and put resources on the command line: `--gres=gpu:1 --cpus-per-task=16 --mem=200G --output=/dev/null`. It must keep the inherited 600-second return reserve and enforce the outer subprocess deadline as well as the item-start cutoff. This build tests the item-start rule but has no validated outer watchdog.

Every new input above 20 MB needs an opaque archive and a governed transfer receipt. This includes export archives, runtime environments, G3T weights, SAM 3 weights, the b04 artifact, media archives, and any proof mask cache. Use the existing serial IO governor; `offnative.cli.governed_transfer` delegates to build R's stopped-source registration and rate-limiter implementation. Do not transfer folders. Coordinate the governor before moving data, use an 8 MB/s ceiling for reads or internet transfers and 4 MB/s for writes to shared storage, and count all concurrent traffic against the user's 18 MB/s limit. Never retry a killed or dropped transfer automatically. The remote transfer path has not run in this build.

A future operator must poll at most once per minute and use the two return channels independently. The local `fetch` path accepts only a completed archive with an independently supplied SHA256 and a 90 MB size limit; it validates every member before extraction. The remote fetch and receipt-to-submission authentication still require the production launcher integration. Do not treat the local import command as proof of an Orchard job's identity.

```bash
"$PY" -B native_read.py fetch --destination work/prepared_read \
  --return-archive "$RETURN_ARCHIVE" --return-sha256 "$RETURN_SHA256"
"$PY" -B native_read.py report --destination work/prepared_read
```

A report requires the complete bound ID list and the binding hash. Each harness arm has all 999 items. The room-unserved arm retains primary records for other types; the fallback arm uses the unserved answer only for refused or non-answered routed records. The scorer receives the model's raw answer bytes. No unit conversion or scripted answer path is enabled.

The first batch of the real export cannot run on this node under the build restrictions. The required in-job proof and canary are control-flow gates, but they have not executed with the real export. Read `out/OPEN_INPUTS.md` before assigning the remaining work. VSI-Bench is not done.
