export TZ=UTC
sinfo -p general,advanced -o '%P %l %D %G' 2>&1 | head -5
df -h /project/community | tail -1
squeue -u $USER -p general -o '%i %j %T %S %M %l' 2>&1 | head
which gcloud; ls -ld /project/community/jjyeung/gcloud
