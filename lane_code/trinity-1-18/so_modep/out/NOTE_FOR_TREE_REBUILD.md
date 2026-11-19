Apply these patches after N's first proof, in a fresh rebuild of build 21 (`b262e7a7`). Keep both switches OFF for the initial rebuilt proof. The two patches apply independently; their file lists do not overlap. The manifest binds each patch and each changed file.

```bash
cd <fresh-build-21-native-tree>
patch --batch --fuzz=0 --no-backup-if-mismatch -p1 < /scratch/jjyeung/orch_n30/so_modep/out/patches/01_fast_paths.diff
patch --batch --fuzz=0 --no-backup-if-mismatch -p1 < /scratch/jjyeung/orch_n30/so_modep/out/patches/02_selected_sql.diff
```

Rebuild the source archive, tree/configuration seals, executable inventory, scan certificate and launch kit through N's normal process. Run its normal proof and review gates. Changing authenticated source necessarily changes its source seal; never reuse the old seal. No configuration field, receipt schema, frame identity, RNG draw, selection rule or authentication check is removed by these patches.

`S1_PREP_FAST_PATHS=1` enables patch 01. Every other value, including unset, keeps the original path operations. The switch replaces lexical path ancestry walks and repeated JSON mapping parsing with equivalent component comparisons and a bounded text-parsing cache. It caches no resolved path, file status or SHA. Every original resolution, containment check and file check still runs. The source map remains dynamic, including `Q_E1`/`Q_E4` aliases.

`S1_PREP_SELECT_SQL=1` enables patch 02. Every other value keeps the original scans. For a selected-index set with density below one quarter of its zero-based prefix, SQLite reads selected payloads in ascending index order using at most 256 bindings per query. Dense selections keep the original scan. All source pin hashes, expected-population checks, retained-row checks, missing-index checks and final original-index ordering remain. No write pragma or output database layout changes.

Enable patch 01 alone on the first timed launch of the rebuilt kit. The wrapper does not unset either switch (`launch_s1/b/r.sh:6-8,56`), and `tk_env` does not overwrite them. Record their values and the actual worker Python version in the operator's launch record. Leave production OMP/MKL/OpenBLAS settings, Torch thread settings, input paths and all admission controls unchanged.

Use the existing phase journals for timing. `resources.seconds` measures the prepare action and the frame-audit action. The full mode-p launch/exit timestamps measure total elapsed time. Their difference includes revalidation, hashing and publication outside those actions. Copy only the small receipts/logs through the lane's existing approved channel; this patch adds no transfer. The delivered read-only helper prints these fields, retained source denominators and receipt mtimes:

```bash
nice -n 10 <native-python> -I -s -B /path/to/measure_modep.py <native-admission-directory> \
  --launch-utc <launch-p-UTC> --exit-utc <exit-rc0-UTC>
```

The helper is delivered at `/scratch/jjyeung/orch_n30/so_modep/work/measure_modep.py`. Keep its stdout outside the authenticated native output tree. Receipt mtimes can estimate pointing/VQA/routing boundaries, but they are not isolated CPU timers. Compare frame time per retained frame reference, prepare time with matched row counts, and total mode-p time against an OFF launch with the same inputs, node storage class and Python build. A single ON launch cannot establish causal savings; do not rerun production preparation merely to fill a timing table without the lane's authorization.

For patch 02, first inspect the retained index files already named by the prepared receipt. Its benefit applies to sparse selections; dense selections deliberately retain the native scan. Enable it alone on a comparable subsequent launch, then compare native preparation, the post-prepare residual, frame time and row denominators. Do not add the two estimated savings: both touch work inside the same phase envelopes. Leave patch 02 OFF if the selected sets are dense or the timed launch does not improve.

Watch the existing refusal messages, phase completion markers, source counts, scene exclusion reports, frame reference/unique counts and fixed samples. Any missing or changed input must still refuse. Check the real worker Python version: the measured path improvement comes from Python 3.12, and a runtime with different pathlib internals may save less. If either switch regresses latency or produces a mismatch, return that switch to OFF and retain the failed artifacts for review. Never adopt a partial phase or relaunch a cluster-killed job automatically.

CPU fixture parity compares every mode-p file at identical paths and UUIDs, with only native elapsed-time and peak-RSS telemetry fixed by the test harness. These fixture controls are not production changes. The focused CPU suites run with CUDA hidden, eight-thread limits and affinity to eight CPUs. `work/run_gloo.sh` runs the delivered two-rank frame parity test and native checkpoint-buffer tests on a lane where sockets work; it has not run in this sandbox. Production throughput and GPU training remain unmeasured.
