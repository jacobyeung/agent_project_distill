ls /scratch/jjyeung/envs
for e in vllm p1cpu sam3_capretry_native_v1 rwtrain native; do P=/scratch/jjyeung/envs/$e/bin/python; [ -x $P ] || continue; echo "== $e"; timeout 120 $P -c "
import importlib
for m in ('torch','transformers','fla','safetensors','PIL','scipy','causal_conv1d'):
    try:
        x=importlib.import_module(m); print(m, getattr(x,'__version__','?'))
    except Exception as e: print(m,'MISSING',type(e).__name__)
" 2>&1 | grep -v Warning; done
which gsutil gcloud 2>&1 | head -2
ls /scratch/jjyeung/orch_n30/trin_read 2>&1 | head; ls -d /scratch/jjyeung/*/m544* /scratch/jjyeung/orch_n30/*/m544* 2>/dev/null | head
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
