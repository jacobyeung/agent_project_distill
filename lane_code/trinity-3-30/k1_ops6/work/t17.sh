date -u +%FT%TZ
R=/scratch/jjyeung/orch_n30/trin_read/root
ls -la $R 2>&1 | head -12
ls -la $R/fsw/ap/97a6a3eb/runs/b19c1200/train/step_400/ 2>&1 | head -6
ls $R/fsw/ap 2>&1 | head; ls $R/project 2>&1 | head
E=/scratch/jjyeung/envs/vllm
ls $E/lib/python3*/site-packages 2>/dev/null | grep -iE "^(torch|transformers|numpy|scipy|pillow|fla|flash_linear|triton|safetensors|tokenizers)[-_].*(dist|egg)-info" | head -20
nvidia-smi --query-gpu=index,name,driver_version,memory.used,memory.total,utilization.gpu --format=csv,noheader 2>&1 | head -8
