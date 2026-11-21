export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; date -u +%TZ
df -BG --output=avail /project/community | tail -1; squeue -u $USER -h -o "%i %P %j %T"; squeue -p advanced -h -o "%i %u %T %b" | head -5; sinfo -p advanced -h -o "%n %T %G" | head -5
sha256sum jn6.sh | cut -c1-16; for k in q n; do echo "$k $(sha256sum $k/SHA256SUMS.txt | cut -c1-16) bad $(cd $k && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$')"; done; ls n_s | tail -3; ls -d n_r 2>&1
