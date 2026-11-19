# User-only cleanup queue

The shared workspace exceeds 3 GB after concurrent review directories appeared. This task's last pre-growth allocation measurement was 2,879,635,456 bytes; `SPACE_STATE.json` records the overage and directory totals.

The user-supplied AGENTS.md says, “Never run file-deletion commands.” This task also permits writes only under so_pack, so the central queue under `/home` cannot be updated here. These commands have **not** run. The user must review whether another active review still needs these old fixtures before executing them.

- [ ] `rm -rf -- /scratch/jjyeung/orch_n30/so_pack/work/tests01 /scratch/jjyeung/orch_n30/so_pack/work/tests02 /scratch/jjyeung/orch_n30/so_pack/work/tests03 /scratch/jjyeung/orch_n30/so_pack/work/tests05 /scratch/jjyeung/orch_n30/so_pack/work/tests06 /scratch/jjyeung/orch_n30/so_pack/work/tests07 /scratch/jjyeung/orch_n30/so_pack/work/final_tests /scratch/jjyeung/orch_n30/so_pack/work/verified_tests`

This preserves the final test sources/results, builder-property inputs/results, validated tool, patches, reports, and every `review1_*` directory. No concurrent job or agent was stopped.
