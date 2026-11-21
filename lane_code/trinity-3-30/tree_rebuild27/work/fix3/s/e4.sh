W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
{
echo "--- inputs"; ls -la $W/inputs | head -30
echo "--- mirror"; ls -la $W/mirror | head -30
echo "--- ext"; ls -la $W/ext | head -30
echo "--- find manifest by sha"; timeout 60 find $W/inputs $W/mirror $W/ext -maxdepth 6 -name 'cc724d5e*' 2>/dev/null | head
echo "--- find model.json"; timeout 60 find $W/inputs $W/mirror $W/ext -maxdepth 6 -name 'model.json' 2>/dev/null | head
echo "--- snapshots on scratch"; ls -d /scratch/jjyeung/hf/hub/models--Qwen* /scratch/jjyeung/.cache/huggingface/hub/models--Qwen* /scratch/jjyeung/cache/huggingface/hub/models--Qwen* 2>/dev/null
echo "--- envs transformers"; for e in p1cpu vllm sam3_capretry_native_v1 nav_habitat024 planner_local_v1; do d=$(ls -d /scratch/jjyeung/envs/$e/lib/python3*/site-packages 2>/dev/null | head -1); echo "$e $(ls -d $d/transformers-*.dist-info $d/torch-*.dist-info $d/tokenizers-*.dist-info $d/safetensors-*.dist-info 2>/dev/null | xargs -n1 basename | tr '\n' ' ') qwen3_5=$(ls -d $d/transformers/models/qwen3_5 2>/dev/null | wc -l)"; done
} >&2
cat $W/w26fix2/s26fix2_n_go.tar
