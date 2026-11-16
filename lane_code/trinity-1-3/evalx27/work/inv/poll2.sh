export TZ=UTC
squeue -j 169991,170008 -o "%.10i %.28j %.8T %.20S %R"
scontrol show job 170008 | grep -o "Dependency=[^ ]*\|TimeLimit=[^ ]*\|Partition=[^ ]*"
