export TZ=UTC; date -u +%TZ; scancel 173664; sleep 3; squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
