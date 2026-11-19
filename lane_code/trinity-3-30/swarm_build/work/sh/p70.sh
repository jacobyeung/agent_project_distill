R=/scratch/jjyeung/orch_n30/sb_ktfix
cat $R/scripts/gpu_environment.sh; echo ====; grep -n -E "GPU_GO|RESERVATION|ledger|def preflight|def admit|code_sha|reservation|DA3_GO|next_authorized|hard_seconds|card" $R/code/runner.py | head -60; echo ===; wc -l $R/code/runner.py
