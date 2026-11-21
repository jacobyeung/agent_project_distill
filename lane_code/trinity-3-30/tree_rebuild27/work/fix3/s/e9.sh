VS=/scratch/jjyeung/envs/vllm/lib/python3.12/site-packages
ls -la $VS/torchvision | head -12; ls $VS/torchvision | wc -l
ls -la $VS/torchvision-0.26.0.dist-info | head -8
ls -d /scratch/jjyeung/envs/*/lib/python3*/site-packages/torchvision/__init__.py 2>/dev/null
ls /scratch/jjyeung/uv-python/ 2>/dev/null | head; ls -d /scratch/jjyeung/.cache/uv /scratch/jjyeung/uv-cache 2>/dev/null
timeout 20 find /scratch/jjyeung -maxdepth 6 -name 'torchvision-0.26*' 2>/dev/null | head -8
