B=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w26trace
cd $B && nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B -I - <<'PY'
import ast, re
from pathlib import Path
S = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w26trace/s')
pat = re.compile(r'qwen3_5|Qwen3_5|AutoModel|AutoProcessor|AutoConfig|from_pretrained|import transformers|from transformers|causal_conv1d|is_torch_cuda_available|torch\.cuda\.')
files = ['carrier_c1_run','carrier_c1_data','s1_routing','mdg_parent','r1_routing','r1_handover','s1_admission','row_removals',
         'first_batch_progress','s1_exclusions','rehearsal','r1_coverage','orchard_paths','grounding_train','students','carrier_c1','p3_provenance']
for f in files:
    p = S/'student_pilot'/(f+'.py'); src = p.read_text().splitlines(); tree = ast.parse('\n'.join(src))
    spans = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)): spans.append((n.lineno, n.end_lineno, n.name))
    for i, l in enumerate(src, 1):
        if pat.search(l):
            fn = [s for s in spans if s[0] <= i <= s[1]]; fn = min(fn, key=lambda s: s[1]-s[0])[2] if fn else '<module>'
            print(f'{f}.py:{i} [{fn}] {l.strip()[:150]}')
PY
/scratch/jjyeung/envs/p1cpu/bin/python -B -I -c "import transformers;print('transformers',transformers.__version__)"
sed -n 55,75p /scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/transformers/models/qwen3_5/modeling_qwen3_5.py
