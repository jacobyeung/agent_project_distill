set -u
K=/scratch/jjyeung/geo_bakeoff_kit
echo "== nproc/load"; nproc; uptime; free -g | head -2
echo "== kit sizes"; du -sh $K/assets/* $K/runtime $K/work $K/data $K/out 2>/dev/null
echo "== geo_bakeoff"; ls $K/work/geo_bakeoff $K/work/geo_bakeoff/* | head -80; ls $K/work/tests | head; ls $K/data/fixture | head
echo "== PAYLOAD"; cat $K/PAYLOAD.json
echo "== CANDIDATES"; cat $K/out/CANDIDATES.md | head -120
echo "== RUNCARD"; head -80 $K/out/RUNCARD.md
echo "== launch"; cat $K/launch/moge2_native.sh $K/launch/mapanything_native.sh $K/work/launch.sh $K/work/kit_env.sh
echo "== k1 capture"; d=$(ls -d /scratch/jjyeung/k1/run_tower_sam_2/*/ | head -1); ls -la $d; cat $d/PHASE_COMPLETE.json | head -c 2000; echo
echo "== k1 src/tools"; ls /scratch/jjyeung/k1/src /scratch/jjyeung/k1/tools /scratch/jjyeung/k1/partB | head -40; cat /scratch/jjyeung/k1/t4.sh | head -40
echo "== manifest"; M=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json; ls -la $M; python3 -c "
import json;m=json.load(open('$M'));print(m.keys());c=m['captures'][0];print({k:(v if k!='rows' else v[:2]) for k,v in c.items()})"
echo "== envs"; ls /scratch/jjyeung/envs
