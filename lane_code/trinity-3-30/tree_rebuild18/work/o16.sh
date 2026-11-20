export TZ=UTC; date -u +%TZ; [ "$(squeue -h -j 173627 -o %T)" = PENDING ] && scancel 173627 && echo cancelled; squeue -u $USER -o "%.10i %.10P %.8T %.10M %R"
