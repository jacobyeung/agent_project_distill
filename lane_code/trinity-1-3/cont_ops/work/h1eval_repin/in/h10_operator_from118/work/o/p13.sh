W=/project/community/jjyeung/okh7/e6fc152498
cat > $W/x.sh <<'EOS'
set -u
W=/project/community/jjyeung/okh7/e6fc152498; X=$W/x; mkdir -p $X/sj/b01ec87a6f29b/p $X/sj/b01ec87a6f29b/d $X/m/ap; cd $X
K=/home/jjyeung/okit/p/d59945c1; B=/project/community/jjyeung/bd8ae51c/p/d59945c1
cat $K/4fe70504.00 $K/4fe70504.01 | tar xf - 'sj/uv-python' ; echo "g0 rc=$? $(date -u +%T)" >> $W/x.done
cat $K/50011a59.0{0,1,2,3,4} $B/50011a59.0{5,6,7,8,9} | tar xf - ; echo "g1 rc=$? $(date -u +%T)" >> $W/x.done
tar xzf /project/community/jjyeung/b01ec87a6f29b/0.tgz -C sj/b01ec87a6f29b/p; echo "p rc=$? $(date -u +%T)" >> $W/x.done
cp /project/community/jjyeung/cp4tk_rt/kit/bwrap $X/bwrap && chmod 700 $X/bwrap && $X/bwrap --version >> $W/x.done 2>&1
EOS
nohup nice -n 19 ionice -c3 bash $W/x.sh > $W/x.out 2>&1 < /dev/null & echo xstarted
sha256sum /project/community/jjyeung/cp4tk_rt/kit/bwrap
