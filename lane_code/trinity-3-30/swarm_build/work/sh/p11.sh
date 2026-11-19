R=/scratch/jjyeung/orch_n30; cd $R; date -u +%TZ
ls sb_cachk sb_cachk/out sb_cachk/out/v2 2>&1 | head -40
python3 - <<'PY'
import json,glob
for f in glob.glob('/scratch/jjyeung/orch_n30/sb_cachk/out/v2/STAGING.json')+glob.glob('/scratch/jjyeung/orch_n30/sb_cachk/kit_v2/*STAGING*'):
    d=json.load(open(f)); print(f, list(d)[:10])
    for it in d.get('items',[])[:30]: print(' ', {k:it[k] for k in list(it)[:5]})
PY
grep -n -i -E 'launch_gpu|stage|absolute' sb_cachk/kit_v2/launch_gpu.sh | head -20
ls -la W 2>/dev/null; ls -la tree_rebuild10_w/w21/out/BUILD21H_REPORT.md 2>&1
echo "== 3-3"; timeout 60 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-3-3.ib 'hostname -s; df -h /scratch | tail -1; ps -u jjyeung --no-headers | wc -l; nvidia-smi -i 3 --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader; nvidia-smi -i 3 --query-compute-apps=pid,used_memory --format=csv,noheader; nvidia-smi --query-gpu=index,uuid,pci.bus_id --format=csv,noheader | sed -n 4p; for p in /scratch/jjyeung/b01ec87a6f29b /scratch/jjyeung/envs/sam3_capretry_native_v1 /scratch/jjyeung/k1_frames /scratch/jjyeung/orch_n30; do ls -d $p 2>&1; done; ls /scratch/jjyeung | head -30'
