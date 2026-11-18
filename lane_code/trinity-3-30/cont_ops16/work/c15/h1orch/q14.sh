export TZ=UTC
date -u +%TZ
squeue -u jjyeung -o '%i %j %P %T %R %M %l' | head -30
df -h /project/community 2>/dev/null | tail -1
