M=/project/community/jjyeung/okh7/h_6ed2c7aa/m400; cd /tmp/n22c && mkdir -p red && cd red
tar tvf $M/s.tar | awk '$3<4000000 && $6 ~ /\.json$/ {print $6}' > names.txt; wc -l < names.txt
tar xf $M/s.tar -T names.txt; cp $M/DONE.json $M/e.json $M/r.json $M/RP.json $M/h.out .; tar xf $M/s.tar MANIFEST.json 2>/dev/null; ls
cd /tmp/n22c && tar cf - -C red . | xz -T4 -6 > red.tar.xz; ls -la red.tar.xz; sha256sum red.tar.xz
