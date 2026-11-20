D=/project/community/jjyeung/okh7/a15_cot_ap39d650beda00a/985f082abb9ff856; 
TZ=UTC squeue -j 173486 -h -o '%T %M %N %R %S'; TZ=UTC sacct -j 173486 -X -n --format=State,Start,Elapsed
ls -la $D/173486 2>/dev/null; for d in $D/173486/*/; do ls -la $d; done 2>/dev/null | head -20
