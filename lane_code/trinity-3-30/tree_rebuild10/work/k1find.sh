W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W && tar xzf - -C $W; sha256sum inputs/rooms/*
for n in K1SPLIT_R0.json alias_map.json d3_token_map.json a40fbc19.json; do echo "== $n"; find /scratch/jjyeung/orch_n30 /scratch/jjyeung/n30_mirror -maxdepth 7 -name $n 2>/dev/null | head -5; done
echo "== excl_check.py"; cat /scratch/jjyeung/n30_mirror/rows_r2/work/chk/excl_check.py; echo "== drop_k1.py"; cat /scratch/jjyeung/n30_mirror/rows_r2/work/chk/drop_k1.py
echo "== codeA common defs"; grep -nE "^def |^[A-Z_]+ *=" /scratch/jjyeung/n30_mirror/rows_r1/work/codeA/common.py | head -40
tail -c 600 $W/w16b/work/build16/STATUS.md
