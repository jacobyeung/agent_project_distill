# Staging inventory

Exact byte counts from local stat; missing inputs have no invented size. Preserve absolute paths on the GPU node.

| Group | Files present / required | Bytes present |
|---|---:|---:|
| Training RGB | 6560 / 6560 | 1,647,025,131 |
| Training rasters | 205 / 205 | 28,683,454 |
| Tuning frames32 RGB | 992 / 992 | 60,344,804 |
| Tuning GT | 31 / 31 | 235,514,771 |
| Linked candidates | 31 / 31 | 13,752,196 |
| SAM candidate caches | 31 / 31 | 63,659,872 |
| T0 required shards | 2 / 2 | 5,997,380,256 |
| T0 metadata | 1 / 1 | 67,691 |
| T0 config and tokenizer | 8 / 8 | 22,984,268 |
| vc_vit | 1 / 1 | 2,763,214,343 |
| sam3_pe | 2 / 2 | 3,450,063,364 |
| g3t | 0 / 1 | 0 |
| cradio_v4_so400m | 0 / 1 | 0 |
| dinov3_vitl16 | 0 / 1 | 0 |
| dinov2_vitl14_reg | 0 / 1 | 0 |
| Runtime helper source | 4 / 4 | 41,334 |
| Label metadata | 3 / 3 | 4,084,677 |
| O5 pending | 0 / 1 | 0 |
| Lane code and manifests | 52 / 52 | 40,476,933 |
| G3T source | 26 / 26 | 137,108 |
| SAM source | 193 / 193 | 4,739,916 |
| Environment sam3_capretry_native_v1 | 24462 / 24462 | 7,778,998,643 |
| Environment p1cpu | 22095 / 22095 | 1,265,633,075 |
| Environment fla site | 436 / 436 | 4,578,775 |

G3T weights: `/dev/shm/jjyeung_mdg_next/g3t` on trinity-2-18 → `/dev/shm/jjyeung_evalx/g3t` on trinity-1-18. Review2 reports approximately 5.5 GB; visibility in this private RAM-disk namespace does not establish host-wide absence. `WEIGHTS.gpu.json` uses the target path.

Every path and byte count is in `STAGING_INVENTORY.json`. Missing source and weights must be recorded in each arm’s `SKIPPED.json`.

| T0 shard | Exact bytes |
|---|---:|
| `/scratch/jjyeung/orch_cd/mdg_build/work/data/t0mind/ap/244cdf20/runs/e59f7158/m800/full_weights/model-00001-of-00005.safetensors` | 4,203,292,568 |
| `/scratch/jjyeung/orch_cd/mdg_build/work/data/t0mind/ap/244cdf20/runs/e59f7158/m800/full_weights/model-00005-of-00005.safetensors` | 1,794,087,688 |
