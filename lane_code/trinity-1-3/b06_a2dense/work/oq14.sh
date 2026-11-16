df -h /project/community/jjyeung /tmp 2>&1 | tail -3
lfs quota -h -u jjyeung /project 2>/dev/null | head -5
TZ=UTC sinfo -p advanced -o "%n %c %m %d %G" -h 2>/dev/null | head -3
TZ=UTC sinfo -p general -o "%n %c %m %d %G" -h 2>/dev/null | head -2
