G=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z11b/a_zffhb1q8/armed/kits/n_go; T=$G/k/t_e047002134f979bd.tar; ls -la $T
for f in s1_admission.py production_proof.py; do m=$(tar tf $T | grep "/$f$\|^$f$" | head -1); echo "== $m"; done
m=$(tar tf $T | grep 's1_admission.py$' | head -1); tar xOf $T $m | grep -n 'setrlimit\|RLIMIT\|memory_gib\|def admit' | head; tar xOf $T $m | sed -n 125,150p
m=$(tar tf $T | grep 'production_proof.py$' | head -1); tar xOf $T $m | sed -n 135,186p
