cd /project/community/jjyeung/okh7 || exit 1
date -u +%TZ
sha256sum x_ee227714/k/pool_selection_eac5f9f0.json x_22c714e1/u/eac5f9f0; stat -c '%n %s %a %y' x_ee227714/k/pool_selection_eac5f9f0.json x_22c714e1/u/eac5f9f0
sha256sum x_ee227714/k/SHA256SUMS.txt; sed -n '85p' x_ee227714/k/SHA256SUMS.txt; grep -n eac5f9f0 x_ee227714/k/SHA256SUMS.txt
ls -la x_22c714e1/ ; ls -la x_22c714e1/o/
ls -la x_22c714e1/o/173555/ ; cat x_22c714e1/o/173555/q1.json; echo; cat x_22c714e1/o/173555/r1.json
