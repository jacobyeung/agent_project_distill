W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; M=$W/w24m; X=$W/w24x2; P=/scratch/jjyeung/envs/p1cpu/bin/python; N=/scratch/jjyeung/orch_n30/n_review; R=$N/r1f; T=$R/tcpx
date -u +%TZ; cat $X/out/tree_rebuild_b24m4x2_e3d14e7b.tar.sha256 2>&1; ls $X/work/build24/kits 2>&1
echo "== kit seals"; for k in $X/work/build24/kits/q $X/work/build24/kits/n $X/out/kit_n_go $X/out/kit_qd; do echo "$k sums=$(sha256sum < $k/SHA256SUMS.txt|cut -c1-64) GO=$(grep -o '"GO": *[a-z]*' $k/BUILD.json 2>/dev/null)"; (cd $T && nice -n 10 $P -I -s -B -c "import sys; sys.path.insert(0,'.'); from launch_r1.build import verify; print('verify',verify('$k'))" 2>&1 | tail -1); done
echo "== sums diffs 24m4m -> 24m4x2"; for p in work/build24/kits/q work/build24/kits/n out/kit_n_go out/kit_qd; do echo "-- $p"; diff <(sort -k2 $M/$p/SHA256SUMS.txt) <(sort -k2 $X/$p/SHA256SUMS.txt) | grep '^[<>]' | awk '{print $1, substr($2,1,12), $3}'; done
echo "== q vs n_go b/"; diff <(grep ' b/' $X/work/build24/kits/q/SHA256SUMS.txt|sort -k2) <(grep ' b/' $X/out/kit_n_go/SHA256SUMS.txt|sort -k2) | grep '^[<>]' | awk '{print $1,$3}' | sort -k2 -u | tr '\n' ' '; echo
echo "== n vs n_go b/"; diff <(grep ' b/' $X/work/build24/kits/n/SHA256SUMS.txt|sort -k2) <(grep ' b/' $X/out/kit_n_go/SHA256SUMS.txt|sort -k2) | grep '^[<>]' | awk '{print $1,$3}' | tr '\n' ' '; echo
echo "== qd vs n_go b/"; diff <(grep ' b/' $X/out/kit_qd/SHA256SUMS.txt|sort -k2) <(grep ' b/' $X/out/kit_n_go/SHA256SUMS.txt|sort -k2) | grep '^[<>]' | awk '{print $1,$3}' | sort -k2 -u | tr '\n' ' '; echo
echo "== identity"
k=$X/out/kit_n_go
nice -n 10 bwrap --ro-bind / / --tmpfs /home --tmpfs /data --tmpfs /data2 --tmpfs /data3 --tmpfs /scratch/jjyeung --ro-bind /scratch/jjyeung/envs/p1cpu /scratch/jjyeung/envs/p1cpu --ro-bind /scratch/jjyeung/uv-python /scratch/jjyeung/uv-python --tmpfs /tmp --ro-bind $T /tmp/x/tree --ro-bind $k/k /tmp/x/k --ro-bind $N/r1e/ident2.py /tmp/x/ident2.py --dev /dev --proc /proc --unshare-net --chdir /tmp/x env -i PATH=/usr/bin:/bin OMP_NUM_THREADS=2 $P -I -s -B /tmp/x/ident2.py > $R/ident_w24x2_tcpx.json 2>&1
sha256sum $N/r1e/ident2.py $R/ident_w24x2_tcpx.json; head -c 3000 $R/ident_w24x2_tcpx.json; echo
