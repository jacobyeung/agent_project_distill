test "$(hostname -s)" = trinity-1-18 || exit 9
cd /scratch/jjyeung/orch_cd/dose_pool/out || exit 8
cat > /tmp/c25_list34.txt <<'LEOF'
t1_gt/gt/scannet__scene0155_00.npz
t1_gt/gt/scannet__scene0155_01.npz
t1_gt/gt/scannet__scene0155_02.npz
t1_gt/gt/scannet__scene0166_00.npz
t1_gt/gt/scannet__scene0166_02.npz
t1_gt/gt/scannet__scene0250_00.npz
t1_gt/gt/scannet__scene0250_01.npz
t1_gt/gt/scannet__scene0250_02.npz
t1_gt/gt/scannet__scene0380_02.npz
t1_gt/gt/scannet__scene0401_00.npz
t1_gt/gt/scannet__scene0475_00.npz
t1_gt/gt/scannet__scene0475_01.npz
t1_gt/gt/scannet__scene0475_02.npz
t1_gt/gt/scannet__scene0515_02.npz
t1_gt/gt/scannet__scene0534_01.npz
t1_gt/gt/scannet__scene0587_00.npz
t1_gt/gt/scannet__scene0587_01.npz
t1_gt/gt/scannet__scene0587_02.npz
t1_gt/gt/scannetppv2__0c7962bd64.npz
t1_gt/gt/scannetppv2__17c5e6a336.npz
t1_gt/gt/scannetppv2__21c5ee0ca5.npz
t1_gt/gt/scannetppv2__260db9cf5a.npz
t1_gt/gt/scannetppv2__307e3262f1.npz
t1_gt/gt/scannetppv2__5b0a310211.npz
t1_gt/gt/scannetppv2__6a217fbcb0.npz
t1_gt/gt/scannetppv2__7e7cd69a59.npz
t1_gt/gt/scannetppv2__80ffca8a48.npz
t1_gt/gt/scannetppv2__99a2503d63.npz
t1_gt/gt/scannetppv2__aaa11940d3.npz
t1_gt/gt/scannetppv2__aaa9c251de.npz
t1_gt/gt/scannetppv2__ad562ce09b.npz
t1_gt/gt/scannetppv2__b37c033757.npz
t1_gt/gt/scannetppv2__e7ccd75e5d.npz
t1_gt/gt/scannetppv2__eb8ef9b4cc.npz
LEOF
du -cb $(cat /tmp/c25_list34.txt) | tail -1
sha256sum $(cat /tmp/c25_list34.txt) > /tmp/c25_gt34.sha
ls POOL_S1 | head -20; ls POOL_S1 | wc -l
for m in scene0642_01 scene0320_00 scene0320_02 scene0261_02 scene0320_01 scene0380_01 scene0515_00 3ce6d36ab5 623c973c56 ca3b651c23 scene0515_01 scene0687_00 scene0261_03 d6bb698875 e35232b92f scene0666_01 37c9538a2b e667e09fe6; do ls -d POOL_S1/*$m* arkit_gt/gt/*$m* t1_gt/gt/*$m* 2>/dev/null; done | head -40
tar cf - $(cat /tmp/c25_list34.txt) -C /tmp c25_gt34.sha | timeout 600 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'mkdir -p /scratch/jjyeung/orch_n30/cont_ops25_c/cam/gt && cd /scratch/jjyeung/orch_n30/cont_ops25_c/cam/gt && tar xf - && sha256sum -c --quiet c25_gt34.sha && echo GT34_OK && du -sh .'
