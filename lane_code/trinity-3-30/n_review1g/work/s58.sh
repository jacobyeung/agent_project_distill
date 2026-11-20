W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Y=$W/w24y2; Z=$W/w24z4; P=/scratch/jjyeung/envs/p1cpu/bin/python; N=/scratch/jjyeung/orch_n30/n_review; R=$N/r1g; T=$N/r1f/tcpx
date -u +%TZ; ls $Z/out | grep -v '^BUILD24M[0-3]\|^DELIVERY_24M[0-3]' | tr '\n' ' '; echo; ls $Z/out/*.tar* 2>/dev/null; cat $Z/out/*.tar.sha256 2>/dev/null | cut -c1-120
echo "== kit seals"; for k in $Z/work/build24/kits/q $Z/work/build24/kits/n $Z/out/kit_n_go $Z/out/kit_qd; do echo "$k sums=$(sha256sum < $k/SHA256SUMS.txt|cut -c1-64) GO=$(grep -o '"GO": *[a-z]*' $k/BUILD.json 2>/dev/null)"; (cd $T && nice -n 10 $P -I -s -B -c "import sys; sys.path.insert(0,'.'); from launch_r1.build import verify; print('verify',verify('$k'))" 2>&1 | tail -1); done
echo "== sums diffs 24m4y2 -> 24m4z4"; for p in work/build24/kits/q work/build24/kits/n out/kit_n_go out/kit_qd; do echo "-- $p"; diff <(sort -k2 $Y/$p/SHA256SUMS.txt) <(sort -k2 $Z/$p/SHA256SUMS.txt) | grep '^[<>]' | awk '{print $1, substr($2,1,12), $3}'; done
echo "== n vs n_go b/"; diff <(grep ' b/' $Z/work/build24/kits/n/SHA256SUMS.txt|sort -k2) <(grep ' b/' $Z/out/kit_n_go/SHA256SUMS.txt|sort -k2) | grep '^[<>]' | awk '{print $1,$3}' | tr '\n' ' '; echo
echo "== qd vs n_go b/"; diff <(grep ' b/' $Z/out/kit_qd/SHA256SUMS.txt|sort -k2) <(grep ' b/' $Z/out/kit_n_go/SHA256SUMS.txt|sort -k2) | grep '^[<>]' | awk '{print $1,$3}' | sort -k2 -u | tr '\n' ' '; echo
echo "== identity"
k=$Z/out/kit_n_go
nice -n 10 bwrap --ro-bind / / --tmpfs /home --tmpfs /data --tmpfs /data2 --tmpfs /data3 --tmpfs /scratch/jjyeung --ro-bind /scratch/jjyeung/envs/p1cpu /scratch/jjyeung/envs/p1cpu --ro-bind /scratch/jjyeung/uv-python /scratch/jjyeung/uv-python --tmpfs /tmp --ro-bind $T /tmp/x/tree --ro-bind $k/k /tmp/x/k --ro-bind $N/r1e/ident2.py /tmp/x/ident2.py --dev /dev --proc /proc --unshare-net --chdir /tmp/x env -i PATH=/usr/bin:/bin OMP_NUM_THREADS=2 $P -I -s -B /tmp/x/ident2.py > $R/ident_w24z4_tcpx.json 2>&1
sha256sum $N/r1e/ident2.py $R/ident_w24z4_tcpx.json; grep -o '"[a-z_]*identity[a-z_]*": *"[0-9a-f]*"\|"[a-z_]*sha256": *"[0-9a-f]*"' $R/ident_w24z4_tcpx.json | head -8
echo "== decoded"; bash -s < /dev/stdin <<'EOS'
EOS
