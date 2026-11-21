R=/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs; C=/scratch/jjyeung/orch_n30/lever1_c
tar cf - -C / --transform 's#.*r4boot2rev/final_message.md#r4rev.md#;s#.*r1bootrev/final_message.md#r1rev.md#;s#.*/delivery.tgz#delivery.tgz#' ${R#/}/20261121T004628Z_lever3_r4boot2rev/final_message.md ${R#/}/20261121T004629Z_lever3_r1bootrev/final_message.md ${C#/}/r4kit/out/delivery.tgz
