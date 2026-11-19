T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1; cd $T
grep -n -E "^def |metrics_|save_seconds|checkpoint_seconds|7200|stop_step|max_steps|milestone|export_dir|exports|print\(json|'event'|\"event\"|output = |output=|cfg\['output|SIGTERM|SIGUSR|signal\." student_pilot/carrier_c1_run.py </dev/null | awk -F: '$1>1950' | cut -c1-210 | head -100
