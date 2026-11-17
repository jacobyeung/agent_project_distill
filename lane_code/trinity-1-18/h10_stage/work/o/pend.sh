export TZ=UTC; date -u +%FT%TZ; squeue -j 170694 -h -o '%i %T %M %r %S %N'; squeue -p general -h -o '%T' | sort | uniq -c
