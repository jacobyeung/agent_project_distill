D=/project/community/jjyeung/b01ec87a6f29b; W=/project/community/jjyeung/okh7/e6fc152498
sha256sum $W/pkg.tar; [ -z "$(ls -A $D)" ] && tar -xf $W/pkg.tar -C $D && cd $D && ls -la && sha256sum 0.json 0.tgz 3.py BATCH.sh CONFIG.json
cat $W/e.sha $W/b.done
