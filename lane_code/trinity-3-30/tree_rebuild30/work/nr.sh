set -e; export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; date -u +%TZ
ls -la n_r; sha256sum n_r/review.json | cut -c1-64
test -e o/174444/live/WAITING_REVIEW.json && { echo "ALREADY_WAITING: not moving"; exit 1; }
[ "$(sha256sum n_r/review.json | cut -c1-16)" = 476d17bdba5b5aeb ] || { echo "UNEXPECTED_REVIEW_SHA: not moving"; exit 1; }
mkdir -p -m 700 n_r_old; test ! -e n_r_old/review_174246.json; mv n_r/review.json n_r_old/review_174246.json
echo "MOVED $(date -u +%TZ)"; ls -la n_r n_r_old; sha256sum n_r_old/review_174246.json | cut -c1-64
tail -3 o/174444/j2.log 2>/dev/null | cut -c1-300
