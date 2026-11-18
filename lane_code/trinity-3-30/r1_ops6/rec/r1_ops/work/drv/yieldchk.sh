export TZ=UTC
y=$(squeue -u $USER -h -p general -t PENDING -o '%i|%j|%r' | grep 'jjy_' | grep -i 'QOSMaxJobsPerUser')
if [ -n "$y" ]; then echo "YIELD: $y"; scancel 170885 && echo "SCANCELLED 170885 $(date -u +%FT%TZ)"; fi
squeue -u $USER -h -p general -o '%i|%j|%T|%M|%r'
