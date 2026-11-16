cd /project/community/jjyeung/okh7/x_f5c353f7/o 2>/dev/null || { echo NO_DIR; exit 0; }
TZ=UTC ls -la --time-style=+%FT%TZ . | grep -E 'gcs_359fcc3c_m[0-9]+\.done' ; for f in gcs_359fcc3c_m*.done; do [ -f "$f" ] && echo "== $f" && cat "$f"; done; true
