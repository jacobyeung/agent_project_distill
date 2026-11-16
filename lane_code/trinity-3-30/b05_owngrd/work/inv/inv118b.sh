cd /scratch/jjyeung
echo ==own; find own_ground_gpu -maxdepth 3 | head -60; du -sh own_ground_gpu
echo ==k1src; ls k1/src k1/m544_parts k1/g3t k1/tools | head -60; du -sh k1/m544_parts k1/src
echo ==pre; python3 -c "
import json;d=json.load(open('k1/run_tower_sam_2.preflight.json'));print(json.dumps(d)[:3000])"
echo ==sam; ls -la orch_cd/mdg_next/work/data/sam3src | head; ls orch_cd 2>/dev/null | head -50
