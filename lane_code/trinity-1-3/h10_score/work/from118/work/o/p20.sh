export TZ=UTC
W=/project/community/jjyeung/okh7/e6fc152498; D=/project/community/jjyeung/b01ec87a6f29b
sha256sum $W/pkg3.tar | grep -q a08c061a8b58463263b136730ddbb57e0d9c593459fc8fc1ee4d452368093694 || { echo BADTAR; exit 1; }
mkdir -p $W/pkg_ecfad90f && cp -p $D/0.tgz $D/0.json $D/CONFIG.json $D/BATCH.sh $D/PACKAGE.json $D/2.json $W/pkg_ecfad90f/
tar -xf $W/pkg3.tar -C $D --overwrite && cd $D && sha256sum 0.tgz PACKAGE.json a/1.json
CUDA_VISIBLE_DEVICES= nice -n 19 /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00; echo "check rc=$?"
A_N=1 A_T=05:00:00 nice -n 19 bash SUBMIT.cmd --test-only; echo "test rc=$?"
tail -1 LEDGER.jsonl
tail -8 $W/rh.out
