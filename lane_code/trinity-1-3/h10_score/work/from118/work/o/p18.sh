export TZ=UTC
W=/project/community/jjyeung/okh7/e6fc152498; D=/project/community/jjyeung/b01ec87a6f29b
sha256sum $W/pkg2.tar
mkdir -p $W/pkg_old && cp -p $D/0.tgz $D/0.json $D/CONFIG.json $D/BATCH.sh $D/PACKAGE.json $D/2.json $W/pkg_old/ 2>/dev/null
tar -xf $W/pkg2.tar -C $D --overwrite && cd $D && ls -la && sha256sum 0.tgz 0.json CONFIG.json BATCH.sh PACKAGE.json 3.py SUBMIT.cmd
echo "== pool"; du -sb /project/community/jjyeung/okh7/ae71c903; ls -la /project/community/jjyeung/okh7/ae71c903 | head -20
