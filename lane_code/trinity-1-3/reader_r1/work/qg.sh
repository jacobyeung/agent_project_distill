export TZ=UTC; squeue -u $USER -h -o "%i %j %P %T %M %l %b %R" | grep -v "^.* jjy_"
