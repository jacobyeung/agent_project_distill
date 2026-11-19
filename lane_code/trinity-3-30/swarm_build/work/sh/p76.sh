date -u +%TZ; hostname -s; ps -u jjyeung --no-headers | wc -l; df -h /scratch | tail -1
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | sed -n 7p
nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader | grep -c . 
for d in /scratch/jjyeung/envs/sam3_scipy_ovl /scratch/jjyeung/envs /scratch/jjyeung/geo_bakeoff_kit /scratch/jjyeung/k1 /scratch/jjyeung/k1_frames /scratch/jjyeung/b01ec87a6f29b /scratch/jjyeung/devs1_frames /scratch/jjyeung/orch_cd /scratch/jjyeung/orch_n30; do [ -e $d ] && echo "HAS $d $(ls $d | head -8 | tr '\n' ' ')" || echo "NO $d"; done
