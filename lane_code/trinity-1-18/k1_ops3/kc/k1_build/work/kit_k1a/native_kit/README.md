# Training response cache kit

`build_manifest.py` binds a pinned admitted candidate-ID list to source pool rows and a dense frame registry. It refuses missing RGB/GT identity joins, noncanonical units and incomplete exclusions. `run.py plan` checks the manifest. `launch.sh` runs one assigned GPU through `watchdog.py`; it performs no staging, scheduling or downloads.

The CPU producer uses the native step-544 geometry converter, frozen dense-alias SAM postprocessing, the native candidate policy, and the native response dispatcher. The filter uses the printed value and independent GT masks. Every output remains `training_admitted=false`; fallback targets require a supplied, evidence-checked qualitative trace. Response spans are rendered by the trainer's real `ground_rows.render_ground` function and can be masked from loss.

The kit has external read-only dependencies on the frozen native reader and training source tree. Set `O3_NATIVE_ROOT` and `LEGS1_TREE` after staging the same pinned code. The bundled `vendor_sam` contains inference source only. No weights or data are included.

Run CPU proof:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/kit/test_kit.py
```

See `out/CACHE_KIT_REPORT.md` for the launch packet, input contracts, resource estimates and untested GPU paths. The runtime encoder's full admission schema does not yet admit real-failure fallback rows; these event records are a cache/builder interface, not a drop-in sealed training stream.
