W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
hostname -s; date -u +%FT%TZ; df -h /scratch | tail -1; uptime; free -g | sed -n 2p
ls -la $W/w27fix | head -40; ls -la $W/w28fix 2>&1 | head
echo "--- envs"
for e in vllm p1cpu; do d=$(ls -d /scratch/jjyeung/envs/$e/lib/python3*/site-packages | head -1); echo "$e: $d"; ls -d $d/torchvision-*.dist-info $d/torch-*.dist-info $d/transformers-*.dist-info $d/triton-*.dist-info $d/fla* $d/flash_linear* $d/einops-* $d/causal_conv1d* 2>/dev/null | xargs -n1 basename 2>/dev/null | tr '\n' ' '; echo; done
ls /scratch/jjyeung/envs | head -40
ls $W/w27fix/ovl $W/w27fix/ovl2 2>/dev/null | head -40
for e in p1cpu vllm; do
M=$(ls /scratch/jjyeung/envs/$e/lib/python3*/site-packages/transformers/models/qwen3_5/modeling_qwen3_5.py 2>/dev/null | head -1)
echo "=== $e $M"; [ -n "$M" ] && { sha256sum $M; grep -n "cuda\|is_fast_path_available\|FusedRMSNormGated\|warning_once\|fast path\|is_flash_linear_attention_available\|causal_conv1d" $M | cut -c1-220 | head -60; }
done
echo "--- torch cuda/__init__ key defs (p1cpu)"
C=$(ls /scratch/jjyeung/envs/p1cpu/lib/python3*/site-packages/torch/cuda/__init__.py); sha256sum $C; grep -n "^def \|^    _lazy_init()\|_lazy_init()" $C | head -150
