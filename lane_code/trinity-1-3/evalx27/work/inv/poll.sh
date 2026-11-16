export TZ=UTC
squeue -j 169991 -o "%.10i %.28j %.8T %.10M %.20S %R"
sacct -j 169991 -X -o JobID,State,Start,Elapsed -P -n
ls -la /project/community/jjyeung/okh7/x27ret
