W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; F=$W/w33n; cd $F
ls -la; wc -c test1.t1.log; head -c 1500 test1.t1.log; ls t1tmp 2>&1|head; cat TEST_T1_33.json 2>&1 | head -c 3000
for f in b/cn.py b/sc.py; do sha256sum $W/w31cen/n_go/$f test1/n_go/$f; stat -c '%a %n' $W/w31cen/n_go/$f test1/n_go/$f; done
diff $W/w31cen/n_go/b/sc.py test1/n_go/b/sc.py | head -20; diff $W/w31cen/n_go/b/cn.py test1/n_go/b/cn.py | head -20
grep -n 'cn.py\|sc.py\|pl.py' $W/w31cen/n_go/SHA256SUMS.txt; ls -la --time-style=+%FT%T $W/w31cen/n_go/b/cn.py $W/w31cen/n_go/b/sc.py $W/w31cen/n_go/b/pl.py
