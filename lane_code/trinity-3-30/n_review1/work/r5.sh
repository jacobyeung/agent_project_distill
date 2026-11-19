W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
cd $W; for h in 210b2534 4e8e6c04 ca0616db 8957d119 93b21a3a e3ee51da 56d34799 ff7c98eb a1a79d79 b6fdc34e c0167f68 e84f4dc9 aa77ee19 7b3d696d; do echo "== $h"; find . -maxdepth 7 -name "*$h*" -printf '%p %s %y %l\n' 2>/dev/null | head -5; done
ls $W/w24/work/build24f | head -80
ls /scratch/jjyeung/orch_n30/ | head -80
