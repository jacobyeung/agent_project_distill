export TZ=UTC
W=/project/community/jjyeung/okh7/e6fc152498; D=/project/community/jjyeung/b01ec87a6f29b
sha256sum $W/pkg4.tar | grep -q ee17ee85824fae7cf64c4d5a30c8a9d7df947adf05f0a5ecf6abf23d9d704c9c || { echo BADTAR; exit 1; }
mkdir -p $W/pkg_2dd91b3b && cp -p $D/0.tgz $D/0.json $D/CONFIG.json $D/BATCH.sh $D/PACKAGE.json $D/2.json $D/LEDGER.jsonl $W/pkg_2dd91b3b/
tar -xf $W/pkg4.tar -C $D --overwrite && cd $D && sha256sum 0.tgz PACKAGE.json a/1.json
CUDA_VISIBLE_DEVICES= nice -n 19 /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00 >/dev/null; echo "check rc=$?"; cat 2.json | head -c 300; echo
A_N=1 A_T=05:00:00 nice -n 19 bash SUBMIT.cmd --test-only; echo "test rc=$?"
nohup nice -n 19 ionice -c3 bash $W/rh2_setup.sh > $W/rh2_setup.out 2>&1 < /dev/null & echo rh2started
