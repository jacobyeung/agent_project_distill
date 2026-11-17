cd /scratch/jjyeung/orch_n30/b04host3/b04_e2ehook 2>/dev/null && pwd && ls && du -sh work/n13/obj/base work/n13 heads tests 2>&1 | head
ls work/n13/obj/base/models--Qwen--Qwen3.5-9B/snapshots/*/ 2>&1 | head -30
du -sh /scratch/jjyeung/n30_mirror/k1_ops3/run_tower_sam_2 2>&1; ls /scratch/jjyeung/n30_mirror/k1_ops3/run_tower_sam_2 2>&1 | head
grep -h -o -E "ROOT ?/ ?'[^']+'|/scratch/[A-Za-z0-9_./-]+" tests/*.py | sort | uniq -c | head -40
