ls -la /scratch/jjyeung/orch_n30/tree_rebuild15_w24l/out/ 2>&1 | grep -i "24l4t\|BUILD24L4T" ; ls /scratch/jjyeung/orch_n30/ | grep -i tree_rebuild; df -h /scratch | tail -1
F=/scratch/jjyeung/orch_n30/fb_pack; for p in patchA2 donor3 camform2; do echo "== $p"; ls $F/$p/out | tr '\n' ' '; echo; done
head -c 1200 $F/patchA2/out/FILES_TOUCHED.json; echo; head -c 800 $F/patchA2/out/TESTS.json; echo; ls $F/camform2/out/*.patch
/scratch/jjyeung/envs/p1cpu/bin/python -c "import pytest;print('pytest',pytest.__version__)"
