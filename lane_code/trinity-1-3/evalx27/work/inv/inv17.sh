set +e
C=/project/community/jjyeung
grep 'o_p1w4m200_vsi: start' $C/official_reads/logs/driver_165610.log | tr ' ' '\n' | grep -A1 -E '^--' | paste - - | head -40
echo "==== hubs"; ls $C/cache/hf/hub $C/open_model_port/hf $C/open_model_port/hf/* $C/orch_qwen_stage/hf_cache 2>&1 | head -40
echo "==== or_drv grep"; grep -n "meta_jsonl\|vsi5130\|5130\|parquet\|test.jsonl\|labels" $C/official_reads/bin/or_drv.py | head -30
