export TZ=UTC; date -u +%FT%TZ
squeue -h -j 172660 -o 'BEFORE %i %j %T %M %N'
scancel 172660; echo "scancel rc=$?"
sleep 20
squeue -h -j 172660 -o 'AFTER %i %j %T %M %N'
sacct -n -j 172660 -X -o JobID,JobName,State,ExitCode,Elapsed,End
