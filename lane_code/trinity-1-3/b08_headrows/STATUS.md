# b08_headrows STATUS (2026-11-16T11:49:46Z)
Lane: headless Claude Opus on trinity-1-3. Brief: orch_n30/briefs/b08_headrows.md -> briefs/qs/08_head_path_rows_and_choice_join.md. Lane folder /scratch/jjyeung/orch_n30/b08_headrows (brief 08 text says head_rows; this lane uses b08_headrows).
## Part A (in progress)
- Copied over IB from trinity-1-18 into work/src118/: devs1_mask_run (SAM 3 default-density candidates + pricing kit incl. route_table.py), devs1_r2 heads (g3t, vcd, anchors, exports), orch_cd/{devs1_tower,devs1_direct,devs1_masks,o3_cache,devs1_price}.
- Lost with 2-18: devs1_masks/cache_r1 (PER_ITEM, ROUTE_PREDICTED.pairs). Rebuilding: code/pricekit = kit/work copy, one patch (prog_v2 VOCAB lazy; GT-ground arm only). code/run_price.sh prices 152 captures on CPU -> work/price_r1/<scene>/ (tmux b08price; done list work/logs/price_done.txt).
- Direct arms: parent = work/src118/devs1_mask_run/kit/out/DIRECT_ON16k.json (cp1m200); step 544 = trinity-1-3 /scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main/report/{ON16k,B2048}.json.
- Cue study (orch_cd/o3_cache/out/CUE_STUDY.md, 1-18): only the no-answer status reaches AUROC>=0.65 (0.79-0.82 direction/rel-distance); no printed non-status cue measured; best proxy 0.645 (low frame support, medium direction, answered items).
- K1 (1-18 /scratch/jjyeung/k1/run_tower_sam_2/<hash>/{candidates.json,tower.npz}, 305 dirs): tower+SAM outputs exist; no K1 VQA program responses found yet.
## Part B: waits for brief 05 cache + ORCH ruling.
