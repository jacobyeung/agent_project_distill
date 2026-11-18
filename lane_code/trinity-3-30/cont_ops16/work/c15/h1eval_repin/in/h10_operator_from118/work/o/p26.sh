export TZ=UTC
W=/project/community/jjyeung/okh7/e6fc152498; D=/project/community/jjyeung/b01ec87a6f29b
sha256sum $W/pkg5.tar | grep -q cbd1cedef8d22333d39ce753e65879c1e590c4dd2d5fcc8f41a42d7e8d6fb5ff || { echo BADTAR; exit 1; }
sha256sum $W/1_t34.json | grep -q 7f09c22e8c6d8ac6bc3a27ee947ecd9f5344c8342aca762847888eb585f245f1 || { echo BAD1; exit 1; }
mkdir -p $W/pkg_e82ac329 && cp -p $D/0.tgz $D/0.json $D/CONFIG.json $D/BATCH.sh $D/PACKAGE.json $D/2.json $D/a/1.json $W/pkg_e82ac329/
tar -xf $W/pkg5.tar -C $D --overwrite && cp $W/1_t34.json $D/a/1.json && chmod 600 $D/a/1.json && cd $D && sha256sum 0.tgz PACKAGE.json a/1.json
CUDA_VISIBLE_DEVICES= nice -n 19 /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 03:00:00 > /dev/null; echo "check rc=$?"
A_N=1 A_T=03:00:00 nice -n 19 bash SUBMIT.cmd --test-only 2>&1 | head -2; echo "test rc=$?"
squeue -u jjyeung -p general -h -o '%i %j %T'
