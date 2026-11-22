X=/project/community/jjyeung/okh7/x_22c714e1; TZ=UTC date +%TZ
cd $X/n < /dev/null && sha256sum SHA256SUMS.txt BUILD.json b/dp.py b/il.py b/pc.py b/a.py b/pf.py k/7.json k/a.json k/c.json k/c0.json k/h.json k/j.json k/n.json k/p.json k/r.json k/y.json k/t_db42866fd9e8d009.tar < /dev/null; nice -n 10 sha256sum -c --quiet SHA256SUMS.txt < /dev/null && echo ALL_MEMBERS_OK
find . -type f < /dev/null | sed 's|^\./||' | sort > /tmp/n_rv1n_f; awk '{print $2}' SHA256SUMS.txt | sort > /tmp/n_rv1n_l; echo "unlisted: $(comm -23 /tmp/n_rv1n_f /tmp/n_rv1n_l | tr '\n' ' ') missing: $(comm -13 /tmp/n_rv1n_f /tmp/n_rv1n_l | tr '\n' ' ')"
ls k/ | grep '^t_' | tr '\n' ' '; echo
cd $X; sha256sum jn8.sh u/c672ad47b28d05d81e524baddb6d164f0f41c0b23a8cf0a1f49bfd045e93ec46 u/da19bb3ad9e9227e12bc28161713ae6a1f2a680e559039e290caa2cff0bc6eca < /dev/null; TZ=UTC date +%TZ
echo "n_r: $(ls -A $X/n_r 2>&1 | tr "\n" " ")"
