T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1; cd $T; ls | tr '\n' ' '; echo; wc -l student_pilot/carrier_c1_run.py </dev/null
grep -n -E "^def |metrics|jsonl|save_every|ckpt_every|checkpoint|export|gsutil|gcs|max_steps|stop_step|seconds|output_dir|out_dir|run_dir" student_pilot/carrier_c1_run.py </dev/null | cut -c1-200 | head -90
