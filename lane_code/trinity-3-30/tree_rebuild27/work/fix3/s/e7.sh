W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; T=$W/w27fix/t1
date -u +%TZ
for e in vllm p1cpu; do d=$(ls -d /scratch/jjyeung/envs/$e/lib/python3*/site-packages | head -1); echo "$e: $(ls -d $d/torchvision-*.dist-info $d/torch-*.dist-info $d/transformers-*.dist-info $d/triton-*.dist-info $d/fla* $d/flash_linear* 2>/dev/null | xargs -n1 basename 2>/dev/null | tr '\n' ' ') py=$(/scratch/jjyeung/envs/$e/bin/python -I -c 'import sys;print(sys.version.split()[0])')"; done
echo "--- tokenizer_for_rows"; grep -n "def tokenizer_for_rows" -A14 $T/s/generator/derivgen_v7/derivgen/ground_v313_tokens.py | head -24
echo "--- modeling import-time checks"; M=/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/transformers/models/qwen3_5/modeling_qwen3_5.py
grep -n "is_fast_path_available\|cuda\|causal_conv1d\|import fla\|from fla\|is_flash_linear\|triton" $M | head -30
grep -rn "def is_flash_linear_attention_available" -A12 /scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/transformers/utils/import_utils.py | head -30
echo "--- pose receipt"; ls $W/ext/preceipts/rc3/u | head -5; ls $W/ext/preceipts/rc3/u | wc -l
for h in 8957d119bfa6776efe776816675da6d0f610a6e8c336acd66c297f29cf4e7e0f; do f=$W/ext/preceipts/rc3/u/$h; [ -f $f ] && /scratch/jjyeung/envs/p1cpu/bin/python -I -c "
import json,sys
d=json.load(open('$f')); print('pose keys',sorted(d)[:30]); print('model',d.get('model')); print('sources',[ (s.get('kind'),s.get('receipt')) for s in d.get('sources',[])][:6])
"; done
echo "--- P prep receipt keys"; /scratch/jjyeung/envs/p1cpu/bin/python -I -c "
import json,glob
u='$T/ns/q_22c714e1/p/q/u/'
for f in glob.glob(u+'a5bbef1b*'):
    d=json.load(open(f)); print(sorted(d)); print({k:d.get(k) for k in ('training_mode','frame_count','frame_markers','geometry_online','mdg','model','schema')}); print('b7' , str(d.get('b7_inputs'))[:300])
for f in glob.glob(u+'5083243c*'):
    d=json.load(open(f)); print('artifact keys',sorted(d)); print('routing_vocabulary',str(d.get('routing_vocabulary'))[:200]); print({k:d.get(k) for k in ('heads','full_weights','step','schema')})
"
