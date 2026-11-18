O=/project/community/jjyeung/okh7
hostname -s; /usr/bin/python3 --version; date -u
ls -la /home/jjyeung/okit 2>&1 | head -8
ls -la $O | head -40
ls -la $O/x_07ca49df $O/x_07ca49df/k 2>&1 | head -20
sha256sum $O/x_07ca49df/SHA256SUMS.txt $O/x_07ca49df/k/0.json 2>&1
ls -la $O/i_bb09a77d $O/b31a069738d1e2f9 2>&1
ls -ld $O/r/1b235d89 $O/x_7cb63d1e 2>&1
ls -la /project/community/jjyeung/distill/okit/in/e00 2>&1
df -h /project/community | tail -1
TZ=UTC squeue -u jjyeung -o '%.10i %.9P %.20j %.8T %.10M %.12l %R' 2>&1 | head
TZ=UTC squeue -p general -o '%.10i %.9u %.20j %.8T %.10M %.12l %S' 2>&1 | head -12
