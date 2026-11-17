# usage: bash merge_ns.sh <return token>   (run on Orchard login after the job returned)
set -u
T=$1; W=/project/community/jjyeung/okh7/e6fc152498; X=$W/r2; D=/project/community/jjyeung/b01ec87a6f29b
cd $D && /usr/bin/python3 -I -s -B 3.py fetch --return-token $T --out $W/fetch_$T || exit 1
mkdir -p $X/sj/h10ret_$T && tar xzf $W/fetch_$T/0.tgz -C $X/sj/h10ret_$T || exit 1
J=/scratch/jjyeung/h10ret_$T/metadata/journals
A=( $X/bwrap )
for n in usr bin sbin lib lib64 etc opt run sys; do p=/$n; if [ -L $p ]; then A+=(--symlink "$(readlink $p)" $p); elif [ -e $p ]; then A+=(--ro-bind $p $p); fi; done
A+=(--dev-bind /dev /dev --proc /proc --bind /tmp /tmp --dir /scratch --bind $X/sj /scratch/jjyeung --bind $X/fsw /scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung --dir /lustre --bind $X/m/ap /lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap --ro-bind $X/sj/uv-python/cpython-3.12.13-linux-x86_64-gnu /home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu --dir /home/jjyeung --die-with-parent --chdir /scratch/jjyeung/b01ec87a6f29b/p)
DIRS=$(cd $X/sj/h10ret_$T/metadata/journals && ls -d */* | sed "s,^,$J/," | tr '\n' ' ')
env -i PATH=/usr/local/bin:/usr/bin:/bin USER=$USER HOME=$X/home TMPDIR=$X/temp CUDA_VISIBLE_DEVICES= HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=4 \
  timeout 3000 nice -n 19 "${A[@]}" /scratch/jjyeung/b01ec87a6f29b/d/v/py -B -I /scratch/jjyeung/b01ec87a6f29b/p/h1eval/h10/merge.py --type-layout $DIRS --items /scratch/jjyeung/b01ec87a6f29b/p/items/devs1_routed.json --out /scratch/jjyeung/h10merged_$T
echo "merge rc=$?"
