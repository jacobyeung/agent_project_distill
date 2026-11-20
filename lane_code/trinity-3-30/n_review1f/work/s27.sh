W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; O=$W/w24v/out
ls -la $O | tail -30; sha256sum $O/TREE_CHANGE_24M4V.patch $O/tree_rebuild_b24m4v_3b4b6cff.tar; cat $O/tree_rebuild_b24m4v_3b4b6cff.tar.sha256 2>/dev/null
wc -l $O/TREE_CHANGE_24M4V.patch; echo "@@@ PATCH"; cat $O/TREE_CHANGE_24M4V.patch
