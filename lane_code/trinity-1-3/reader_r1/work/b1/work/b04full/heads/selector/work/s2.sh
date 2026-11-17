cd /scratch/jjyeung/orch_n30/k1_ops3
ls kc kc/k1_build/work/kit_k1a/out | head -40; ls -la kc/grd_selector kc/devs1_masks kc/leg_s1_tree 2>&1 | head
sed -n 1,12p kc/k1_build/work/kit_k1a/work/gate.py
echo ==ds; cat work/k1_downstream.sh 2>&1 | head -80
echo ==sam3; ls /scratch/jjyeung/orch_cd/ttower/work/ ; ls -la /scratch/jjyeung/orch_cd/ttower/work/sam3_weights; ls /scratch/jjyeung/orch_cd/ttower/work/sam3src 2>/dev/null | head
for e in planner_local_v1 p1cpu sam3_capretry_native_v1; do echo == $e; /scratch/jjyeung/envs/$e/bin/python -c "import sys;print(sys.version)
for m in ['torch','numpy','scipy','sklearn','safetensors','PIL','cv2']:
  try: mod=__import__(m); print(m, getattr(mod,'__version__','?'))
  except Exception as e: print(m,'MISSING',type(e).__name__)" 2>&1; done
ls /scratch/jjyeung/orch_n30/e3_geom/work/harness | head
