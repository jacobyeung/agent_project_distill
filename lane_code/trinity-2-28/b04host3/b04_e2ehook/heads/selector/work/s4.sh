set -u
L=/scratch/jjyeung/orch_n30/b04_e2ehook_sl; cd $L
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8
/scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import numpy as np,json
m=json.load(open('/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json'))
for c in m['captures'][:3]:
    z=np.load(c['gt']['path'])
    print(c['canonical'], {k:(z[k].shape,z[k].dtype) for k in z.files})
PY
P=/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python
$P -c "import sam3,os;print(sam3.__file__);print(os.listdir(os.path.dirname(sam3.__file__)))"
SP=$($P -c "import sam3,os;print(os.path.dirname(sam3.__file__))")
grep -n "def forward_text" -A40 $SP/model/vl_combiner.py 2>/dev/null | head -60
grep -rn "def build_sam3_image_model" -A30 $SP/model_builder.py | head -45
grep -n "forward_text\|def set_text_prompt" -A6 $SP/model/sam3_image_processor.py | head -30
