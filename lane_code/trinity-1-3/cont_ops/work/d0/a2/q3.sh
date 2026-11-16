export TZ=UTC
F=/project/community/jjyeung/okh7/e31b18bf254e12ef
echo "UTC $(date -u +%FT%TZ)"
sha256sum $F/r.sqlite $F/r.json
echo "==RJSON=="; cat $F/r.json
