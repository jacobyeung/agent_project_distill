calls=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m3/db_loop_fixture/missing.calls
sleeps=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m3/db_loop_fixture/missing.sleeps
python3() { return 99; }
sleep() { echo "$1" >> "$sleeps"; }
tk_db_loop() {
    local node="$1" output="$2" helper="$3" attempt
    for ((attempt=1; attempt<=180; attempt++)); do
        if [[ -f "$output/routing_selection.json" ]]; then
            if python3 -B -I -s "$helper" "$node" "$output"; then return 0; fi
        fi
        if (( attempt < 180 )); then sleep 60; fi
    done
    return 1
}

tk_db_loop /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m3/db_loop_fixture/node /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m3/db_loop_fixture/missing unused
