T=/scratch/jjyeung/orch_n30/n_review/r1f/tcpx
grep -rn "\.register(\|register_for_auto\|CONFIG_MAPPING\|PROCESSOR_MAPPING\|AutoProcessor\|AutoConfig" $T/student_pilot $T/launch_r1 --include=*.py < /dev/null | grep -v "^.*#" | cut -c1-220 | head -30
