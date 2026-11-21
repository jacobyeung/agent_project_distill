export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
[ "$(sha256sum $X/n_s/sess_173966.json | cut -c1-16)" = 01aec44e04ca02e1 ] && scontrol release 173966; sleep 10; squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
