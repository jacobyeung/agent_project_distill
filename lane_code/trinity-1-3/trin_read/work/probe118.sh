hostname -s; df -h /scratch | tail -1
ls -la /scratch/jjyeung/k1/m544_parts/
ls /scratch/jjyeung/envs/
V=/scratch/jjyeung/envs/vllm
cat $V/pyvenv.cfg 2>/dev/null
ls $V/lib/python3*/site-packages | grep -i -E "^(vllm|torch|transformers|tokenizers|flash|xformers|triton|numpy|pillow|qwen|safetensors)[-_].*info" 
du -sh $V 2>/dev/null
nvidia-smi --query-gpu=index,name,memory.used --format=csv,noheader
