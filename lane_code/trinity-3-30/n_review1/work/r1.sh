W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
mkdir -p /scratch/jjyeung/orch_n30/n_review
date -u +%TZ; df -BG --output=avail /scratch|tail -1
ls -la $W/w24/out | head -80
echo ==== kit_n_go; ls -la $W/w24/out/kit_n_go $W/w24/out/kit_n_go/k $W/w24/out/kit_n_go/b 2>&1 | head -80
echo ==== kits; ls $W/w24/out/kits 2>&1; ls $W/w24/work/ | head -50
echo ==== DELIVERY; cat $W/w24/out/DELIVERY_24F.json | head -c 4000
echo ==== tmux; tmux ls
