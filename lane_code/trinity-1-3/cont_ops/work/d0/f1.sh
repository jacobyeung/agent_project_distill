cd /project/community/jjyeung/okh7/x_07ca49df || exit 1
ls -la k | awk '{print $5, $9}' >&2
ls -la runs/469ddece/m544 >&2
sha256sum runs/469ddece/m544/artifact.json >&2
tar cf - $(ls k/* | grep -v -E '\.tar$') runs/469ddece/m544/artifact.json runs/469ddece/attempt_169097.json SHA256SUMS.txt job.sh job8.sh
