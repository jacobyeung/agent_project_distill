M=/project/community/jjyeung/okh7/h_6ed2c7aa/m400; ls -la $M; mkdir -p /tmp/n22c; cd /tmp/n22c
tar tvf $M/s.tar | sort -k3 -n -r | head -8 | awk '{print $3, $6}' | sed 's#/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap##'
tar cf - -C $M DONE.json e.json r.json RP.json h.json s.tar 2>/dev/null | xz -T4 -6 > /tmp/n22c/m400s.tar.xz; ls -la /tmp/n22c/m400s.tar.xz; sha256sum /tmp/n22c/m400s.tar.xz
