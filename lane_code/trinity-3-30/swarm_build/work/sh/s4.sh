V=/scratch/jjyeung/orch_n30/sb_cachk/out/v2; cd $V
for d in track seeds; do echo "$d $(find $d -type f | sort | xargs sha256sum | sha256sum | cut -c1-16) $(find $d -type f | wc -l)"; done; sha256sum LAUNCH_228.log STAGING_FRAMES.txt | cut -c1-16
timeout 200 ssh -n -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'cd /scratch/jjyeung/orch_n30/sb_cachk/out/v2; for d in track seeds; do echo "$d $(find $d -type f | sort | xargs sha256sum | sha256sum | cut -c1-16) $(find $d -type f | wc -l)"; done; sha256sum LAUNCH_228.log STAGING_FRAMES.txt | cut -c1-16'
ls $V/track/S_A0_D64 | wc -l
sed -n 20,60p /scratch/jjyeung/orch_n30/sb_cachk/kit_v2/mc_summary.py; echo ----; sed -n 315,345p /scratch/jjyeung/orch_n30/sb_cachk/kit_v2/mc_summary.py; echo ----; sed -n 125,167p /scratch/jjyeung/orch_n30/sb_cachk/kit_v2/mc_price.py
