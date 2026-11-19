V=/scratch/jjyeung/orch_n30/sb_cachk/out/v2; cd $V; ls -d track seeds LAUNCH_228.log STAGING_FRAMES.txt 2>&1 | head
timeout 300 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'cd /scratch/jjyeung/orch_n30/sb_cachk/out/v2 && tar cf - track seeds LAUNCH_228.log STAGING_FRAMES.txt' | tar xf - --keep-old-files -C $V; echo "tar rc ${PIPESTATUS[*]}"
(cd $V && find track seeds LAUNCH_228.log STAGING_FRAMES.txt -type f | sort | xargs sha256sum | sha256sum)
timeout 200 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'cd /scratch/jjyeung/orch_n30/sb_cachk/out/v2 && find track seeds LAUNCH_228.log STAGING_FRAMES.txt -type f | sort | xargs sha256sum | sha256sum'
ls $V/track/S_A0_D64 | wc -l
sed -n 20,60p /scratch/jjyeung/orch_n30/sb_cachk/kit_v2/mc_summary.py; sed -n 315,345p /scratch/jjyeung/orch_n30/sb_cachk/kit_v2/mc_summary.py; sed -n 125,167p /scratch/jjyeung/orch_n30/sb_cachk/kit_v2/mc_price.py
