G=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z11b/a_zffhb1q8/armed/kits/n_go; P=/scratch/jjyeung/envs/p1cpu/bin/python
cd $G/b; $P -I -s -B -c "import sys;sys.path.insert(0,'.');from z import load;import json;j=load('$G/k/j.json');s=j if isinstance(j,str) else json.dumps(j);open('/tmp/jsh_tr26.txt','w').write(s)" && grep -n 'a\.py\|t\.py\|torchrun\|ulimit\|rv\.py\|h\.py\|d\.py\|o\.py' /tmp/jsh_tr26.txt | cut -c1-220 | head -30
echo ===a.py; cat -n a.py | sed -n 1,95p | cut -c1-200
echo ===t.py head; grep -n 'Popen\|subprocess\|torchrun\|setrlimit\|RLIMIT\|def main' t.py | head -20
T=$G/k/t_e047002134f979bd.tar; m=$(tar tf $T | grep 'production_proof.py$'); tar xOf $T $m | grep -n 'def scope\|def run\|def _run\|def forward\|sys.path\|import' | head -30
