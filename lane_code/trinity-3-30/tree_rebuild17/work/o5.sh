export TZ=UTC; date -u +%TZ; squeue -u $USER -h -o "%i %P %j %T %M" | grep 24d9b8e2
for J in 173512 173513; do st=$(squeue -h -j $J -o %T 2>/dev/null); [ "$st" = PENDING ] && scancel $J && echo "cancelled $J"; done; sleep 3; squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
