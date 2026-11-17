export TZ=UTC
W=/project/community/jjyeung/okh7/e6fc152498; D=/project/community/jjyeung/b01ec87a6f29b
sha256sum $W/pkg6.tar | grep -q b874abf12225f6c6081f8ad38a8f45b4531cabf95b0460fd97ad7785b5d308e2 || { echo BADTAR; exit 1; }
sha256sum $W/1_t4.json | grep -q 4a2d652c094c6e1212c97614fdd6ec9c2fbd9cded534c2a12ca5d14c842756c0 || { echo BAD1; exit 1; }
[ -e $W/pkg_b1e209ee ] && { echo BACKUP_EXISTS; exit 1; }
mkdir -p $W/pkg_b1e209ee && cp -p $D/0.tgz $D/0.json $D/CONFIG.json $D/BATCH.sh $D/PACKAGE.json $D/a/1.json $W/pkg_b1e209ee/ && ls $D/2.json 2>/dev/null && cp -p $D/2.json $W/pkg_b1e209ee/
tar -xf $W/pkg6.tar -C $D --overwrite && cp $W/1_t4.json $D/a/1.json && chmod 600 $D/a/1.json && cd $D && sha256sum 0.tgz PACKAGE.json a/1.json
CUDA_VISIBLE_DEVICES= nice -n 19 /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 00:45:00 > $W/p28_check.out 2>&1; echo "check rc=$?"; tail -3 $W/p28_check.out | cut -c1-300
A_N=1 A_T=00:45:00 nice -n 19 bash SUBMIT.cmd --test-only 2>&1 | head -3; echo "test rc=$?"
squeue -u jjyeung -p general -h -o '%i %j %T'
