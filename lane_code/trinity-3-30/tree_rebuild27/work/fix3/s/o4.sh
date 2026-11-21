export TZ=UTC
V=/project/community/jjyeung/cp4tk_rt/kit/venv_rwtrain_torch211_cu129.tar
ls -la /project/community/jjyeung/cp4tk_rt/kit/ | head -20
ls -la $V
ls /project/community/jjyeung/okh7/x_ee227714/b/ 2>/dev/null | tr '\n' ' '; echo
echo "=== kitx.py"; cat /project/community/jjyeung/okh7/x_ee227714/b/kitx.py 2>/dev/null | head -60
echo "=== venv tar scan"
timeout 200 tar tvf $V 2>/dev/null | grep -E "bin/python|pyvenv.cfg|site-packages/(transformers|torch|torchvision|tokenizers|triton|fla|flash_linear_attention|safetensors|numpy|accelerate)-[^/]*(dist-info|egg-info)/?$|models/qwen3_5/modeling_qwen3_5.py" | cut -c1-260 | head -40
echo "scan rc=${PIPESTATUS[0]}"
ls -d /project/community/jjyeung/*/venvs/rwtrain_torch211_cu129 /project/community/jjyeung/*/*/venvs/rwtrain_torch211_cu129 2>/dev/null | head
df -BG --output=avail /project/community | tail -1
