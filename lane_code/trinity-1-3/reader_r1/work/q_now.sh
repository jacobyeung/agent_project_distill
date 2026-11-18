export TZ=UTC; date -u +%FT%TZ
squeue -u $USER -h -o "%i %j %P %T %M %R"
sacct -j 171112 -X -n -o JobID,JobName%22,State,Elapsed,End
