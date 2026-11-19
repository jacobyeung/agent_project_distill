K=fixture; HM="$HX"; NX="$HX"; X="$HX"; S="$HX/node"; NR="$TK_RUNS_DIR"; mkdir -p "$S"
tk_stage() { TK_PC_HIT="${TEST_HIT:-0}"; printf 'stage %s\n' "$1" >> "$TRACE"; }
tk_bwrap() { BW=(); }; tk_env() { PILOT_VENV="$HX/runtime"; }; tk_pythonpath() { :; }
tk_step() { printf '%s\n' "$*" >> "$TRACE"; }; tk_persist_small() { :; }; tk_persist_exports() { :; }; sleep() { return 1; }
