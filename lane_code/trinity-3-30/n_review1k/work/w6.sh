export TZ=UTC; date -u +%TZ
timeout 150 srun --overlap --jobid 174246 -N1 -n1 bash -s <<'EOS'
J=/tmp/q_22c714e1_174246
timeout 60 nice -n 10 find $J -maxdepth 6 \( -name '0482359088665775*' -o -name '07c2d3b0358fd6f1*' -o -name 'encoder.safetensors' -o -name 'heads.safetensors' \) 2>/dev/null | head
ls $J/p/q | head -40
grep -o '"0482359088665775014cb46c10f6d87a6f99c4203a978b6b6d1a74a50155438d": *"[^"]*"' $J/p/q/*.json $J/p/i/*.json $J/r.json 2>/dev/null | head -5
EOS
date -u +%TZ
