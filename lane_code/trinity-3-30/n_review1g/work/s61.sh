K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z7/out/kit_n_go
grep -n "env_node" $K/b/z.py | head; grep -n "def .*env_node\|env_node=" $K/b/z.py | head; grep -n "z.py\|bootstrap\|execute\|launch(" $K/job.sh | head -8; grep -n "N=\|z.py\|pc.sh" $K/b/x.py | head -10
