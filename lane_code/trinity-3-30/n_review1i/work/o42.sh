X=/project/community/jjyeung/okh7/x_22c714e1; TZ=UTC date +%TZ
cd $X/n < /dev/null && sha256sum SHA256SUMS.txt BUILD.json b/a.py k/a.json k/y.json k/c.json k/h.json k/p.json k/r.json k/n.json < /dev/null; nice -n 10 sha256sum -c --quiet SHA256SUMS.txt < /dev/null; echo "check_rc=$? listed=$(wc -l < SHA256SUMS.txt) files=$(find . -type f < /dev/null | wc -l) pycache=$(find . -name __pycache__ < /dev/null | wc -l)"
find . -type f < /dev/null | sed 's|^\./||' | sort > /tmp/n_rv1i_f; awk '{print $2}' SHA256SUMS.txt | sort > /tmp/n_rv1i_l; echo "unlisted: $(comm -23 /tmp/n_rv1i_f /tmp/n_rv1i_l | tr '\n' ' ') missing: $(comm -13 /tmp/n_rv1i_f /tmp/n_rv1i_l | tr '\n' ' ')"
cd $X; sha256sum jn6.sh < /dev/null; ls -d a24m4z12/n_3f55530c < /dev/null; TZ=UTC date +%TZ
