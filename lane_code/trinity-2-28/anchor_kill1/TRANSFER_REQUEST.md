# K1 transfer request (not executed)

Source: trinity-1-18. Destination: trinity-2-28, W/k1_inputs.
The supplied K1_TRANSFER_FILES.txt is a 684-line relative-path manifest generated
from the local SEEDS.json input_sha256 provenance. K1_MISSING_INPUTS.json carries
every absolute source path and recorded hash. It requests 209 candidate-pool
JSON files, 209 raster NPZ files, and 266 sb_kbox4 code/table/row-set files.
Only 204 captures and the specified 1,012 rows may contribute decision scores.

The source paths include:
- /scratch/jjyeung/k1/run_convert_2/01949c4249271126/candidates.json (plus 208 named pools).
- /scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/41048124.npz (plus the other 208 named raster files).
- /scratch/jjyeung/orch_n30/sb_kbox4/out/box_ladder/serving_tables/arkitscenes__41048124.json.gz (209 named serving tables).
- /scratch/jjyeung/orch_n30/sb_kbox4/out/box_ladder/PER_ITEM.jsonl.
- /scratch/jjyeung/orch_n30/sb_kbox4/{train_manifest.json,train_labels.json,train_pricing.py,predicted.py,serving_reference.py} and the other named code inputs.

Remote file sizes are UNKNOWN: the available provenance records hashes but no
byte sizes, the source trees are absent here, and SSH is forbidden. No aggregate
size is invented. The transfer owner must stat the exact named files, record each
byte size, check that the transfer plus current W stays below 20 GB, and confirm
100–200 GB free on destination scratch before transferring. No directory scan is
needed. No automatic transfer is authorized by a timeout.

Once the owner has placed K1_TRANSFER_FILES.txt at /tmp/anchor_kill1.files on
trinity-1-18 and completed those checks, run this one InfiniBand tar pipe there:

```bash
tar -cf - -C /scratch/jjyeung --verbatim-files-from -T /tmp/anchor_kill1.files | ssh -o ConnectTimeout=20 trinity-2-28.ib 'mkdir -p /scratch/jjyeung/orch_n30/anchor_kill1/k1_inputs && tar -xf - -C /scratch/jjyeung/orch_n30/anchor_kill1/k1_inputs'
```

Verify each received file against the supplied hashes. The source list supplies
the minimum pool/raster/table evidence; the served distance replay may need more
geometry dependencies after the sb_kbox4 code is inspected. The A3x raw-input
adapter is not implemented against files that are unavailable.
