D=/scratch/jjyeung/orch_n30/fb_pack/score400n; mkdir -p $D; K=/scratch/jjyeung/orch_n30/sb_own400/kit
/scratch/jjyeung/envs/p1cpu/bin/python -B - <<'P'
src=open('/scratch/jjyeung/orch_n30/sb_own400/kit/score_400.py').read()
a="    assert np.array_equal(z['frame_indices'],c['anchor_indices'])\n    assert np.array_equal(z['grid_uv'],np.linspace(0,1000,51,dtype=np.float32))\n"
b="    # Native layout (job 173346): same keys and producer as the accepted step-544 arm A; anchors bound by capture_sha256 above.\n    assert sorted(z.files)==['depth','gravity'] and rec['producer_sha256']==read(r['own544']['receipt'])['producer_sha256']\n"
assert src.count(a)==1
src=src.replace(a,b).replace("import numpy as np\nfrom core import *","import numpy as np\nsys.path.insert(0,'/scratch/jjyeung/orch_n30/sb_own400/kit')\nfrom core import *",1)
assert "sys.path.insert" in src
open('/scratch/jjyeung/orch_n30/fb_pack/score400n/score_400n.py','w').write(src)
P
diff $K/score_400.py $D/score_400n.py > $D/DIFF_vs_score_400.txt; cat $D/DIFF_vs_score_400.txt; sha256sum $K/score_400.py $D/score_400n.py $D/DIFF_vs_score_400.txt | cut -c1-16,65-
cd /scratch/jjyeung/orch_n30/sb_own400 && tmux new-session -d -s fbp3_score400n "env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B $D/score_400n.py --own-root in/own_400/native/probe --out out/real400_score_n > out/real400_score_n.log 2>&1; echo EXIT \$? >> out/real400_score_n.log" </dev/null >/dev/null 2>&1
sleep 60; tail -5 out/real400_score_n.log
