set -uo pipefail
test "$(hostname -s)" = trinity-1-18 || exit 9
R=/scratch/jjyeung/orch_cd/dose_pool/out
cd $R || exit 8
cat > /tmp/c24_gt60.txt <<'EOL'
arkit_gt/gt/41069053.npz
arkit_gt/gt/41069054.npz
arkit_gt/gt/41098140.npz
arkit_gt/gt/41098149.npz
arkit_gt/gt/41126645.npz
arkit_gt/gt/41159771.npz
arkit_gt/gt/41159772.npz
arkit_gt/gt/41159782.npz
arkit_gt/gt/41254810.npz
arkit_gt/gt/41291639.npz
arkit_gt/gt/41291643.npz
arkit_gt/gt/42446097.npz
arkit_gt/gt/42446117.npz
arkit_gt/gt/42897921.npz
arkit_gt/gt/42897936.npz
arkit_gt/gt/42897942.npz
arkit_gt/gt/42899532.npz
arkit_gt/gt/42899535.npz
arkit_gt/gt/42899829.npz
arkit_gt/gt/43649603.npz
arkit_gt/gt/43828324.npz
arkit_gt/gt/43828368.npz
arkit_gt/gt/44358634.npz
arkit_gt/gt/45261332.npz
arkit_gt/gt/45663051.npz
arkit_gt/gt/47330997.npz
arkit_gt/gt/47331002.npz
arkit_gt/gt/47332556.npz
arkit_gt/gt/47332598.npz
arkit_gt/gt/47332599.npz
t1_gt/gt/scannet__scene0166_00.npz
t1_gt/gt/scannet__scene0166_02.npz
t1_gt/gt/scannet__scene0250_01.npz
t1_gt/gt/scannet__scene0261_02.npz
t1_gt/gt/scannet__scene0320_01.npz
t1_gt/gt/scannet__scene0380_01.npz
t1_gt/gt/scannet__scene0515_00.npz
t1_gt/gt/scannet__scene0515_01.npz
t1_gt/gt/scannet__scene0515_02.npz
t1_gt/gt/scannet__scene0642_01.npz
t1_gt/gt/scannet__scene0666_01.npz
t1_gt/gt/scannetppv2__0c7962bd64.npz
t1_gt/gt/scannetppv2__17c5e6a336.npz
t1_gt/gt/scannetppv2__246fe09e98.npz
t1_gt/gt/scannetppv2__307e3262f1.npz
t1_gt/gt/scannetppv2__37c9538a2b.npz
t1_gt/gt/scannetppv2__38fcf02d0b.npz
t1_gt/gt/scannetppv2__3ce6d36ab5.npz
t1_gt/gt/scannetppv2__6a217fbcb0.npz
t1_gt/gt/scannetppv2__7e7cd69a59.npz
t1_gt/gt/scannetppv2__80ffca8a48.npz
t1_gt/gt/scannetppv2__99a2503d63.npz
t1_gt/gt/scannetppv2__aaa9c251de.npz
t1_gt/gt/scannetppv2__ad562ce09b.npz
t1_gt/gt/scannetppv2__ca3b651c23.npz
t1_gt/gt/scannetppv2__d6bb698875.npz
t1_gt/gt/scannetppv2__e35232b92f.npz
t1_gt/gt/scannetppv2__e667e09fe6.npz
t1_gt/gt/scannetppv2__e7ccd75e5d.npz
t1_gt/gt/scannetppv2__eb8ef9b4cc.npz
EOL
echo "DIRCOUNT t1 $(ls t1_gt/gt | wc -l) arkit $(ls arkit_gt/gt | wc -l)"
: > /tmp/c24_gtav.txt
while read f; do if [ -f "$f" ]; then echo "$f" >> /tmp/c24_gtav.txt; else echo "MISSING $f"; fi; done < /tmp/c24_gt60.txt
for id in 41126645 41159771 41159772 41254810 42446097 42899829 47331002 scene0261_02 scene0320_01 scene0380_01 scene0515_00 scene0515_01 scene0642_01 scene0666_01 246fe09e98 37c9538a2b 38fcf02d0b 3ce6d36ab5 ca3b651c23 d6bb698875 e35232b92f e667e09fe6; do ls t1_gt/gt arkit_gt/gt 2>/dev/null | grep -F "$id" | sed "s/^/ALT $id /"; done
echo "AVAIL $(wc -l < /tmp/c24_gtav.txt) BYTES $(cat /tmp/c24_gtav.txt | xargs stat -c %s | paste -sd+ | bc)"
tar -cf - -T /tmp/c24_gtav.txt | timeout 600 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'mkdir -p /scratch/jjyeung/orch_n30/cont_ops24_c/gt && cd /scratch/jjyeung/orch_n30/cont_ops24_c/gt && tar -xf - && find . -name "*.npz" | sort | xargs sha256sum > ../gt_sha_228.txt; wc -l ../gt_sha_228.txt; df -h /scratch | tail -1'
echo "TAR_RC ${PIPESTATUS[*]}"
sha256sum $(cat /tmp/c24_gtav.txt) | sed 's#  #  ./#' | sort -k2 > /tmp/c24_gt_sha_118.txt; md5sum /tmp/c24_gt_sha_118.txt; cat /tmp/c24_gt_sha_118.txt | head -3
