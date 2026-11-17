export TZ=UTC; sacct -n -X -j 170757 -o JobID,State,ExitCode,Start,End,Elapsed -P
