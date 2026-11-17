D=/project/community/jjyeung/b01ec87a6f29b; W=/project/community/jjyeung/okh7/e6fc152498
cat $W/b.done 2>/dev/null; ls -la $W/e 2>/dev/null; cat $W/term2.sha 2>/dev/null | tail -5
if [ -e $D ]; then echo "EXISTS $D"; ls -la $D; else
 mkdir -m 755 $D && head -c 5304320 > $W/pkg.tar && sha256sum $W/pkg.tar && tar -xf $W/pkg.tar -C $D && ls -la $D && cd $D && sha256sum 0.json 0.tgz 3.py BATCH.sh CONFIG.json; fi
