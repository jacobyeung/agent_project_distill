date -u +%TZ; grep -n -E "sess|gcsput|gs://|storage.googleapis|mirror|upload|exit_trap|trap " /tmp/tr14_j.sh </dev/null | cut -c1-220 | head -30
K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_n_go; ls $K/b; grep -l -E "gcsput|sess" $K/b/* </dev/null
