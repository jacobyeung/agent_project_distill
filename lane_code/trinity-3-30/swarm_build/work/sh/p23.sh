R=/scratch/jjyeung/orch_n30; cd $R; date -u +%TZ
head -3 sb_ktfix2/out/STAGE_LIST.tsv | cut -c1-300; awk -F'\t' 'NR>1{print NF}' sb_ktfix2/out/STAGE_LIST.tsv | sort | uniq -c; wc -l sb_ktfix2/out/STAGE_LIST.tsv
head -3 sb_cachk/out/v2/STAGING_FRAMES.txt; wc -l sb_cachk/out/v2/STAGING_FRAMES.txt
ls sb_ph2fix/out/ | head; python3 -c "import json;d=json.load(open('$R/sb_ph2fix/out/STAGING_PART2.json'));print(list(d)[:8])" 2>&1 | head -3
grep -n -E 'vnice|/data3' sb_cachk/kit_v2/launch_gpu.sh | head -5; grep -n -E 'vnice|/data3' sb_ktfix2/scripts/run_A.sh sb_ktfix2/scripts/gpu_environment.sh | head -5
timeout 60 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'hostname -s; uptime; df -h /scratch | tail -1; nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | tr "\n" " "; echo; nvidia-smi --query-compute-apps=pid,gpu_uuid --format=csv,noheader | wc -l; ls /scratch; ls -la /data3/shared/scripts/vnice/vnice.sh; ps -u jjyeung --no-headers | wc -l'
