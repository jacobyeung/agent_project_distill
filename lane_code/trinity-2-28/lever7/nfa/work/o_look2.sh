ls -ld /project/community/jjyeung/c8b836b4ae536 2>&1 | head -1
TZ=UTC squeue -u jjyeung -h -o "%i %P %T" 2>&1 | head
