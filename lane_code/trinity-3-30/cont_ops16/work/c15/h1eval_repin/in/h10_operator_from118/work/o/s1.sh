W=/project/community/jjyeung/okh7/e6fc152498
cat > $W/sub2_ns.sh <<'EOS'
set -u
# usage: sub2_ns.sh <return token> <type idx list e.g. 4 or 3> ; scores with the payload in W/p446 (0.tgz 446a4323) bound over the old p
W=/project/community/jjyeung/okh7/e6fc152498; X=$W/r2; T=$1; N=$2; PN=$W/p446
[ -d $PN ] || { mkdir -p $PN && sha256sum /project/community/jjyeung/b01ec87a6f29b/0.tgz | grep -q 446a432306b8e68e && tar xzf /project/community/jjyeung/b01ec87a6f29b/0.tgz -C $PN; }
mkdir -p $X/sj/h10ret_$T && [ -z "$(ls -A $X/sj/h10ret_$T)" ] && tar xzf /project/community/jjyeung/okh7/ae71c903/$T/result.tar.gz -C $X/sj/h10ret_$T
cp $W/submerge2.py $X/sj/submerge2.py
A=( $X/bwrap )
for n in usr bin sbin lib lib64 etc opt run sys; do p=/$n; if [ -L $p ]; then A+=(--symlink "$(readlink $p)" $p); elif [ -e $p ]; then A+=(--ro-bind $p $p); fi; done
A+=(--dev-bind /dev /dev --proc /proc --bind /tmp /tmp --dir /scratch --bind $X/sj /scratch/jjyeung --ro-bind $PN /scratch/jjyeung/b01ec87a6f29b/p --bind $X/fsw /scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung --dir /lustre --bind $X/m/ap /lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap --ro-bind $X/sj/uv-python/cpython-3.12.13-linux-x86_64-gnu /home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu --dir /home/jjyeung --die-with-parent --chdir /scratch/jjyeung)
env -i PATH=/usr/local/bin:/usr/bin:/bin USER=$USER HOME=$X/home TMPDIR=$X/temp CUDA_VISIBLE_DEVICES= HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=4 \
  timeout 3000 nice -n 19 "${A[@]}" /scratch/jjyeung/b01ec87a6f29b/d/v/py -B -I /scratch/jjyeung/submerge2.py /scratch/jjyeung/h10ret_$T/metadata/journals /scratch/jjyeung/h10sub_$T $N > $W/sub_$T.out 2>&1
echo "sub rc=$?" >> $W/sub_$T.out
EOS
sha256sum $W/sub2_ns.sh | cut -c1-16
nohup nice -n 19 bash $W/sub2_ns.sh b01ec87a6f29b00029ac6 4 > $W/sub2_ac6.nohup 2>&1 < /dev/null &
sleep 45; cat $W/sub_b01ec87a6f29b00029ac6.out 2>/dev/null | tail -30
