W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; A=$W/w24z11b/a_zffhb1q8/armed/kits/n_go; F=$W/w26fix; P=/scratch/jjyeung/envs/p1cpu/bin/python; date -u +%TZ
test -e $F && { echo EXISTS; exit 1; }; mkdir -p $F/src $F/tree && cd $F/src && tar xf - && cp -a $A $F/n_go
grep -n 'code_sha256\|p_kit_identity' $F/n_go/b/*.py | cut -c1-160 | head -8; grep -l 'e3ef430d0a09a21f' -r $F/n_go | head
$P -I -s -B $F/src/patch.py $F/n_go
cd $F/n_go/b && $P -I -s -B -c "import sys;sys.path.insert(0,'.');from z import seal;print('z.seal',seal('$F/n_go'))"
diff -rq $A $F/n_go; diff $A/b/a.py $F/n_go/b/a.py
tar xf $A/k/t_e047002134f979bd.tar -C $F/tree student_pilot launch_r1 2>/dev/null || tar xf $A/k/t_e047002134f979bd.tar -C $F/tree
for m in before after; do nice -n 10 timeout 120 $P -I -s -B $F/src/t_fix.py $F/tree $m 2>&1 | tail -1; done
grep -n "Q_KIT=\|Q_KIT:" /dev/null; $P -I -s -B -c "import ast;ast.parse(open('$F/n_go/b/a.py').read());print('a.py parses')"
