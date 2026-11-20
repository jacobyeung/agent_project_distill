W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
ls $W/ext/b12 $W/inputs/rooms 2>&1 | head -30
f=$W/w24c/work/build24m4c/upload/u/27126674a57111585615308cb3e779e169b5693b1c87afafe691ce8e56c2b390; ls -la $f 2>&1
for d in $W/ext/b12 $W/inputs/rooms; do for x in $d/*; do [ -f "$x" ] && echo "$(sha256sum < $x | cut -c1-8) $x"; done; done 2>/dev/null | grep "^27126674"
