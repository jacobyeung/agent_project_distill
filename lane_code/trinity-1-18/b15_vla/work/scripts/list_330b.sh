cd /scratch/jjyeung
echo "== mp3d_dl"; ls -la orch_cd/mp3d_dl; for d in orch_cd/mp3d_dl/*/; do echo "-- $d"; ls -la $d | head -20; done; du -sh orch_cd/mp3d_dl/* 2>/dev/null
echo "== nav_build/out"; ls -la orch_cd/nav_build/out; head -c 2000 orch_cd/nav_build/out/sources.json; echo
echo "== nav_survey"; find orch_cd/nav_survey -maxdepth 3 | head -40
echo "== env"; ls envs/nav_habitat024; ls envs/nav_habitat024/lib/python3*/site-packages 2>/dev/null | grep -i -E "habitat|magnum|fastdtw|torch|numpy|transformers|quaternion|gzip|networkx" ; envs/nav_habitat024/bin/python -c "import habitat_sim,sys;print(habitat_sim.__version__, sys.version)" 2>&1 | tail -2; du -sh envs/nav_habitat024
ls -d /scratch/jjyeung/*r2r* /scratch/jjyeung/*R2R* /scratch/jjyeung/*vlnce* /scratch/jjyeung/*habitat* 2>/dev/null
ls mp3d_e0_models | head
