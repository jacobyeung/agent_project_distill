K=fixture
HM="$HX"; NX="$HX"; X="$HX"; S="$HX/node"
tk_stage() { :; }
tk_bwrap() { BW=(); }
tk_env() { PILOT_VENV="$HX/runtime"; }
tk_pythonpath() { :; }
tk_step() { :; }
tk_persist_small() { :; }
tk_persist_exports() { :; }
sleep() { return 1; }
