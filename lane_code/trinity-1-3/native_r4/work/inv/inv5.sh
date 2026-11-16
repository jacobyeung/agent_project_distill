set +e
export TZ=UTC
df -B1 /project/community/jjyeung/okh7 | tail -1
(lfs quota -u jjyeung /project 2>/dev/null || true) | head -5
squeue -u jjyeung -o '%i %j %P %T %M %l' | head -5
ls /project/community/jjyeung/okh7/nr2tmp/full_b07/native | head
