cd /project/community/jjyeung/okh7/x_22c714e1 || exit 1
date -u +%TZ; ls -la o/ | tail -4; for j in 173555 173556 173557 173558; do [ -d o/$j ] && ls -la o/$j; [ -f j/a15_cot_ap24d9b8e2_$j.log ] && tail -3 j/a15_cot_ap24d9b8e2_$j.log; done
