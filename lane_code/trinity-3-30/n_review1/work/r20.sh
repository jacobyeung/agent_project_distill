W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; M=/scratch/jjyeung/orch_n30/n_review; K=$W/w24/out/kit_n_go
echo "== identity hidden view"
nice -n 10 bwrap --ro-bind / / --tmpfs /home --tmpfs /data --tmpfs /data2 --tmpfs /data3 --tmpfs /scratch/jjyeung \
  --ro-bind /scratch/jjyeung/envs/p1cpu /scratch/jjyeung/envs/p1cpu --ro-bind /scratch/jjyeung/uv-python /scratch/jjyeung/uv-python --tmpfs /tmp --ro-bind $M/tree /tmp/x/tree --ro-bind $M/x/k /tmp/x/k --ro-bind $M/x/u /tmp/x/u --ro-bind $M/ident.py /tmp/x/ident.py \
  --dev /dev --proc /proc --unshare-net --chdir /tmp/x env -i PATH=/usr/bin:/bin OMP_NUM_THREADS=2 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /tmp/x/ident.py > $M/ident_out.json 2>&1; cat $M/ident_out.json; sha256sum $M/ident_out.json
echo "== tree tar top dirs"; tar tf $K/k/t_e047002134f979bd.tar | cut -d/ -f1-2 | sort -u | head -30
echo "== naming tests"; ls $W/w24/work/build24f/ | grep -i nam; head -c 1500 $W/w24/work/build24f/NAMING_TESTS.json; echo
echo "== manifest 87b68303"; for f in $(find $W/w24/work $W/ext -maxdepth 5 -name 'MANIFEST*.json' -size -2M 2>/dev/null | head -40); do h=$(sha256sum < $f | cut -c1-8); [ "$h" = 87b68303 ] && { echo $f; head -c 3000 $f; echo; break; }; done
echo "== resolver tests"; head -c 2500 $W/w24/work/build24d/RESOLVER_TESTS.json; echo
echo "== rehearsal"; ls $W/w24/work/build24f/ | grep -i "rehears\|FIX"; tail -25 $W/w24/work/build24f/rehearsal_run.log; ls -la $W/w24/work/build24f/rehearsal 2>&1 | head; cat $W/w24/work/build24f/REHEARSAL_FIX_REPORT.md 2>&1 | head -40
