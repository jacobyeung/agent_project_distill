K=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a
cd $K; ls work native_kit | head -60
grep -n "load_model\|read_runtime\|artifact\|trainer\|selected_trainer\|tree_root\|def own\|'own'" work/k1_phases.py native_kit/boundaries.py work/k1_pipeline.py 2>/dev/null | cut -c1-220 | head -60
