export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X
df -BG --output=avail /project/community | tail -1; squeue -u $USER -h -o "%i %P %j %T %M"
ls -la $X | head -80
for k in q n n_go; do test -d $k || { echo NO_$k; continue; }; echo "$k seal $(sha256sum $k/SHA256SUMS.txt | cut -c1-16) bad $(cd $k && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$') files $(find $k -type f | wc -l) listed $(wc -l < $k/SHA256SUMS.txt)"; echo "unlisted:"; (cd $k; comm -23 <(find . -type f | sed 's|^\./||' | sort) <(awk '{print $2}' SHA256SUMS.txt | sed 's|^\*||' | sort) | head); done
ls $X/a24m4z12 2>&1 | head; ls -la $X/n_s $X/n_r 2>&1 | head -8 | cut -c1-120
