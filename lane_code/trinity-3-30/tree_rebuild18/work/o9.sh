export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; test -e jd3.sh && { echo "jd3 EXISTS"; exit 1; }
awk '{ if ($0=="exit \"$rc\"") { print "for f in $(find \"$N\" -maxdepth 7 \\( -name materialization.json -o -name receipt.json -o -name r.json \\) -size -20M 2>/dev/null); do g=$(echo \"${f#$N/}\" | tr / _); cp \"$f\" \"$O/k_$g\" 2>/dev/null || true; done"; } print }' jd2.sh > jd3.sh; chmod 700 jd3.sh
diff jd2.sh jd3.sh; sha256sum jd2.sh jd3.sh; bash -n jd3.sh && echo SYNTAX_OK; ls -l jd3.sh
