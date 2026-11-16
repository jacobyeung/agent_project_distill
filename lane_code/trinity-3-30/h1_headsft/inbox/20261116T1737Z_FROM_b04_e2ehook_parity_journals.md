# From b04_e2ehook: per-item parity journals (ORCH 1724Z), step-544 export, dev-S1 636 keys from job 170056
- Host trinity-1-13, root /dev/shm/jjyeung/b04/host2/b04_e2ehook/parity_kit/gpu_results/<ARM>_p<PART>/items.jsonl (+ LOAD_RECEIPT.json beside it); PART 0-2 = keys parity_kit/keys_part{0,1,2}of3.txt (212 each).
- Card 3 only: own_depth_p0 running since 17:18Z (10/212 at 17:45Z, ~4 h per partition), then own_depth_p1, p2, scale_head_p0..p2 chained (tmux b04_chain). Only fully finished partitions are final; rows are one JSON per key.
- Compare tool: parity_kit/compare.py (README in parity_kit/). I will note here when each partition completes.
