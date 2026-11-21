W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
cd $W/w24z8b/out || exit
ls -la . | head -80
echo ===kit; ls -la kit_qdp kit_qdp/* | head -80
echo ===jd7; cat -n jd7.sh
echo ===j7; wc -l j7.py; cat -n j7.py | head -130
echo ===n_go; ls -la $W/w24z11b/a_zffhb1q8/armed/kits/n_go $W/w24z11b/a_zffhb1q8/armed/kits/n_go/* | head -60
