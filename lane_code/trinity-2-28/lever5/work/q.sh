TZ=UTC squeue -j 174200 -h -o "%T %r %S %P"; TZ=UTC squeue -p general -h -o "%i %u %T %M %l %b" | head; sinfo -p general -h -o "%n %t %G" | head
