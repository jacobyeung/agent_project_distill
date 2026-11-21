W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w33n/n_go; O=$W/w30f1/n_go; C=$W/w31cen/n_go; R=$W/w32frm/n_go; T=/scratch/jjyeung/orch_n30/n_review/r1f/tcpx
date -u +%TZ
(cd $T && nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import sys; sys.path.insert(0,'.'); from launch_r1.build import verify; print('verify',verify('$K'))" < /dev/null 2>&1 | tail -1)
nice -n 10 sha256sum $W/w33n/s33n_n_go.tar < /dev/null | cut -c1-16
(cd $K && nice -n 10 sha256sum -c --quiet SHA256SUMS.txt < /dev/null; echo "check_rc=$? listed=$(wc -l < SHA256SUMS.txt) files=$(find . -type f < /dev/null | wc -l) pycache=$(find . -name __pycache__ < /dev/null | wc -l)"; sha256sum SHA256SUMS.txt < /dev/null | cut -c1-16)
echo "== members differing from F1 489f7f0f"; diff -rq $O $K < /dev/null
echo "== vs census test kit w31cen"; for f in b/cn.py b/sc.py; do cmp $C/$f $K/$f < /dev/null && echo "$f equal"; done
echo "== vs frame test kit w32frm"; cmp $R/k/j.json $K/k/j.json < /dev/null && echo "k/j.json equal"
echo "== pl.py merged vs F1"; diff $O/b/pl.py $K/b/pl.py < /dev/null
echo "== pf.py merged vs frame kit"; diff $R/b/pf.py $K/b/pf.py < /dev/null | head -80
sha256sum $K/b/*.py $K/k/j.json < /dev/null | awk '{print substr($1,1,8), $2}' | grep -E "cn.py|sc.py|pf.py|pl.py|cs.py|sv.py|j.json"
