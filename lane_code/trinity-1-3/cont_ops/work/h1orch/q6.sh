export TZ=UTC; squeue -u jjyeung -o "%i %j %P %T %M %l %R"; squeue -p general -h -o "%u %T %b" | sort | uniq -c
